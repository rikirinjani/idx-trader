from trader import PaperTrader
from screener_client import get_screened_tickers, get_ticker_price
from datetime import datetime, timezone
import pandas as pd

POSITION_PCT = 0.10
MAX_HOLDINGS = 10
STOP_LOSS_PCT = -15
TAKE_PROFIT_PCT = 20

def _current_prices(screened):
    return {t: d["price"] for t, d in screened.items() if d.get("price")}

def _exit_signals(h, info):
    if h["pnl_pct"] <= STOP_LOSS_PCT:
        return "stop_loss"
    if info:
        pe = info.get("pe_ratio")
        gn = info.get("graham_number")
        if pe and pe > 30:
            return "pe_too_high"
        if gn is not None and pd.notna(gn) and h["current_price"] > gn:
            return "above_graham"
    return None

def run_eod_strategy():
    trader = PaperTrader("EOD")
    screened = get_screened_tickers({"max_pe": 30, "max_pb": 5, "min_score": 60})
    prices = _current_prices(screened)

    holdings_info = trader.get_holdings_with_pnl(prices)
    for h in holdings_info:
        reason = _exit_signals(h, screened.get(h["ticker"]))
        if reason:
            trader.sell(h["ticker"], h["current_price"], reason=reason)

    existing_tickers = {h["ticker"] for h in holdings_info}
    candidates = [
        (t, d) for t, d in screened.items()
        if t not in existing_tickers
        and d.get("graham_number") is not None and pd.notna(d.get("graham_number"))
        and d.get("price") and d["price"] < d["graham_number"] * 0.8
        and d.get("value_score", 0) >= 60
    ]
    candidates.sort(key=lambda x: x[1]["value_score"], reverse=True)

    holdings_info = trader.get_holdings_with_pnl(prices)
    slots = MAX_HOLDINGS - len(holdings_info)
    for ticker, info in candidates[:slots]:
        price = info["price"]
        position_size = trader.cash * POSITION_PCT
        shares = max(1, int(position_size / price))
        trader.buy(ticker, price, shares, reason="eod_signal")

    trader.log_current_value(prices)
    print(f"[EOD] Cash: {trader.cash:,.0f}, Holdings: {len(trader.holdings)}")

def run_real_time_strategy():
    trader = PaperTrader("REAL_TIME")
    screener_result = get_screened_tickers({"max_pe": 30, "max_pb": 5, "min_score": 60})
    prices = _current_prices(screener_result)
    from db import get_recent_prices

    holdings_info = trader.get_holdings_with_pnl(prices)
    for h in holdings_info:
        reason = _exit_signals(h, screener_result.get(h["ticker"]))
        if not reason and h["pnl_pct"] >= TAKE_PROFIT_PCT:
            reason = "take_profit"
        if reason:
            trader.sell(h["ticker"], h["current_price"], reason=reason)

    existing_tickers = {h["ticker"] for h in holdings_info}
    holdings_info = trader.get_holdings_with_pnl(prices)
    slots = MAX_HOLDINGS - len(holdings_info)
    entries = 0

    for ticker, info in sorted(screener_result.items(), key=lambda x: x[1].get("value_score", 0), reverse=True):
        if ticker in existing_tickers or entries >= slots:
            continue
        recent = get_recent_prices(ticker, 5)
        if len(recent) < 3:
            continue
        avg_price = sum(r["price"] for r in recent) / len(recent)
        current = prices.get(ticker)
        if not current:
            continue
        drop_pct = (avg_price - current) / avg_price * 100
        if drop_pct >= 5:
            position_size = trader.cash * POSITION_PCT
            shares = max(1, int(position_size / current))
            trader.buy(ticker, current, shares, reason=f"rt_drop_{drop_pct:.0f}pct")
            entries += 1

    trader.log_current_value(prices)
    print(f"[REAL_TIME] Cash: {trader.cash:,.0f}, Holdings: {len(trader.holdings)}")

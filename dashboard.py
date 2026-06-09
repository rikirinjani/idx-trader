import streamlit as st
import pandas as pd
import plotly.express as px
from db import init_db, get_portfolio, get_trades, get_performance
from trader import PaperTrader
from screener_client import get_ticker_price

st.set_page_config(page_title="IDX Paper Trading Bot", layout="wide")
st.title("IDX Paper Trading Bot")

init_db()

t1, t2, t3, t4, t5 = st.tabs(["Portfolios", "Holdings", "Trade History", "Performance", "Comparison"])

def fetch_current_prices(holdings_dict):
    prices = {}
    for ticker in holdings_dict:
        px = get_ticker_price(ticker)
        if px:
            prices[ticker] = px
    return prices

with t1:
    cols = st.columns(2)
    for i, name in enumerate(["EOD", "REAL_TIME"]):
        trader = PaperTrader(name)
        p, _ = get_portfolio(name)
        prices = {}
        if trader.holdings:
            prices = fetch_current_prices(trader.holdings)
        val = trader.portfolio_value(prices)
        ret = (val - p["initial_capital"]) / p["initial_capital"] * 100
        with cols[i]:
            st.subheader(f"Portfolio: {name}")
            st.metric("Total Value", f"Rp{val:,.0f}", f"{ret:+.1f}%")
            st.metric("Cash", f"Rp{trader.cash:,.0f}")
            st.metric("Holdings", len(trader.holdings))

with t2:
    for name in ["EOD", "REAL_TIME"]:
        st.subheader(f"Holdings — {name}")
        trader = PaperTrader(name)
        if not trader.holdings:
            st.caption("No holdings")
            continue
        prices = fetch_current_prices(trader.holdings)
        rows = trader.get_holdings_with_pnl(prices)
        df = pd.DataFrame(rows)
        df["pnl_pct_str"] = df["pnl_pct"].apply(lambda x: f"{x:+.1f}%")
        df["pnl_str"] = df["pnl"].apply(lambda x: f"Rp{x:+,.0f}")
        st.dataframe(
            df[["ticker", "shares", "avg_price", "current_price", "pnl_str", "pnl_pct_str"]],
            width='stretch',
        )

with t3:
    for name in ["EOD", "REAL_TIME"]:
        st.subheader(f"Trades — {name}")
        p, _ = get_portfolio(name)
        trades = get_trades(p["id"])
        if trades:
            df = pd.DataFrame(trades)
            st.dataframe(df[["timestamp", "ticker", "side", "price", "shares", "reason"]], width='stretch')
        else:
            st.caption("No trades yet")

with t4:
    for name in ["EOD", "REAL_TIME"]:
        st.subheader(f"Equity Curve — {name}")
        p, _ = get_portfolio(name)
        perf = get_performance(p["id"])
        if perf:
            df = pd.DataFrame(perf)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            fig = px.line(df, x="timestamp", y="total_value", title=f"{name} Portfolio Value")
            fig.add_hline(y=p["initial_capital"], line_dash="dash", line_color="gray")
            st.plotly_chart(fig, use_container_width=True)

with t5:
    results = []
    for name in ["EOD", "REAL_TIME"]:
        p, _ = get_portfolio(name)
        trader = PaperTrader(name)
        prices = {}
        if trader.holdings:
            prices = fetch_current_prices(trader.holdings)
        val = trader.portfolio_value(prices)
        ret = (val - p["initial_capital"]) / p["initial_capital"] * 100
        trades = get_trades(p["id"])
        perf_data = get_performance(p["id"])

        max_val = p["initial_capital"]
        max_dd = 0.0
        for r in perf_data:
            max_val = max(max_val, r["total_value"])
            dd = (max_val - r["total_value"]) / max_val * 100
            max_dd = max(max_dd, dd)

        results.append({
            "Strategy": name,
            "Return": f"{ret:+.1f}%",
            "Total Trades": len(trades),
            "Max Drawdown": f"{max_dd:.1f}%",
        })

    if results:
        st.subheader("Strategy Comparison")
        st.dataframe(pd.DataFrame(results), width='stretch')

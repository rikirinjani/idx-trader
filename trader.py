from db import (
    get_portfolio, upsert_holding, delete_holding, add_trade,
    update_portfolio_cash, get_holdings, log_performance, log_price,
)

FEE_RATE = 0.003
MIN_CASH = 500_000

class PaperTrader:
    def __init__(self, portfolio_name):
        self.portfolio_name = portfolio_name
        self._refresh()

    def _refresh(self):
        p, holdings = get_portfolio(self.portfolio_name)
        self.portfolio_id = p["id"]
        self.cash = p["cash"]
        self.holdings = {h["ticker"]: h for h in holdings}

    @staticmethod
    def _calc_fee(amount):
        return round(amount * FEE_RATE, 2)

    def buy(self, ticker, price, shares, reason=""):
        cost = price * shares
        fee = self._calc_fee(cost)
        total_cost = cost + fee
        if total_cost > self.cash - MIN_CASH:
            max_shares = int((self.cash - MIN_CASH - fee) / price)
            if max_shares <= 0:
                return None
            shares = max_shares
            cost = price * shares
            fee = self._calc_fee(cost)
            total_cost = cost + fee

        existing = self.holdings.get(ticker)
        if existing:
            total_shares = existing["shares"] + shares
            total_cost_basis = existing["avg_price"] * existing["shares"] + cost
            new_avg = round(total_cost_basis / total_shares, 2)
            upsert_holding(self.portfolio_id, ticker, total_shares, new_avg)
        else:
            upsert_holding(self.portfolio_id, ticker, shares, price)

        update_portfolio_cash(self.portfolio_id, round(self.cash - total_cost, 2))
        add_trade(self.portfolio_id, ticker, "BUY", price, shares, fee, reason)
        self._refresh()
        return shares

    def sell(self, ticker, price, shares=None, reason=""):
        existing = self.holdings.get(ticker)
        if not existing:
            return None
        if shares is None:
            shares = existing["shares"]
        shares = min(shares, existing["shares"])

        proceeds = price * shares
        fee = self._calc_fee(proceeds)
        net_proceeds = proceeds - fee

        remaining = existing["shares"] - shares
        if remaining <= 0:
            delete_holding(self.portfolio_id, ticker)
        else:
            upsert_holding(self.portfolio_id, ticker, remaining, existing["avg_price"])

        update_portfolio_cash(self.portfolio_id, round(self.cash + net_proceeds, 2))
        add_trade(self.portfolio_id, ticker, "SELL", price, shares, fee, reason)
        self._refresh()
        return shares

    def portfolio_value(self, prices=None):
        total = self.cash
        for h in self.holdings.values():
            px = prices.get(h["ticker"]) if prices else h["avg_price"]
            total += px * h["shares"]
        return round(total, 2)

    def log_current_value(self, prices):
        val = self.portfolio_value(prices)
        log_performance(self.portfolio_id, val, self.cash)
        for ticker, price in prices.items():
            log_price(ticker, price)
        return val

    def get_holdings_with_pnl(self, prices):
        result = []
        for h in self.holdings.values():
            px = prices.get(h["ticker"], h["avg_price"])
            pnl = round((px - h["avg_price"]) * h["shares"], 2)
            pnl_pct = round((px - h["avg_price"]) / h["avg_price"] * 100, 1)
            result.append({**h, "current_price": px, "pnl": pnl, "pnl_pct": pnl_pct})
        return result

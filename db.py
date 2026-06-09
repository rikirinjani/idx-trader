import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "trading.db")

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    with _conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                cash REAL NOT NULL DEFAULT 100000000,
                initial_capital REAL NOT NULL DEFAULT 100000000,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                shares INTEGER NOT NULL DEFAULT 0,
                avg_price REAL NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL,
                UNIQUE(portfolio_id, ticker),
                FOREIGN KEY(portfolio_id) REFERENCES portfolios(id)
            );
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                side TEXT NOT NULL CHECK(side IN ('BUY','SELL')),
                price REAL NOT NULL,
                shares INTEGER NOT NULL,
                fee REAL NOT NULL DEFAULT 0,
                timestamp TEXT NOT NULL,
                reason TEXT,
                FOREIGN KEY(portfolio_id) REFERENCES portfolios(id)
            );
            CREATE TABLE IF NOT EXISTS price_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                price REAL NOT NULL,
                timestamp TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS perf_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                total_value REAL NOT NULL,
                cash REAL NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY(portfolio_id) REFERENCES portfolios(id)
            );
        """)
        for name in ("EOD", "REAL_TIME"):
            exists = conn.execute("SELECT id FROM portfolios WHERE name=?", (name,)).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO portfolios (name, cash, initial_capital, created_at) VALUES (?, 100000000, 100000000, ?)",
                    (name, datetime.now(timezone.utc).isoformat()),
                )

def get_portfolio(name):
    with _conn() as conn:
        p = conn.execute("SELECT * FROM portfolios WHERE name=?", (name,)).fetchone()
        if not p:
            return None, []
        holdings = conn.execute(
            "SELECT * FROM holdings WHERE portfolio_id=?", (p["id"],)
        ).fetchall()
        return dict(p), [dict(h) for h in holdings]

def get_holdings(portfolio_id):
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM holdings WHERE portfolio_id=?", (portfolio_id,)).fetchall()
        return [dict(r) for r in rows]

def upsert_holding(portfolio_id, ticker, shares, avg_price):
    with _conn() as conn:
        conn.execute(
            """INSERT INTO holdings (portfolio_id, ticker, shares, avg_price, updated_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(portfolio_id, ticker) DO UPDATE SET
               shares=excluded.shares, avg_price=excluded.avg_price, updated_at=excluded.updated_at""",
            (portfolio_id, ticker, shares, avg_price, datetime.now(timezone.utc).isoformat()),
        )

def delete_holding(portfolio_id, ticker):
    with _conn() as conn:
        conn.execute("DELETE FROM holdings WHERE portfolio_id=? AND ticker=?", (portfolio_id, ticker))

def add_trade(portfolio_id, ticker, side, price, shares, fee, reason):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO trades (portfolio_id, ticker, side, price, shares, fee, timestamp, reason) VALUES (?,?,?,?,?,?,?,?)",
            (portfolio_id, ticker, side, price, shares, fee, datetime.now(timezone.utc).isoformat(), reason),
        )

def update_portfolio_cash(portfolio_id, cash):
    with _conn() as conn:
        conn.execute("UPDATE portfolios SET cash=? WHERE id=?", (cash, portfolio_id))

def get_trades(portfolio_id, limit=100):
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM trades WHERE portfolio_id=? ORDER BY timestamp DESC LIMIT ?",
            (portfolio_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

def log_performance(portfolio_id, total_value, cash):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO perf_log (portfolio_id, total_value, cash, timestamp) VALUES (?,?,?,?)",
            (portfolio_id, total_value, cash, datetime.now(timezone.utc).isoformat()),
        )

def get_performance(portfolio_id, limit=500):
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM perf_log WHERE portfolio_id=? ORDER BY timestamp ASC LIMIT ?",
            (portfolio_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

def log_price(ticker, price):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO price_log (ticker, price, timestamp) VALUES (?,?,?)",
            (ticker, price, datetime.now(timezone.utc).isoformat()),
        )

def get_recent_prices(ticker, days=5):
    with _conn() as conn:
        rows = conn.execute(
            """SELECT price, timestamp FROM price_log
               WHERE ticker=? ORDER BY timestamp DESC LIMIT ?""",
            (ticker, days),
        ).fetchall()
        return [dict(r) for r in rows]

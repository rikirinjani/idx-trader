from data_fetcher import fetch_all_tickers, fetch_single
from screener import screen

def get_screen_results(filters=None):
    if filters is None:
        filters = {"max_pe": 30, "max_pb": 5}
    df = fetch_all_tickers(tickers=None, max_workers=10)
    result = screen(df, filters)
    return result

def get_ticker_price(ticker):
    data = fetch_single(ticker)
    if data:
        return data.get("price")
    return None

def get_screened_tickers(filters=None):
    result = get_screen_results(filters)
    if result.empty:
        return {}
    out = {}
    for _, row in result.iterrows():
        out[row["ticker"]] = {
            "price": row.get("price"),
            "pe_ratio": row.get("pe_ratio"),
            "pb_ratio": row.get("pb_ratio"),
            "value_score": row.get("value_score"),
            "graham_number": row.get("graham_number"),
            "graham_discount_pct": row.get("graham_discount_pct"),
            "sector": row.get("sector"),
        }
    return out

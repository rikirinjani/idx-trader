import yfinance as yf
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import read_cache, write_cache

IDX_TICKERS = [
    "AALI", "ABBA", "ACES", "ADHI", "ADRO", "AGII", "AGRO", "AKRA", "AMMN", "ANTM",
    "APLN", "ARTO", "ASII", "ASRI", "ASSA", "AUTO", "BABP", "BBCA", "BBNI",
    "BBRI", "BBTN", "BDMN", "BFIN", "BGTG", "BISI",
    "BJBR", "BJTM", "BMRI", "BNGA", "BNII", "BRPT", "BSDE", "BSSR", "BUDI", "BUMI",
    "BYAN", "CANI", "CLEO", "CMRY", "CNMA", "CPIN", "CPRO", "CSAP",
    "CTRA", "DGIK", "DILD", "DLTA", "DMAS", "DSNG",
    "ELSA", "EMTK", "ENRG", "EPMT", "ERAA",
    "ESSA", "EXCL", "FAST", "FILM", "FISH", "FREN",
    "GEMS", "GGRM", "GOOD", "GOTO",
    "HEXA", "HMSP", "HRUM",
    "ICBP", "ICON", "INCO", "INDF", "INDY", "INPP", "INTP",
    "ISAT", "ITMG",
    "JBSS", "JPFA", "JSMR",
    "KAEF", "KBLI", "KIAS", "KLBF", "KRAS",
    "LPCK", "LPKR", "LPPF", "LSIP", "LTLS",
    "MAPA", "MASA", "MDLN", "MEDC", "MEGA", "MIKA",
    "MLPL", "MNCN", "MPPA", "MYOR",
    "NIKL", "NISP",
    "PALM", "PANR", "PANS", "PGUN", "PNBN", "PNLF", "PNSE",
    "POLL", "POWR", "PTBA", "PTPP", "PTRO", "PWON",
    "RANC", "RMKE", "RODA", "ROTI",
    "SAMF", "SCMA", "SIDO", "SILO", "SIMP", "SMAR", "SMDR", "SMGR", "SMRA",
    "SMSM", "SPTO", "SSMS", "SULI",
    "TBIG", "TCID", "TINS", "TKIM", "TLKM", "TMAS", "TOWR", "TPIA",
    "TSPC", "UCID", "ULTJ", "UNTR", "UNVR",
    "VALE", "WEGE", "WIKA", "WINS", "WOOD",
]

def fetch_single(ticker):
    try:
        s = yf.Ticker(f"{ticker}.JK")
        info = s.info or {}
        price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
        if price is None:
            return None
        return {
            "ticker": ticker,
            "name": info.get("longName") or info.get("shortName") or ticker,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "price": price,
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "pb_ratio": info.get("priceToBook"),
            "eps": info.get("trailingEps"),
            "book_value": info.get("bookValue"),
            "ev_to_ebitda": info.get("enterpriseToEbitda"),
            "dividend_yield": info.get("dividendYield"),
            "dividend_rate": info.get("dividendRate"),
            "debt_to_equity": info.get("debtToEquity"),
            "ebitda": info.get("ebitda"),
            "total_debt": info.get("totalDebt"),
            "total_revenue": info.get("totalRevenue"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "return_on_equity": info.get("returnOnEquity"),
            "return_on_assets": info.get("returnOnAssets"),
            "profit_margins": info.get("profitMargins"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "beta": info.get("beta"),
        }
    except Exception:
        return None

def fetch_all_tickers(tickers=None, max_workers=10):
    if tickers is None:
        tickers = IDX_TICKERS
    cached = read_cache("idx_data")
    if cached is not None:
        df = pd.DataFrame(cached)
        return df
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(fetch_single, t): t for t in tickers}
        for f in as_completed(futures):
            r = f.result()
            if r:
                results.append(r)
    df = pd.DataFrame(results)
    if not df.empty:
        write_cache("idx_data", df.to_dict("records"))
    return df

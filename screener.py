import pandas as pd
import numpy as np

def _safe(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    return val

def _positive_val(val):
    v = _safe(val)
    if v is not None and v > 0:
        return v
    return None

def compute_graham_number(eps, book_value):
    eps = _positive_val(eps)
    bv = _positive_val(book_value)
    if eps is None or bv is None:
        return None
    return np.sqrt(22.5 * eps * bv)

def compute_graham_discount(price, gn):
    if gn is None or price is None or price <= 0:
        return None
    return round((gn - price) / gn * 100, 1)

def compute_value_score(row):
    scores = []
    weights = []

    pe = _safe(row.get("pe_ratio"))
    if pe is not None and pe > 0:
        pe_score = max(0, 100 - (pe / 50) * 100)
        scores.append(pe_score)
        weights.append(0.20)

    pb = _safe(row.get("pb_ratio"))
    if pb is not None and pb > 0:
        pb_score = max(0, 100 - (pb / 10) * 100)
        scores.append(pb_score)
        weights.append(0.15)

    ev_ebitda = _safe(row.get("ev_to_ebitda"))
    if ev_ebitda is not None and ev_ebitda > 0:
        ev_score = max(0, 100 - (ev_ebitda / 30) * 100)
        scores.append(ev_score)
        weights.append(0.15)

    dy = _safe(row.get("dividend_yield"))
    if dy is not None and dy > 0:
        dy_pct = dy * 100
        dy_score = min(100, (dy_pct / 10) * 100)
        scores.append(dy_score)
        weights.append(0.15)

    der = _safe(row.get("debt_to_equity"))
    if der is not None and der >= 0:
        der_score = max(0, 100 - (der / 3) * 100)
        scores.append(der_score)
        weights.append(0.10)

    disc = _safe(row.get("graham_discount_pct"))
    if disc is not None:
        disc_score = min(100, max(0, disc + 50))
        scores.append(disc_score)
        weights.append(0.15)

    if not scores:
        return 0

    weighted = sum(s * w for s, w in zip(scores, weights))
    total_w = sum(weights)
    return round(weighted / total_w, 1) if total_w > 0 else 0

def screen(df, filters=None):
    df = df.copy()
    if filters is None:
        filters = {}

    df["graham_number"] = df.apply(
        lambda r: compute_graham_number(r.get("eps"), r.get("book_value")), axis=1
    )
    df["graham_discount_pct"] = df.apply(
        lambda r: compute_graham_discount(r.get("price"), r.get("graham_number")), axis=1
    )
    df["value_score"] = df.apply(compute_value_score, axis=1)

    mask = pd.Series(True, index=df.index)
    if "min_pe" in filters and filters["min_pe"] is not None:
        mask &= df["pe_ratio"].fillna(999) >= filters["min_pe"]
    if "max_pe" in filters and filters["max_pe"] is not None:
        mask &= df["pe_ratio"].fillna(999) <= filters["max_pe"]
    if "min_pb" in filters and filters["min_pb"] is not None:
        mask &= df["pb_ratio"].fillna(999) >= filters["min_pb"]
    if "max_pb" in filters and filters["max_pb"] is not None:
        mask &= df["pb_ratio"].fillna(999) <= filters["max_pb"]
    if "min_div_yield" in filters and filters["min_div_yield"] is not None:
        mask &= df["dividend_yield"].fillna(0) >= filters["min_div_yield"]
    if "min_market_cap" in filters and filters["min_market_cap"] is not None:
        mask &= df["market_cap"].fillna(0) >= filters["min_market_cap"]
    if "min_score" in filters and filters["min_score"] is not None:
        mask &= df["value_score"].fillna(0) >= filters["min_score"]
    if "max_der" in filters and filters["max_der"] is not None:
        mask &= df["debt_to_equity"].fillna(999) <= filters["max_der"]

    result = df[mask].sort_values("value_score", ascending=False)
    result["rank"] = range(1, len(result) + 1)
    return result

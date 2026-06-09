import json
import os
import time
from pathlib import Path

CACHE_DIR = Path(__file__).parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL = 3600

def read_cache(name):
    path = CACHE_DIR / f"{name}.json"
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    if time.time() - data.get("_ts", 0) > CACHE_TTL:
        return None
    return data.get("data")

def write_cache(name, data):
    path = CACHE_DIR / f"{name}.json"
    with open(path, "w") as f:
        json.dump({"data": data, "_ts": time.time()}, f)

def fmt_rupiah(val):
    if val is None or val != val:
        return "N/A"
    if abs(val) >= 1e12:
        return f"Rp{val/1e12:.2f}T"
    if abs(val) >= 1e9:
        return f"Rp{val/1e9:.2f}B"
    if abs(val) >= 1e6:
        return f"Rp{val/1e6:.2f}M"
    return f"Rp{val:,.0f}"

def fmt_pct(val):
    if val is None or val != val:
        return "N/A"
    return f"{val:.2f}%"

def fmt_ratio(val):
    if val is None or val != val:
        return "N/A"
    return f"{val:.2f}x"

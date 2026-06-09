"""Export trading report to CSV + summary text for GitHub Actions."""
import csv
import os
from datetime import datetime
from db import init_db, get_portfolio, get_trades, get_performance

OUT_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(OUT_DIR, exist_ok=True)

def export():
    init_db()
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    for name in ["EOD", "REAL_TIME"]:
        p, holdings = get_portfolio(name)
        if not p:
            continue

        # Holdings CSV
        with open(os.path.join(OUT_DIR, f"holdings_{name}.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ticker", "shares", "avg_price"])
            for h in holdings:
                w.writerow([h["ticker"], h["shares"], h["avg_price"]])

        # Trades CSV
        trades = get_trades(p["id"], limit=500)
        with open(os.path.join(OUT_DIR, f"trades_{name}.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["timestamp", "ticker", "side", "price", "shares", "fee", "reason"])
            for t in trades:
                w.writerow([t["timestamp"], t["ticker"], t["side"], t["price"], t["shares"], t["fee"], t["reason"]])

        # Performance CSV
        perf = get_performance(p["id"])
        with open(os.path.join(OUT_DIR, f"perf_{name}.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["timestamp", "total_value", "cash"])
            for r in perf:
                w.writerow([r["timestamp"], r["total_value"], r["cash"]])

        perf_val = perf[-1]["total_value"] if perf else p["initial_capital"]
        ret = (perf_val - p["initial_capital"]) / p["initial_capital"] * 100
        print(f"[{name}] Value: Rp{perf_val:,.0f} | Return: {ret:+.2f}% | Holdings: {len(holdings)} | Trades: {len(trades)}")

    # Summary
    lines = []
    lines.append(f"# IDX Trading Bot Report — {ts}\n")
    for name in ["EOD", "REAL_TIME"]:
        p, holdings = get_portfolio(name)
        if not p:
            continue
        perf = get_performance(p["id"])
        perf_val = perf[-1]["total_value"] if perf else p["initial_capital"]
        ret = (perf_val - p["initial_capital"]) / p["initial_capital"] * 100
        trades = get_trades(p["id"])
        lines.append(f"## {name}")
        lines.append(f"- Value: Rp{perf_val:,.0f}")
        lines.append(f"- Return: {ret:+.2f}%")
        lines.append(f"- Cash: Rp{p['cash']:,.0f}")
        lines.append(f"- Holdings: {len(holdings)}")
        lines.append(f"- Total Trades: {len(trades)}")
        lines.append("")

    report = "\n".join(lines)
    with open(os.path.join(OUT_DIR, f"summary_{ts}.md"), "w") as f:
        f.write(report)
    with open(os.path.join(OUT_DIR, "latest.md"), "w") as f:
        f.write(report)
    print(report)

if __name__ == "__main__":
    export()

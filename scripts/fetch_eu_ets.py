"""Fetch EU ETS daily price from Yahoo Finance (CO2.L = SparkChange Physical Carbon EUA ETC).

Updates data/prices.json eu_eur[current_year] in place.
Designed for ANS morning task automation.
"""
import yfinance as yf
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRICES_JSON = ROOT / "data" / "prices.json"
TICKER = "CO2.L"  # SparkChange Physical Carbon EUA ETC (EUR)
PHASE_MAP = {2005: "Phase 1", 2006: "Phase 1", 2007: "Phase 1",
             2008: "Phase 2", 2009: "Phase 2", 2010: "Phase 2", 2011: "Phase 2", 2012: "Phase 2",
             2013: "Phase 3", 2014: "Phase 3", 2015: "Phase 3", 2016: "Phase 3", 2017: "Phase 3",
             2018: "Phase 3", 2019: "Phase 3", 2020: "Phase 3"}


def main():
    year = datetime.now().year
    t = yf.Ticker(TICKER)
    hist = t.history(period="2y")
    if hist.empty:
        print(f"ERROR: no data from {TICKER}")
        return 1

    cur = hist[hist.index.year == year]["Close"]
    if cur.empty:
        print(f"ERROR: no {year} rows in {TICKER} history")
        return 1

    stats = {
        "year": str(year),
        "avg_price": round(float(cur.mean()), 2),
        "max_price": round(float(cur.max()), 2),
        "min_price": round(float(cur.min()), 2),
        "phase": PHASE_MAP.get(year, "Phase 4"),
    }

    data = json.loads(PRICES_JSON.read_text(encoding="utf-8"))
    updated = False
    for i, row in enumerate(data["eu_eur"]):
        if row["year"] == str(year):
            data["eu_eur"][i] = stats
            updated = True
            break
    if not updated:
        data["eu_eur"].append(stats)

    PRICES_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated EU {year}: avg={stats['avg_price']} max={stats['max_price']} min={stats['min_price']} ({len(cur)} trading days via {TICKER})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Fetch EU ETS daily price from Yahoo Finance (CO2.L = SparkChange Physical Carbon EUA ETC).

Updates data/prices.json eu_eur[current_year] in place.
Saves daily OHLCV to data/eu_ets.db eu_ets_daily table.
Designed for ANS morning task automation.
"""
import sqlite3
import yfinance as yf
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRICES_JSON = ROOT / "data" / "prices.json"
EU_DB = ROOT / "data" / "eu_ets.db"
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

    # Save daily prices to eu_ets.db
    con = sqlite3.connect(EU_DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS eu_ets_daily (
            date TEXT PRIMARY KEY,
            open_price REAL,
            high_price REAL,
            low_price REAL,
            close_price REAL,
            volume INTEGER,
            fetched_at TEXT
        )
    """)
    fetched_at = datetime.now().isoformat()
    # NaN close_price (thin/pending session, e.g. Close未確定) はsqlite3書込み時に無音でNULLへ
    # 変換され、INSERT OR IGNOREのためその日付キーが永久欠損として固定されてしまう。
    # 行自体を作らず日付キーを空けておくことで、翌日以降の再取得で自然に埋まるようにする。
    incomplete_dates = [str(idx.date()) for idx, row in hist.iterrows() if row[["Open", "High", "Low", "Close"]].isna().any()]
    rows = [
        (
            str(idx.date()),
            round(float(row["Open"]), 4),
            round(float(row["High"]), 4),
            round(float(row["Low"]), 4),
            round(float(row["Close"]), 4),
            int(row["Volume"]),
            fetched_at,
        )
        for idx, row in hist.iterrows()
        if not row[["Open", "High", "Low", "Close"]].isna().any()
    ]
    if incomplete_dates:
        print(f"[skip] {len(incomplete_dates)} incomplete (NaN OHLC) date(s) not inserted, will retry next run: {incomplete_dates}")
    cur_db = con.cursor()
    cur_db.executemany(
        "INSERT OR IGNORE INTO eu_ets_daily (date,open_price,high_price,low_price,close_price,volume,fetched_at) VALUES (?,?,?,?,?,?,?)",
        rows,
    )
    new_count = cur_db.rowcount
    cur_db.execute("SELECT COUNT(*), MAX(date) FROM eu_ets_daily")
    total, latest = cur_db.fetchone()
    con.commit()
    con.close()
    print(f"EU daily DB: +{new_count} new records | total={total} | latest={latest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

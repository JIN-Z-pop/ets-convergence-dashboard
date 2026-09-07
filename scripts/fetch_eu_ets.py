"""Fetch EU ETS daily price from Yahoo Finance (CO2.L = SparkChange Physical Carbon EUA ETC).

Saves daily OHLCV to data/eu_ets.db eu_ets_daily table (single source of truth).
Computes data/prices.json eu_eur[current_year] stats from that table instead of the live
snapshot, so the published value only changes on a day new rows are actually recorded.
Designed for ANS morning task automation.
"""
import sqlite3
import yfinance as yf
import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRICES_JSON = ROOT / "data" / "prices.json"
EU_DB = ROOT / "data" / "eu_ets.db"
TICKER = "CO2.L"  # SparkChange Physical Carbon EUA ETC (EUR)
PHASE_MAP = {2005: "Phase 1", 2006: "Phase 1", 2007: "Phase 1",
             2008: "Phase 2", 2009: "Phase 2", 2010: "Phase 2", 2011: "Phase 2", 2012: "Phase 2",
             2013: "Phase 3", 2014: "Phase 3", 2015: "Phase 3", 2016: "Phase 3", 2017: "Phase 3",
             2018: "Phase 3", 2019: "Phase 3", 2020: "Phase 3"}


def half_up(value):
    """2-decimal round-half-up (avoids float round()'s banker's-rounding split on .xx5)."""
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def year_stats_from_db(con, year):
    """Return (n, avg, max, min) for a given year from eu_ets_daily. n=0 -> (0, None, None, None)."""
    cur = con.execute(
        "SELECT COUNT(*), AVG(close_price), MAX(close_price), MIN(close_price) "
        "FROM eu_ets_daily WHERE date LIKE ?",
        (f"{year}-%",),
    )
    n, avg, mx, mn = cur.fetchone()
    if n == 0:
        return 0, None, None, None
    return n, avg, mx, mn


def decide_update(year_stats, existing_row, year, phase_map):
    """year_stats: (n, avg, max, min) from year_stats_from_db.
    existing_row: current eu_eur[year] dict, or None if not present yet.
    Returns (action, new_row) with action in {"UNCHANGED", "CHANGED", "NO_ROWS"}.
    NO_ROWS carries new_row=None (nothing to write).
    """
    n, avg, mx, mn = year_stats
    if n == 0:
        return "NO_ROWS", None
    new_row = {
        "year": str(year),
        "avg_price": half_up(avg),
        "max_price": half_up(mx),
        "min_price": half_up(mn),
        "phase": phase_map.get(year, "Phase 4"),
    }
    if existing_row == new_row:
        return "UNCHANGED", new_row
    return "CHANGED", new_row


def main():
    year = datetime.now().year
    t = yf.Ticker(TICKER)
    hist = t.history(period="2y")
    if hist.empty:
        print(f"ERROR: no data from {TICKER}")
        return 1

    cur = hist[hist.index.year == year]["Close"]
    if cur.empty:
        print(f"no {year} rows yet (expected in early January)")
        return 0

    # eu_ets.db is the single source of truth for the published stats below; if it is
    # missing we must not silently create a fresh (incomplete) one and compute from that,
    # so bail out before touching sqlite3.connect at all.
    if not EU_DB.exists():
        print(f"eu_ets.db missing: {EU_DB}")
        return 1

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
    # 2026-08-01鬼検証: 判定列がOHLCの4列だけだったため、Volume単独NaNの行が素通りし
    # int(row["Volume"])でValueErrorになる同型の穴が残っていた。int()変換もINSERT OR IGNORE
    # の不可逆性もVolumeを含む5列に等しく効くので、判定列を書込み列と一致させる。
    REQUIRED_COLS = ["Open", "High", "Low", "Close", "Volume"]
    incomplete_dates = [str(idx.date()) for idx, row in hist.iterrows() if row[REQUIRED_COLS].isna().any()]
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
        if not row[REQUIRED_COLS].isna().any()
    ]
    if incomplete_dates:
        print(f"[skip] {len(incomplete_dates)} incomplete (NaN in {'/'.join(REQUIRED_COLS)}) date(s) "
              f"not inserted, will retry next run: {incomplete_dates}")
    cur_db = con.cursor()
    cur_db.executemany(
        "INSERT OR IGNORE INTO eu_ets_daily (date,open_price,high_price,low_price,close_price,volume,fetched_at) VALUES (?,?,?,?,?,?,?)",
        rows,
    )
    new_count = cur_db.rowcount
    cur_db.execute("SELECT COUNT(*), MAX(date) FROM eu_ets_daily")
    total, latest = cur_db.fetchone()
    con.commit()
    print(f"EU daily DB: +{new_count} new records | total={total} | latest={latest}")

    year_stats = year_stats_from_db(con, year)
    con.close()

    if year_stats[0] == 0:
        print(f"no {year} rows yet (expected in early January)")
        return 0

    data = json.loads(PRICES_JSON.read_text(encoding="utf-8"))
    existing_idx = next((i for i, row in enumerate(data["eu_eur"]) if row["year"] == str(year)), None)
    existing_row = data["eu_eur"][existing_idx] if existing_idx is not None else None

    action, new_row = decide_update(year_stats, existing_row, year, PHASE_MAP)

    if action == "UNCHANGED":
        print(f"UNCHANGED EU {year}: avg={new_row['avg_price']} max={new_row['max_price']} min={new_row['min_price']}")
    else:
        print(f"CHANGED EU {year}: {existing_row} -> {new_row}")
        if existing_idx is not None:
            data["eu_eur"][existing_idx] = new_row
        else:
            data["eu_eur"].append(new_row)
        PRICES_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    n = year_stats[0]
    print(f"Updated EU {year}: avg={new_row['avg_price']} max={new_row['max_price']} min={new_row['min_price']} "
          f"({n} trading days from eu_ets.db; live hist {len(cur)} rows, +{new_count} new)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

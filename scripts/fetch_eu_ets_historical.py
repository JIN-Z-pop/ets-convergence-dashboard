"""Fetch EU ETS historical daily prices from NASDAQ Data Link (CHRIS/ICE_EUA1).

Fills the gap: 2008-01-01 to 2021-10-17 (before CO2.L ETF listing).
Stores results in gods_eye.db raw_eu_ets_daily and outputs CSV.

Usage:
    python fetch_eu_ets_historical.py --api-key YOUR_KEY
    python fetch_eu_ets_historical.py  # reads NASDAQ_DATA_LINK_API_KEY env var
"""
import argparse
import os
import sqlite3
from datetime import datetime, date
from pathlib import Path

DB_PATH = Path.home() / ".claude" / "databases" / "gods_eye.db"
CSV_OUT = Path(__file__).parent.parent / "data" / "eu_ets_daily_historical.csv"

# Gap to fill: CO2.L starts 2021-10-18, so we fetch up to 2021-10-17
FETCH_START = "2008-01-01"
FETCH_END   = "2021-10-17"


def fetch_nasdaq(api_key: str) -> "pd.DataFrame":
    import nasdaqdatalink
    nasdaqdatalink.ApiConfig.api_key = api_key
    df = nasdaqdatalink.get(
        "CHRIS/ICE_EUA1",
        start_date=FETCH_START,
        end_date=FETCH_END,
    )
    return df


def insert_to_db(df) -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    inserted = 0
    skipped = 0
    for dt, row in df.iterrows():
        d = dt.date().isoformat() if hasattr(dt, "date") else str(dt)[:10]
        # Settle = daily settlement price (EUA EUR/t)
        price = float(row.get("Settle", row.get("Close", 0)))
        vol   = int(row.get("Volume", 0)) if not __import__("math").isnan(float(row.get("Volume", 0))) else 0
        try:
            c.execute(
                "INSERT INTO raw_eu_ets_daily (date, price_usd, volume, fetched_at) VALUES (?,?,?,?)",
                (d, price, vol, now),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1
    conn.commit()
    conn.close()
    return inserted, skipped


def save_csv(df):
    out = df[["Settle", "Volume"]].copy()
    out.index.name = "date"
    out.columns = ["price_eur", "volume"]
    out.to_csv(CSV_OUT)
    return CSV_OUT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", default=os.environ.get("NASDAQ_DATA_LINK_API_KEY", ""))
    parser.add_argument("--csv-only", action="store_true", help="save CSV but skip DB insert")
    parser.add_argument("--dry-run", action="store_true", help="fetch and report without saving")
    args = parser.parse_args()

    if not args.api_key:
        print("ERROR: API key required. Pass --api-key or set NASDAQ_DATA_LINK_API_KEY env var.")
        print("  Free registration: https://data.nasdaq.com/sign-up")
        return 1

    print(f"Fetching CHRIS/ICE_EUA1 from {FETCH_START} to {FETCH_END} ...")
    try:
        df = fetch_nasdaq(args.api_key)
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

    if df.empty:
        print("No data returned.")
        return 1

    print(f"Fetched {len(df)} rows: {df.index.min().date()} to {df.index.max().date()}")
    print(f"Columns: {list(df.columns)}")
    print(df[["Settle", "Volume"]].head(3).to_string())
    print("...")
    print(df[["Settle", "Volume"]].tail(3).to_string())

    settle_col = "Settle" if "Settle" in df.columns else df.columns[0]
    price_series = df[settle_col].dropna()
    print(f"\nSettle stats: avg={price_series.mean():.2f} max={price_series.max():.2f} min={price_series.min():.2f} EUR")

    if args.dry_run:
        print("[dry-run] Skipping save.")
        return 0

    csv_path = save_csv(df)
    print(f"\nCSV saved: {csv_path}")

    if not args.csv_only:
        ins, skip = insert_to_db(df)
        print(f"DB insert: {ins} new rows, {skip} skipped (already exist)")
        total = sqlite3.connect(DB_PATH).execute("SELECT COUNT(*) FROM raw_eu_ets_daily").fetchone()[0]
        new_min = sqlite3.connect(DB_PATH).execute("SELECT MIN(date) FROM raw_eu_ets_daily").fetchone()[0]
        new_max = sqlite3.connect(DB_PATH).execute("SELECT MAX(date) FROM raw_eu_ets_daily").fetchone()[0]
        print(f"raw_eu_ets_daily: {total} rows total, {new_min} to {new_max}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

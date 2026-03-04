"""Export data from gods-eye-db (SQLite) to JSON for dashboard pages."""
import sqlite3
import json
import os
from pathlib import Path

DB_PATH = Path.home() / ".claude" / "databases" / "gods_eye.db"
OUT_DIR = Path(__file__).resolve().parent.parent / "data"

def query(conn, sql):
    cur = conn.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

def export_prices(conn):
    """Price trends for Overview page."""
    china = query(conn, """
        SELECT strftime('%Y', date) as year,
               ROUND(AVG(closing_price), 2) as avg_price,
               ROUND(MAX(closing_price), 2) as max_price,
               ROUND(MIN(closing_price), 2) as min_price,
               ROUND(SUM(total_volume), 0) as total_volume
        FROM raw_cea_daily
        GROUP BY strftime('%Y', date) ORDER BY year
    """)
    korea = query(conn, """
        SELECT strftime('%Y', date) as year,
               ROUND(AVG(closing_price), 0) as avg_price,
               MAX(closing_price) as max_price,
               MIN(closing_price) as min_price,
               COUNT(*) as trading_days
        FROM raw_kets_daily_price
        GROUP BY strftime('%Y', date) ORDER BY year
    """)
    # EU reference prices (no DB table — well-known market data)
    eu_ref = [
        {"year": "2013", "avg_price": 4.5}, {"year": "2014", "avg_price": 6.0},
        {"year": "2015", "avg_price": 7.7}, {"year": "2016", "avg_price": 5.3},
        {"year": "2017", "avg_price": 5.8}, {"year": "2018", "avg_price": 15.9},
        {"year": "2019", "avg_price": 24.8}, {"year": "2020", "avg_price": 24.6},
        {"year": "2021", "avg_price": 53.3}, {"year": "2022", "avg_price": 81.2},
        {"year": "2023", "avg_price": 85.0}, {"year": "2024", "avg_price": 65.0},
        {"year": "2025", "avg_price": 68.0}, {"year": "2026", "avg_price": 72.0},
    ]
    return {"china_cny": china, "korea_krw": korea, "eu_eur": eu_ref,
            "fx": {"KRW_USD": 1/1400, "CNY_USD": 1/7.2, "EUR_USD": 1.1}}

def export_systems(conn):
    """System comparison metrics for Compare page."""
    return query(conn, """
        SELECT country, system_name, reference_year, metric_name, metric_value, metric_unit
        FROM ets_system_comparison WHERE reference_year >= 2024
        ORDER BY country, metric_name
    """)

def export_allocation(conn):
    """Allocation evolution for Allocation page."""
    typology = query(conn, "SELECT * FROM ets_allocation_typology ORDER BY country, id")
    eu_phases = query(conn, "SELECT * FROM eu_ets_phases ORDER BY year_start")
    japan = query(conn, "SELECT * FROM japan_gx_ets_timeline ORDER BY event_date")
    return {"typology": typology, "eu_phases": eu_phases, "japan_timeline": japan}

def export_cbam(conn):
    """CBAM timeline for CBAM page."""
    return query(conn, "SELECT * FROM eu_ets_cbam_timeline ORDER BY event_date")

def export_terminology(conn):
    """4-language terminology for Rosetta page."""
    return query(conn, "SELECT * FROM ets_terminology ORDER BY category, term_en")

def main():
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        return
    OUT_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    exports = {
        "prices.json": export_prices,
        "systems.json": export_systems,
        "allocation.json": export_allocation,
        "cbam.json": export_cbam,
        "terminology.json": export_terminology,
    }
    for filename, func in exports.items():
        data = func(conn)
        path = OUT_DIR / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  {filename}: OK")
    conn.close()
    print(f"\nAll data exported to {OUT_DIR}")

if __name__ == "__main__":
    main()

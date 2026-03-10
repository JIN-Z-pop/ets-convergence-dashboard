"""Export ETS data from SQLite database to JSON for dashboard pages."""
import sqlite3
import json
import os
from pathlib import Path

DB_PATH = Path(os.environ.get("ETS_DB_PATH", "ets_data.db"))
OUT_DIR = Path(__file__).resolve().parent.parent / "data"

# Fields to exclude from exported JSON (internal metadata)
STRIP_FIELDS = {"source_id", "created_at"}

def query(conn, sql):
    cur = conn.execute(sql)
    cols = [d[0] for d in cur.description]
    return [{k: v for k, v in zip(cols, row) if k not in STRIP_FIELDS and not k.endswith("_source_id")} for row in cur.fetchall()]

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
    eu = query(conn, """
        SELECT CAST(year AS TEXT) as year,
               avg_price, max_price, min_price, phase
        FROM eu_ets_annual_prices
        ORDER BY year
    """)
    return {"china_cny": china, "korea_krw": korea, "eu_eur": eu,
            "fx": {"KRW_USD": 1/1400, "CNY_USD": 1/7.2, "EUR_USD": 1.1}}

def export_systems(conn):
    """System comparison metrics + visualization data for Compare page."""
    metrics = query(conn, """
        SELECT country, system_name, reference_year, metric_name, metric_value, metric_unit
        FROM ets_system_comparison WHERE reference_year >= 2024
        ORDER BY country, metric_name
    """)
    # Radar chart: normalized 0-100 values for 5 axes
    radar = {
        "EU":    [100, 40, 43, 90, 100],
        "Korea": [9,   68, 10, 80, 52],
        "China": [12.5,60,  0, 50, 24],
        "Japan": [0,   60,  0, 20, 14]
    }
    # Comparison table: 14 metrics × 4 countries
    table = [
        {"EU": "EU-ETS",          "Korea": "K-ETS",          "China": "China-ETS",        "Japan": "GX-ETS"},
        {"EU": "2005",            "Korea": "2015",           "China": "2021",             "Japan": "2023"},
        {"EU": "~€72/t (~$79)",   "Korea": "~₩11,823/t (~$8)","China": "~¥79/t (~$11)",  "Japan": "N/A (GX League)"},
        {"EU": "~40% of GHG",     "Korea": "~68% of GHG",    "China": "~60% (power only)","Japan": "~60%*"},
        {"EU": "~11,000",         "Korea": "~680",           "China": "~3,500",           "Japan": "~747 (GX League)"},
        {"EU": "Absolute",        "Korea": "Absolute",       "China": "Intensity-based",  "Japan": "Voluntary targets"},
        {"EU": "~43%",            "Korea": "~10%",           "China": "0% (100% free)",   "Japan": "0% (2033~ planned)"},
        {"EU": "BM + Auction",    "Korea": "GF + BM + Auction","China": "Intensity BM",   "Japan": "Self-set targets"},
        {"EU": "No (Phase 4)",    "Korea": "Yes (KOC, 10%)", "China": "Yes (CCER, 5%)",   "Japan": "J-Credit"},
        {"EU": "€100/t + next year","Korea": "3x market price","China": "1-5x avg price",  "Japan": "Name & shame (TBD)"},
        {"EU": "Yes",             "Korea": "Yes",            "China": "Yes",              "Japan": "TBD"},
        {"EU": "No",              "Korea": "Limited",        "China": "No",               "Japan": "TBD"},
        {"EU": "EU MRR",          "Korea": "K-MRV",          "China": "CEMS + Calc.",     "Japan": "GHG Protocol"},
        {"EU": "-62% (vs 2005)",  "Korea": "-40% (vs 2018)", "China": "-65% intensity (vs 2005)","Japan": "-46% (vs 2013)"},
    ]
    return {"metrics": metrics, "radar": radar, "table": table}

def export_allocation(conn):
    """Allocation evolution for Allocation page."""
    typology = query(conn, "SELECT * FROM ets_allocation_typology ORDER BY country, id")
    eu_phases = query(conn, "SELECT * FROM eu_ets_phases ORDER BY year_start")
    japan = query(conn, "SELECT * FROM japan_gx_ets_timeline ORDER BY event_date")
    # Gantt chart phases
    gantt = [
        {"country":"EU","phase":"Phase 1","start":2005,"end":2007,"method":"GF","free":95,"auction":5,"color":"#2b6cb0"},
        {"country":"EU","phase":"Phase 2","start":2008,"end":2012,"method":"GF+BM","free":90,"auction":10,"color":"#3182ce"},
        {"country":"EU","phase":"Phase 3","start":2013,"end":2020,"method":"BM+Auction","free":57,"auction":43,"color":"#4299e1"},
        {"country":"EU","phase":"Phase 4","start":2021,"end":2030,"method":"BM+Auction+CBAM","free":40,"auction":60,"color":"#63b3ed"},
        {"country":"EU","phase":"CBAM Full","start":2026,"end":2034,"method":"CBAM phase-out","free":None,"auction":None,"color":"#90cdf4"},
        {"country":"Korea","phase":"Phase 1","start":2015,"end":2017,"method":"GF","free":100,"auction":0,"color":"#276749"},
        {"country":"Korea","phase":"Phase 2","start":2018,"end":2020,"method":"GF+BM","free":97,"auction":3,"color":"#38a169"},
        {"country":"Korea","phase":"Phase 3","start":2021,"end":2025,"method":"GF+BM+Auction","free":90,"auction":10,"color":"#48bb78"},
        {"country":"China","phase":"Power BM","start":2021,"end":2024,"method":"Intensity BM","free":100,"auction":0,"color":"#c05621"},
        {"country":"China","phase":"4-Sector BM","start":2025,"end":2030,"method":"Intensity BM","free":100,"auction":0,"color":"#ed8936"},
        {"country":"Japan","phase":"GX League","start":2023,"end":2025,"method":"Voluntary","free":None,"auction":None,"color":"#c53030"},
        {"country":"Japan","phase":"GX-ETS P2","start":2026,"end":2032,"method":"GF+BM","free":None,"auction":None,"color":"#e53e3e"},
        {"country":"Japan","phase":"GX-ETS P3","start":2033,"end":2040,"method":"Auction intro","free":None,"auction":None,"color":"#fc8181"},
    ]
    # Stacked bar: allocation method mix
    method_mix = [
        {"label":"EU P1\n2005","gf":95,"bm":0,"auction":5},
        {"label":"EU P3\n2013","gf":0,"bm":57,"auction":43},
        {"label":"EU P4\n2021","gf":0,"bm":40,"auction":60},
        {"label":"KR P1\n2015","gf":100,"bm":0,"auction":0},
        {"label":"KR P2\n2018","gf":80,"bm":17,"auction":3},
        {"label":"KR P3\n2021","gf":60,"bm":30,"auction":10},
        {"label":"CN\n2021","gf":0,"bm":100,"auction":0},
        {"label":"JP\n2026","gf":50,"bm":50,"auction":0},
    ]
    return {"typology": typology, "eu_phases": eu_phases, "japan_timeline": japan,
            "gantt": gantt, "method_mix": method_mix}

def export_cbam(conn):
    """CBAM timeline for CBAM page."""
    return query(conn, "SELECT * FROM eu_ets_cbam_timeline ORDER BY event_date")

def export_convergence(_conn):
    """Scatter plot data for Convergence page (static projection data)."""
    return {
        "current": [
            {"country": "EU", "age": 21, "price": 79, "coverage": 1600, "label": "EU 2026"},
            {"country": "Korea", "age": 11, "price": 8, "coverage": 600, "label": "Korea 2026"},
            {"country": "China", "age": 5, "price": 11, "coverage": 5000, "label": "China 2026"},
            {"country": "Japan", "age": 3, "price": 0, "coverage": 400, "label": "Japan 2026"}
        ],
        "predicted_2030": [
            {"country": "EU", "age": 25, "price": 85, "coverage": 2000, "label": "EU 2030"},
            {"country": "Korea", "age": 15, "price": 25, "coverage": 700, "label": "Korea 2030"},
            {"country": "China", "age": 9, "price": 20, "coverage": 6000, "label": "China 2030"},
            {"country": "Japan", "age": 7, "price": 15, "coverage": 500, "label": "Japan 2030"}
        ]
    }

def export_terminology(conn):
    """4-language terminology for Rosetta page."""
    return query(conn, "SELECT * FROM ets_terminology ORDER BY category, term_en")

def main():
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Set ETS_DB_PATH environment variable to your database location.")
        return
    OUT_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    exports = {
        "prices.json": export_prices,
        "systems.json": export_systems,
        "allocation.json": export_allocation,
        "cbam.json": export_cbam,
        "convergence.json": export_convergence,
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

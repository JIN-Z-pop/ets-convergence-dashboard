"""CEA daily trading data collector from carbonmarket.cn

Fetches Table 1 (挂牌/listed) and Table 2 (大宗/block) from carbonmarket.cn,
merges them by date, and inserts into china_ets.db.

Usage: python cea_carbonmarket_collector.py
"""
import re
import sqlite3
import requests
from datetime import datetime
from pathlib import Path

URL = "https://carbonmarket.cn/ets/cets/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}
DB_PATH = Path.home() / "Desktop" / "china-ets-mcp" / "data" / "china_ets.db"


def parse_number(text: str) -> float:
    """Parse Chinese formatted number (with commas)."""
    return float(text.replace(",", "").strip()) if text.strip() else 0.0


def fetch_tables() -> tuple[list[dict], list[dict]]:
    """Fetch and parse both tables from carbonmarket.cn."""
    resp = requests.get(URL, headers=HEADERS, timeout=30)
    resp.encoding = "utf-8"
    html = resp.text

    # Parse tables using regex (avoid BS4 dependency)
    # Find all <table> blocks
    tables = re.findall(r"<table[^>]*>(.*?)</table>", html, re.DOTALL)

    listed_rows = []  # Table 1: 挂牌
    block_rows = []   # Table 2: 大宗

    for idx, table_html in enumerate(tables):
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, re.DOTALL)
        for row in rows:
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
            cells = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
            if not cells or not re.match(r"\d{4}-\d{2}-\d{2}", cells[0]):
                continue

            if idx == 1 and len(cells) >= 9:
                # Table 1 (idx=1): 日期, 开盘, 收盘, 最高, 最低, 涨跌, 成交量, 成交额, 振幅
                listed_rows.append({
                    "date": cells[0],
                    "opening_price": parse_number(cells[1]),
                    "closing_price": parse_number(cells[2]),
                    "high_price": parse_number(cells[3]),
                    "low_price": parse_number(cells[4]),
                    "listed_volume": int(parse_number(cells[6])),
                    "listed_amount": parse_number(cells[7]),
                })
            elif idx == 2 and len(cells) >= 5:
                # Table 2 (idx=2): 日期, 成交量, 成交额, 均价, 折溢价
                block_rows.append({
                    "date": cells[0],
                    "block_volume": int(parse_number(cells[1])),
                    "block_amount": parse_number(cells[2]),
                })

    return listed_rows, block_rows


def merge_and_insert(listed_rows: list[dict], block_rows: list[dict]):
    """Merge listed + block data, calculate totals, insert into DB."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Get existing dates
    existing = {r[0] for r in conn.execute("SELECT date FROM cea_daily").fetchall()}

    # Get last derived cumulative values (列分離 2026-08-22: 積み上げ先を cum_*_derived へ変更。
    # 旧 cumulative_* は出所混成(原典公表値×自前積み上げ)のため非推奨・書き込み停止)
    last = conn.execute(
        "SELECT cum_volume_derived, cum_amount_derived FROM cea_daily ORDER BY date DESC LIMIT 1"
    ).fetchone()
    if last and last[0] is not None:
        cum_vol, cum_amt = last[0], last[1]
    else:
        # 種欠損時は全史SUMでseed(混成値を持ち込まない)
        seed = conn.execute(
            "SELECT COALESCE(SUM(total_volume),0), COALESCE(ROUND(SUM(total_amount),4),0.0) FROM cea_daily"
        ).fetchone()
        cum_vol, cum_amt = seed[0], seed[1]

    # Build block lookup
    block_map = {r["date"]: r for r in block_rows}

    # Process in chronological order (oldest first for cumulative calc)
    new_records = []
    anomalies = []
    for row in sorted(listed_rows, key=lambda x: x["date"]):
        if row["date"] in existing:
            continue

        block = block_map.get(row["date"], {"block_volume": 0, "block_amount": 0.0})
        total_vol = row["listed_volume"] + block["block_volume"]
        total_amt = row["listed_amount"] + block["block_amount"]
        cum_vol += total_vol
        cum_amt += total_amt

        # Integrity guard (oni_ets_t10, 2026-07-21): listed_volume=0 while block_volume>0
        # is the exact shape of a 24-row bug found in a 2026-03 backfill (source unidentified).
        # Never silently accept it -- flag for manual review instead of trusting the source blindly.
        if row["listed_volume"] == 0 and block["block_volume"] > 0:
            msg = (f"{row['date']}: listed_volume=0 but block_volume={block['block_volume']:,} "
                   f"(possible source parse issue, needs manual check)")
            print(f"  [WARNING] {msg}")
            anomalies.append(row["date"])

        record = {
            "date": row["date"],
            "opening_price": row["opening_price"],
            "high_price": row["high_price"],
            "low_price": row["low_price"],
            "closing_price": row["closing_price"],
            "listed_volume": row["listed_volume"],
            "listed_amount": row["listed_amount"],
            "block_volume": block["block_volume"],
            "block_amount": block["block_amount"],
            "total_volume": total_vol,
            "total_amount": total_amt,
            "cum_volume_derived": cum_vol,
            "cum_amount_derived": cum_amt,
        }
        new_records.append(record)

    # Insert
    inserted = 0
    for rec in new_records:
        try:
            conn.execute(
                """INSERT INTO cea_daily
                (date, opening_price, high_price, low_price, closing_price,
                 listed_volume, listed_amount, block_volume, block_amount,
                 total_volume, total_amount, cum_volume_derived, cum_amount_derived)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (rec["date"], rec["opening_price"], rec["high_price"],
                 rec["low_price"], rec["closing_price"],
                 rec["listed_volume"], rec["listed_amount"],
                 rec["block_volume"], rec["block_amount"],
                 rec["total_volume"], rec["total_amount"],
                 rec["cum_volume_derived"], rec["cum_amount_derived"]),
            )
            inserted += 1
            print(f"  + {rec['date']}: 終値{rec['closing_price']:.2f} "
                  f"掛牌{rec['listed_volume']:,}t 大宗{rec['block_volume']:,}t "
                  f"合計{rec['total_volume']:,}t")
        except sqlite3.IntegrityError:
            pass

    conn.commit()

    # Log (status=warning + anomaly dates appended when the integrity guard fired)
    log_message = f"carbonmarket.cn: {inserted} new, {len(listed_rows)} on page"
    status = "success"
    if anomalies:
        log_message += f" | ANOMALY listed=0&block>0 on {anomalies}"
        status = "warning"
    conn.execute(
        "INSERT INTO fetch_log (market, fetched_at, records_added, status, message) VALUES (?,?,?,?,?)",
        ("cea", datetime.now().astimezone().isoformat(timespec="seconds"), inserted, status, log_message),
    )
    conn.commit()
    conn.close()
    return inserted, anomalies


def log_outage(message: str):
    """Record a source outage in fetch_log (audit trail) without crashing."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute(
            "INSERT INTO fetch_log (market, fetched_at, records_added, status, message) VALUES (?,?,?,?,?)",
            ("cea", datetime.now().astimezone().isoformat(timespec="seconds"), 0, "error", message[:300]),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # logging must never be the thing that crashes the collector


def main():
    print(f"=== CEA Data Collector (carbonmarket.cn) ===")
    print(f"DB: {DB_PATH}")
    print(f"Fetching from {URL} ...")

    try:
        listed_rows, block_rows = fetch_tables()
    except requests.exceptions.SSLError as e:
        # Source-side cert problem (e.g. carbonmarket.cn leaf cert expired 2026-06-19).
        # Do NOT disable TLS verification — degrade gracefully and leave an audit trail.
        msg = f"TLS/cert error (source-side): {e.__class__.__name__}"
        print(f"WARNING: {msg}")
        print("  -> CEA source unreachable via verified TLS; skipping this run (no data lost).")
        print("  -> Diagnose: openssl s_client -connect carbonmarket.cn:443 | openssl x509 -noout -dates")
        log_outage(msg)
        return
    except requests.exceptions.RequestException as e:
        msg = f"request failed: {e.__class__.__name__}"
        print(f"WARNING: {msg} -> skipping this run.")
        log_outage(msg)
        return
    print(f"  Table 1 (挂牌): {len(listed_rows)} rows")
    print(f"  Table 2 (大宗): {len(block_rows)} rows")

    if not listed_rows:
        print("WARNING: No data found on page. Site structure may have changed.")
        return

    print(f"\nInserting new records...")
    inserted, anomalies = merge_and_insert(listed_rows, block_rows)

    if inserted == 0:
        print("  No new records (DB is up to date)")
    else:
        print(f"\n  {inserted} new record(s) inserted")
    if anomalies:
        print(f"  [WARNING] {len(anomalies)} record(s) flagged (listed=0&block>0): {anomalies}")

    # Show latest
    conn = sqlite3.connect(str(DB_PATH))
    row = conn.execute("SELECT * FROM cea_daily ORDER BY date DESC LIMIT 1").fetchone()
    total = conn.execute("SELECT COUNT(*) FROM cea_daily").fetchone()[0]
    conn.close()

    if row:
        print(f"\nDB status: {total} records, latest: {row[0]} 終値{row[4]:.2f}")
    print("=== Done ===")


if __name__ == "__main__":
    main()

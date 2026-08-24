"""CCER daily trading data collector.

Data source: https://www.ccer.com.cn/wcm/ccer/data/2502lshq.json
Usage: python ccer_daily_data_collector.py
"""
import re
import json
import time
import sqlite3
import requests
from datetime import datetime
from pathlib import Path

BASE_URL = "https://www.ccer.com.cn/wcm/ccer/html/"
JSON_URL = "https://www.ccer.com.cn/wcm/ccer/data/2502lshq.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://www.ccer.com.cn/wcm/ccer/html/2502lshq/index.html",
}
DB_PATH = Path.home() / "Desktop" / "china-ets-mcp" / "data" / "china_ets.db"
REQUEST_DELAY = 0.3


def extract_trading_data(html_content: str, title: str) -> dict:
    """Extract CCER trading data from report page HTML."""
    data = {
        "date": "",
        # daily_volume/daily_amount/avg_price の既定0は「維持」する:
        #   原典は無取引日に0を明示し、統一正本 build_ets_market_smart.load_ccer が
        #   (avg_price==0 and vol==0) で no_trade を判定している。Noneにすると
        #   その判定が壊れる(2026-08-21 精査で伝播確認)。
        "daily_volume": 0, "daily_amount": 0.0,
        "avg_price": 0.0,
        # 累計2列は None が既定。原典が累计成交量/额 を載せない日に0を代入すると
        #   「累計がゼロ」という偽の事実になる(2026-08-21 精査: 188/357行が0、
        #   うち62行は daily_volume>0 で明確な矛盾)。欠測はNULLで表す。
        "cumulative_volume": None, "cumulative_amount": None,
    }

    date_match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", title)
    if date_match:
        y, m, d = date_match.groups()
        data["date"] = f"{y}-{m.zfill(2)}-{d.zfill(2)}"

    # Strip HTML tags so label/number separators like 成交量</span>224,348吨
    # don't break the \s* separators below (2026-06-08 224kt parse-fail fix)
    html_content = re.sub(r"<[^>]+>", "", html_content)

    patterns = {
        "daily_volume": (r"(?<!累计)成交量\s*([0-9,]+)\s*吨", lambda x: int(x.replace(",", ""))),
        "daily_amount": (r"(?<!累计)成交额\s*([0-9,.]+)\s*元", lambda x: float(x.replace(",", ""))),
        "avg_price": (r"成交均价\s*([0-9,.]+)\s*元/吨", lambda x: float(x.replace(",", ""))),
        "cumulative_volume": (r"累计成交量\s*([0-9,]+)\s*吨", lambda x: int(x.replace(",", ""))),
        "cumulative_amount": (r"累计成交额\s*([0-9,.]+)\s*元", lambda x: float(x.replace(",", ""))),
    }

    matched = set()
    for key, (pattern, converter) in patterns.items():
        match = re.search(pattern, html_content)
        if match:
            data[key] = converter(match.group(1))
            matched.add(key)

    # parse成功フラグ(2026-08-22): daily 3列が1つもマッチしない=ページはあるのに取引データを
    # 読めていない疑い。原典の明示0はregexがマッチして0を返すため、ここに来るのはparse失敗側
    # (match有無で区別可能)。INSERTは落とさない(既定0のまま入る) — 記録して可視化する。
    # 落とすと真の無取引日表現の変化に巻き込まれるため、skipでなくWARN+fetch_log記録を採る。
    data["_daily_parse_failed"] = not ({"daily_volume", "daily_amount", "avg_price"} & matched)

    return data


def log_outage(message: str):
    """Record a source outage in fetch_log (audit trail) without crashing.

    cea_carbonmarket_collector.py の同名関数を移植(§2X-3記録流儀統一:
    原典到達不能=別行status=error)。index取得(旧L84-86裸)がここに落ちていた
    W14残置=クラッシュ時に記録なし、を解消する。
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute(
            "INSERT INTO fetch_log (market, fetched_at, records_added, status, message) VALUES (?,?,?,?,?)",
            ("ccer", datetime.now().astimezone().isoformat(timespec="seconds"), 0, "error", message[:300]),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # logging must never be the thing that crashes the collector


def main():
    print(f"=== CCER Data Collector ===")
    print(f"DB: {DB_PATH}")

    conn = sqlite3.connect(str(DB_PATH))
    existing_dates = {r[0] for r in conn.execute("SELECT date FROM ccer_daily").fetchall()}
    print(f"  Existing: {len(existing_dates)} records")

    # Fetch JSON index (§2X-3: 原典到達不能=別行status=errorで記録してから継続)
    print(f"Fetching index from {JSON_URL} ...")
    try:
        resp = requests.get(JSON_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        records = json.loads(resp.text).get("rows", [])
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        msg = f"index fetch/parse failed: {e.__class__.__name__}: {e}"
        print(f"WARNING: {msg}")
        log_outage(msg)
        conn.close()
        return
    print(f"  Index: {len(records)} entries")

    inserted = 0
    anomalies = []
    fetch_errors = []
    for record in records:
        title = record.get("title", "")
        url = record.get("url", "")

        # Quick date check from title
        date_match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", title)
        if date_match:
            y, m, d = date_match.groups()
            date_str = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
            if date_str in existing_dates:
                continue

        # Fetch detail page
        try:
            full_url = BASE_URL + url
            page_resp = requests.get(full_url, headers={
                "User-Agent": HEADERS["User-Agent"],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }, timeout=30)
            page_resp.encoding = "utf-8"
            data = extract_trading_data(page_resp.text, title)

            # INSERT前にpopするためINSERT値の経路は不変(no_trade判定への伝播なし=検証済み)
            parse_failed = data.pop("_daily_parse_failed", False)
            if parse_failed and data["date"]:
                msg = (f"{data['date']}: daily 3列すべてparse不能"
                       f"(既定0のままINSERT=偽no_trade化の恐れ・原典ページ要目視)")
                print(f"  [WARNING] {msg}")
                anomalies.append(data["date"])

            if data["date"] and data["date"] not in existing_dates:
                try:
                    conn.execute(
                        """INSERT INTO ccer_daily
                        (date, daily_volume, daily_amount, avg_price,
                         cumulative_volume, cumulative_amount)
                        VALUES (?,?,?,?,?,?)""",
                        (data["date"], data["daily_volume"], data["daily_amount"],
                         data["avg_price"], data["cumulative_volume"], data["cumulative_amount"]),
                    )
                    inserted += 1
                    existing_dates.add(data["date"])
                    print(f"  + {data['date']}: {data['daily_volume']:,}t @{data['avg_price']:.2f}")
                except sqlite3.IntegrityError:
                    pass
        except Exception as e:
            print(f"  ! Error fetching {url}: {e}")
            # ネットワーク等の失敗も台帳に痕跡を残す(沈黙のcontinueはstatus=successの偽記録源)。
            # parse失敗(ANOMALY)とは別リスト=messageで原因を区別できるようにする。
            fetch_errors.append(f"{url}: {e.__class__.__name__}")
            continue

        time.sleep(REQUEST_DELAY)

    # status警告化(2026-08-22 cea collector流儀の対称移植): エラー/parse失敗が起きたのに
    # 常に "success" と記録する=記録層の偽事実、を根絶。anomaly時は status="warning"。
    log_message = f"ccer.com.cn: {inserted} new, {len(records)} in index"
    status = "success"
    if anomalies:
        log_message += f" | ANOMALY daily-parse-failed on {anomalies}"
        status = "warning"
    if fetch_errors:
        log_message += f" | FETCH-ERROR {len(fetch_errors)}件: {fetch_errors[:3]}"
        status = "warning"
    conn.execute(
        "INSERT INTO fetch_log (market, fetched_at, records_added, status, message) VALUES (?,?,?,?,?)",
        ("ccer", datetime.now().astimezone().isoformat(timespec="seconds"), inserted, status, log_message),
    )
    conn.commit()

    # Show latest
    row = conn.execute("SELECT * FROM ccer_daily ORDER BY date DESC LIMIT 1").fetchone()
    total = conn.execute("SELECT COUNT(*) FROM ccer_daily").fetchone()[0]
    conn.close()

    if inserted == 0:
        print("  No new records (DB is up to date)")
    else:
        print(f"\n  {inserted} new record(s) inserted")

    if row:
        print(f"\nDB status: {total} records, latest: {row[0]} @{row[3]:.2f}")
    print("=== Done ===")


if __name__ == "__main__":
    main()

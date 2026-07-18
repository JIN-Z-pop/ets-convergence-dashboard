#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sync_eua_to_gods.py — eu_ets.db(ets-convergence-dashboard) → gods_eye.raw_eu_ets_daily 差分同期。

2026-07-18鬼検証是正: raw_eu_ets_daily.price_usd の実体はEUR建て(CO2.L=SparkChange Physical Carbon
EUA ETC)。列名price_usdは歴史的負債であり、本スクリプトはeu_ets_daily.close_price(EUR建て)を
そのままprice_usdへ格納する(通貨変換はしない=同一通貨のミラーリング)。

S1a裁定(奏 2026-07-18夜, 案B採用): raw_eu_ets_daily に2026-04-22 price_usd=NULLのplaceholder行
が既存(fetcher一時停止時の未確定snapshot)。これは「genuine観測値」ではなく未充足欠損のため、
唯一の例外としてUPDATE(date名指し+price_usd IS NULL の両条件ガード)で充足する。
それ以外の全既存行(date<2026-04-22)は不可侵=INSERT OR IGNOREのみで一切UPDATEしない。

安全ガード:
  1. 実行前に price_usd IS NULL 行を全走査 — 2026-04-22の1件のみでなければ即abort(裁定持ち帰り)。
  2. UPDATE文は WHERE date=? AND price_usd IS NULL の複合条件(誤爆構造的に不能)。
  3. date<2026-04-22 の全行についてsync前後でhash比較し不変性を検証。

🔴 本スクリプトの責務はDB層まで。ets_market.json再build・デプロイは別承認(禁止)。

Usage: python scripts/sync_eua_to_gods.py   (ets-convergence-dashboardルートから)
"""
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EU_DB = ROOT / "data" / "eu_ets.db"
GODS_DB = Path(r"C:\Users\jin_z\.claude\databases\gods_eye.db")

STUB_DATE = "2026-04-22"


def row_hash(rows):
    h = hashlib.sha256()
    for r in rows:
        h.update(repr(r).encode("utf-8"))
    return h.hexdigest()


def main():
    gods = sqlite3.connect(str(GODS_DB))
    eu = sqlite3.connect(str(EU_DB))

    # --- Guard 1: pre-scan all NULL price_usd rows — must be exactly [STUB_DATE] ---
    null_rows = gods.execute(
        "SELECT date, price_usd, volume, fetched_at FROM raw_eu_ets_daily WHERE price_usd IS NULL"
    ).fetchall()
    if len(null_rows) != 1 or null_rows[0][0] != STUB_DATE:
        print(f"[ABORT] price_usd IS NULL rows != exactly [{STUB_DATE}]. Found: {null_rows}")
        print("裁定条件(1件のみ)に不一致のため停止。奏へ一覧を報告し追加裁定を仰ぐこと。")
        gods.close(); eu.close()
        return 1
    print(f"[guard1] NULL price_usd pre-scan: OK (only {STUB_DATE})")

    # --- Immutability snapshot BEFORE: all rows with date < STUB_DATE ---
    before_rows = gods.execute(
        "SELECT date, price_usd, volume, fetched_at FROM raw_eu_ets_daily WHERE date < ? ORDER BY date",
        (STUB_DATE,),
    ).fetchall()
    before_hash = row_hash(before_rows)
    before_count = len(before_rows)
    total_before = gods.execute("SELECT COUNT(*) FROM raw_eu_ets_daily").fetchone()[0]
    print(f"[snapshot] date<{STUB_DATE} rows={before_count} hash={before_hash[:16]}...  total_before={total_before}")

    # --- Step A: fill the STUB_DATE placeholder (Option B, guarded UPDATE) ---
    stub_src = eu.execute("SELECT close_price, volume FROM eu_ets_daily WHERE date=?", (STUB_DATE,)).fetchone()
    if stub_src is None:
        print(f"[ABORT] {STUB_DATE} not found in eu_ets.db — cannot fill stub, no source value.")
        gods.close(); eu.close()
        return 1
    new_price, new_volume = round(float(stub_src[0]), 2), int(stub_src[1])
    now = datetime.now().isoformat()

    before_stub = gods.execute(
        "SELECT date, price_usd, volume, fetched_at FROM raw_eu_ets_daily WHERE date=?", (STUB_DATE,)
    ).fetchone()
    print(f"[stub] BEFORE: {before_stub}")

    cur = gods.execute(
        "UPDATE raw_eu_ets_daily SET price_usd=?, volume=?, fetched_at=? WHERE date=? AND price_usd IS NULL",
        (new_price, new_volume, now, STUB_DATE),
    )
    stub_updated = cur.rowcount
    after_stub = gods.execute(
        "SELECT date, price_usd, volume, fetched_at FROM raw_eu_ets_daily WHERE date=?", (STUB_DATE,)
    ).fetchone()
    print(f"[stub] UPDATE rowcount={stub_updated}  AFTER: {after_stub}")
    if stub_updated != 1:
        print(f"[ABORT] stub UPDATE rowcount={stub_updated} (expected 1) — rolling back, nothing committed.")
        gods.rollback()
        gods.close(); eu.close()
        return 1

    # --- Step B: differential INSERT of the rest of eu_ets.db (existing PKs skipped) ---
    # NOTE: still inside the same uncommitted transaction opened by the UPDATE above.
    total_before_insert = gods.execute("SELECT COUNT(*) FROM raw_eu_ets_daily").fetchone()[0]
    src_rows = eu.execute("SELECT date, close_price, volume FROM eu_ets_daily ORDER BY date").fetchall()
    insert_rows = [(d, round(float(c), 2), int(v), now) for d, c, v in src_rows]
    gods.executemany(
        "INSERT OR IGNORE INTO raw_eu_ets_daily (date, price_usd, volume, fetched_at) VALUES (?,?,?,?)",
        insert_rows,
    )

    total_after = gods.execute("SELECT COUNT(*) FROM raw_eu_ets_daily").fetchone()[0]
    actual_inserted = total_after - total_before_insert  # count-diff, not cursor.rowcount (executemany semantics unreliable)
    nonnull_after = gods.execute("SELECT COUNT(*) FROM raw_eu_ets_daily WHERE price_usd IS NOT NULL").fetchone()[0]
    null_after = gods.execute("SELECT COUNT(*) FROM raw_eu_ets_daily WHERE price_usd IS NULL").fetchone()[0]
    maxdate_after = gods.execute("SELECT MAX(date) FROM raw_eu_ets_daily").fetchone()[0]

    # --- Immutability check (still pre-commit: read own uncommitted writes) ---
    after_rows = gods.execute(
        "SELECT date, price_usd, volume, fetched_at FROM raw_eu_ets_daily WHERE date < ? ORDER BY date",
        (STUB_DATE,),
    ).fetchall()
    after_hash = row_hash(after_rows)

    boundary = gods.execute(
        "SELECT date, price_usd FROM raw_eu_ets_daily WHERE date IN ('2026-04-21','2026-04-22','2026-04-23') ORDER BY date"
    ).fetchall()

    print(f"[insert] new_rows_inserted={actual_inserted}  total_before_insert={total_before_insert}  total_after={total_after}")
    print(f"[result] total_rows={total_after}  non_null={nonnull_after}  null_remaining={null_after}  max_date={maxdate_after}")
    print(f"[result] boundary(04-21/22/23)={boundary}")
    print(f"[immutability] rows<{STUB_DATE}: before={before_count} after={len(after_rows)}  hash_match={before_hash == after_hash}")

    if before_hash != after_hash:
        print("[ABORT] immutability hash mismatch — genuine rows would be altered. ROLLING BACK, nothing committed.")
        gods.rollback()
        gods.close(); eu.close()
        return 1

    gods.commit()
    print("[commit] OK — all guards passed, transaction committed.")
    gods.close()
    eu.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

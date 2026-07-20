#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""load_eua_hist_fsr.py — EUA歴史価格(FSR Figure_1.csv)をgods_eye.dbの恒久層テーブルへ投入。

奏(editor) spec 2026-07-20発注 (eua_hist_permanent_load_spec_20260720.md) / 葉山(actor)実装。
経緯: 2026-07-19にEEXオークション998行を直接ets_dailyへ投入したところ翌build時のDELETE→
全再構築で消滅(2026-07-20発覚)。恒久投入へ設計転換した結果が本spec。

設計原則(上記消滅事故の教訓): 恒久データはbuildソース側(gods_eye.db)に置く。
ets_market_smart.db.ets_daily は build_ets_market_smart.py が毎朝DELETE→全再構築する揮発層。

投入元: data/sources/eua_hist/fsr_Figure_1.csv (md5=43af6218d0b671f50f2e77d0f1c1cc9b)
日付書式: 前期 DD.MM.YYYY (〜2023-10-01) / 後期 DD/MM/YYYY (2023-10-02〜) の2書式混在。
投入範囲: 最初の有効価格日 〜 2021-10-17 (現行raw_eu_ets_daily開始2021-10-18の前日まで)。
#N/A行(価格未収録)はスキップ。no_trade=1(無取引日)とは意味が異なるため混同しない。

Usage: python scripts/load_eua_hist_fsr.py  (ets-convergence-dashboardルートから)
"""
import csv
import hashlib
import sqlite3
from datetime import datetime

GODS = r"C:\Users\jin_z\.claude\databases\gods_eye.db"
CSV_PATH = r"C:\Users\jin_z\Desktop\ets-convergence-dashboard\data\sources\eua_hist\fsr_Figure_1.csv"
EXPECTED_MD5 = "43af6218d0b671f50f2e77d0f1c1cc9b"
CUTOFF = datetime(2021, 10, 17)

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS raw_eua_hist_fsr (
    date TEXT PRIMARY KEY,
    price_eur REAL NOT NULL,
    loaded_at TEXT
)
"""


def parse_date(s):
    s = s.strip()
    if "." in s:
        return datetime.strptime(s, "%d.%m.%Y")
    elif "/" in s:
        return datetime.strptime(s, "%d/%m/%Y")
    raise ValueError(f"unrecognized date format: {s!r}")


def verify_md5():
    with open(CSV_PATH, "rb") as f:
        actual = hashlib.md5(f.read()).hexdigest()
    if actual != EXPECTED_MD5:
        raise RuntimeError(f"md5 mismatch: expected {EXPECTED_MD5}, got {actual}. 素材が改変された可能性=投入中断。")
    print(f"[OK] md5 verified: {actual}")


def load_rows():
    rows = []
    na_skipped = 0
    after_cutoff = 0
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        next(reader)  # header
        for r in reader:
            d = parse_date(r[0])
            if d > CUTOFF:
                after_cutoff += 1
                continue
            price = r[3].strip()
            if price == "#N/A" or price == "":
                na_skipped += 1
                continue
            rows.append((d.strftime("%Y-%m-%d"), float(price)))
    return rows, na_skipped, after_cutoff


def main():
    verify_md5()
    rows, na_skipped, after_cutoff = load_rows()
    print(f"target rows(valid,<=2021-10-17)={len(rows)}  na_skipped={na_skipped}  after_cutoff_excluded={after_cutoff}")
    print(f"first={rows[0]}  last={rows[-1]}")

    conn = sqlite3.connect(GODS)
    conn.execute(CREATE_SQL)

    existing = conn.execute("SELECT COUNT(*) FROM raw_eua_hist_fsr").fetchone()[0]
    if existing:
        print(f"[SKIP-CLEAR] raw_eua_hist_fsr already has {existing} rows. Clearing for idempotent reload.")
        conn.execute("DELETE FROM raw_eua_hist_fsr")

    loaded_at = datetime.now().isoformat()
    conn.executemany(
        "INSERT INTO raw_eua_hist_fsr (date, price_eur, loaded_at) VALUES (?, ?, ?)",
        [(d, p, loaded_at) for d, p in rows],
    )
    conn.commit()

    # 期間重複assert(spec B項目): 2021-10-18以降が紛れ込んでいないことを投入後にも確認
    overlap = conn.execute("SELECT COUNT(*) FROM raw_eua_hist_fsr WHERE date >= '2021-10-18'").fetchone()[0]
    if overlap:
        conn.close()
        raise RuntimeError(f"ASSERT FAILED: raw_eua_hist_fsr contains {overlap} rows on/after 2021-10-18 (overlap with raw_eu_ets_daily)")

    total = conn.execute("SELECT COUNT(*), MIN(date), MAX(date) FROM raw_eua_hist_fsr").fetchone()
    print(f"[DONE] raw_eua_hist_fsr: rows={total[0]} range={total[1]}..{total[2]}")
    print("[ASSERT OK] no overlap with 2021-10-18 onward")
    conn.close()


if __name__ == "__main__":
    main()

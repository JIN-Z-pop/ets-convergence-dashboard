#!/usr/bin/env python3
"""sync_smart_market.py — 運用repo DB → スマートDB 市場層 鮮度同期 (approved 2026-07-05)

毎朝の炭素市場サイクルの一部として実行し、GitHub公開用repo DB(運用の体)と
スマートDB(知識の体)の市場層乖離を解消する。

方式: 全量ミラー再構築 (idempotent)
  - repo表の全行を smart表へ DELETE+INSERT (単一トランザクション)
  - 列は smart表のPRAGMAから取得し repo表と突合 (列集合不一致=即FAIL)
  - 同期後 verify: count / max(date) / 数値列SUM の source完全一致を機械検証
  - smart_meta に last_sync / last_sync_source を記録

対象 (市場層のみ。知識層 methodology/parameter等は不可侵):
  china_ets_smart.db : cn_ets_market_cea_daily / cn_ets_market_ccer_daily  <- china_ets.db
  korea_ets_smart.db : kets_market_kau_ohlcv / kets_market_daily_price
                       / kets_market_auction / kets_market_monthly        <- korea_ets.db

Exit code: 0=ALL PASS / 1=FAIL (verify不一致 or 列不一致)
"""
import os
import sqlite3
import sys
from datetime import datetime

from local_paths import require

# ---- 凍結ガード (approved 2026-07-21) ----
# repo側是正(t11)完了までsyncを凍結する。全量ミラーがsmart側の是正成果
# (364行追加+289行是正)をrepo旧値へ巻き戻すのを防ぐ機械ガード。
# 解除条件: t11完了+repo=smart一致検証後にフラグ削除。詳細=フラグファイル本文。
FREEZE_FLAG = require("freeze_flag")
if os.path.exists(FREEZE_FLAG):
    print("[FROZEN] sync_smart_market.py は意図的に凍結中 (t11進行中, 2026-07-21)")
    print("  これはエラーではありません。修復・フラグ削除・再実行は不要です。")
    print(f"  理由と解除条件: {FREEZE_FLAG} を参照。")
    sys.exit(2)
# ---- 凍結ガードここまで ----

REPO_CHINA = require("china_repo_db")
REPO_KOREA = require("korea_repo_db")
SMART_CHINA = require("china_smart_db")
SMART_KOREA = require("korea_smart_db")

# (smart_db, meta_table, [(smart_table, repo_db, repo_table, sum_col)])
SYNC_MAP = [
    (SMART_CHINA, "cn_ets_smart_meta", [
        ("cn_ets_market_cea_daily", REPO_CHINA, "cea_daily", "closing_price"),
        ("cn_ets_market_ccer_daily", REPO_CHINA, "ccer_daily", "avg_price"),
    ]),
    (SMART_KOREA, "kets_smart_meta", [
        ("kets_market_kau_ohlcv", REPO_KOREA, "kets_kau_ohlcv", "close_price"),
        ("kets_market_daily_price", REPO_KOREA, "kets_daily_price", "closing_price"),
        ("kets_market_auction", REPO_KOREA, "kets_auction", None),
        ("kets_market_monthly", REPO_KOREA, "kets_monthly", None),
    ]),
]


def table_cols(con, table):
    return [r[1] for r in con.execute(f"PRAGMA table_info([{table}])")]


def stats(con, table, cols, sum_col):
    cnt = con.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
    mx = con.execute(f"SELECT MAX(date) FROM [{table}]").fetchone()[0] if "date" in cols else None
    sm = None
    if sum_col:
        sm = con.execute(f"SELECT ROUND(SUM([{sum_col}]), 4) FROM [{table}]").fetchone()[0]
    return cnt, mx, sm


def main():
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    failures = []
    for smart_db, meta_table, pairs in SYNC_MAP:
        smart = sqlite3.connect(smart_db)
        for smart_table, repo_db, repo_table, sum_col in pairs:
            repo = sqlite3.connect(f"file:{repo_db}?mode=ro", uri=True)
            s_cols = table_cols(smart, smart_table)
            r_cols = table_cols(repo, repo_table)
            if set(s_cols) != set(r_cols):
                print(f"[FAIL] {smart_table}: column set mismatch smart={s_cols} repo={r_cols}")
                failures.append(smart_table)
                repo.close()
                continue
            col_list = ", ".join(f"[{c}]" for c in s_cols)
            rows = repo.execute(f"SELECT {col_list} FROM [{repo_table}]").fetchall()
            if not rows:
                # repo空ガード (approved 2026-07-05): repo 0行時にsmart全消し+0==0 verify通過を防ぐ
                print(f"[SKIP] {smart_table}: repo {repo_table} is EMPTY — mirror削除を中止 (要調査)")
                failures.append(smart_table)
                repo.close()
                continue
            with smart:  # transaction
                smart.execute(f"DELETE FROM [{smart_table}]")
                smart.executemany(
                    f"INSERT INTO [{smart_table}] ({col_list}) VALUES ({', '.join('?' * len(s_cols))})",
                    rows,
                )
            # verify: source complete match
            sc = stats(smart, smart_table, s_cols, sum_col)
            rc = stats(repo, repo_table, r_cols, sum_col)
            ok = sc == rc
            tag = "PASS" if ok else "FAIL"
            print(f"[{tag}] {smart_table:28} rows={sc[0]:6} max_date={sc[1]} sum({sum_col})={sc[2]}"
                  f"{'' if ok else f'  <> repo {rc}'}")
            if not ok:
                failures.append(smart_table)
            repo.close()
        with smart:
            smart.execute(
                f"INSERT OR REPLACE INTO [{meta_table}] (key, value) VALUES ('last_sync', ?)", (now,))
            smart.execute(
                f"INSERT OR REPLACE INTO [{meta_table}] (key, value) VALUES "
                f"('last_sync_source', 'sync_smart_market.py (repo market layer full-mirror, approved 2026-07-05)')")
        smart.close()
    if failures:
        print(f"\nRESULT: FAIL ({len(failures)} tables): {failures}")
        return 1
    print(f"\nRESULT: ALL PASS (market layer repo=smart, synced at {now})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

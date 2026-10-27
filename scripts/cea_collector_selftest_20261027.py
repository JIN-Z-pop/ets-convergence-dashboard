#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cea_collector_selftest_20261027.py — cea_carbonmarket_collector.merge_and_insert() の累計列(cum_*_derived)のselftest。

合成DB(一時ディレクトリ)だけを使い、本番のchina_ets.db・ネットワークには一切触れない。
collector の DB_PATH を合成DBへ差し替えて merge_and_insert() を呼ぶ(fetch_tables は呼ばない)。

答える問い: 古い日付の行が後から届いた(後日着地)時に、累計列が「全履歴の合計」の定義と一致したままか。
            通常日(最新日より新しい行だけが届く)の累計は、従来の式と1ビットも違わないか。

(1) 後日着地: 最古より前(d0)と最新より後(d4)を同じrunで注入。
(2) 通常日(陰性対照): d4だけ。累計は従来式(最後の累計 + 自分)と一致し、既存行は不変。
(3) 後日着地のみ: d0だけ。後ろの既存行がすべて +50 される。
(4) 空run: 新規0件。既存行は不変・fetch_log に1行(records_added=0・status=success)。
(5) 丸めの陰性対照: 金額の累計は丸め無しの浮動小数加算(従来式)とビット一致する。
    初期の累計は逐次 += で作る(sum()やSQLのSUMは誤差補正で値が変わるため使わない)。
    ケース自身が「丸めると値が変わる組(prev + 0.1 != round(prev + 0.1, 4))」であることを実行時に確かめ、
    成り立たなければケース無効=FAIL(丸めの有無を区別できない値では、検査が常に通ってしまうため)。
(6) 基点NULL: 既存行の累計がNULLの所へ、最古より前の行を注入。全行が埋まる。
(7) 中間着地: 既存行の間(d2とd3の間)に1行だけ届く。前の行の累計を基点に、後ろの既存行を更新する経路を撃つ。

判定式: 日付順の隣接差 |cum - 直前のcum - total| が 出来高 <= 0.5・金額 <= 0.001。先頭行は0との差で見る。
        最終行のcum = 全履歴のtotalの合計。累計がNULLの行は違反として数える。
        ((5) は金額を == (ビット一致) で見る。)

答えない: 本番DB・ネットワーク・fetch_tables() のHTMLパース・外部の監査スクリプト・実データでの値。
          (監査の該当検査は出来高のみで先頭行を飛ばす。この判定式は金額・先頭行・最終行の合計も見る。)

Usage: python scripts/cea_collector_selftest_20261027.py [--target <collector.py のpath>]
終了コード: FAIL(または対象の不在・読込失敗)があれば0以外。全OKなら0。
"""
import argparse
import contextlib
import importlib.util
import io
import math
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

DEFAULT_TARGET = Path(__file__).resolve().parent / "cea_carbonmarket_collector.py"

# 本番の CREATE 文と同じ(合成DBを本番と同じ形にする)
DDL_CEA = """CREATE TABLE cea_daily (
    date TEXT PRIMARY KEY,
    opening_price REAL,
    high_price REAL,
    low_price REAL,
    closing_price REAL,
    listed_volume INTEGER,
    listed_amount REAL,
    block_volume INTEGER,
    block_amount REAL,
    total_volume INTEGER,
    total_amount REAL,
    fetched_at TEXT DEFAULT CURRENT_TIMESTAMP
, cum_volume_reported INTEGER, cum_amount_reported REAL, cum_volume_derived INTEGER, cum_amount_derived REAL)"""
DDL_LOG = """CREATE TABLE fetch_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market TEXT NOT NULL,
    fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
    records_added INTEGER DEFAULT 0,
    status TEXT NOT NULL,
    message TEXT
)"""

# 日付(間隔を空ける): d0 < d1 < d2 < dx < d3 < d4
D0, D1, D2, DX, D3, D4 = "2026-01-01", "2026-01-10", "2026-01-20", "2026-01-25", "2026-01-30", "2026-02-10"
INIT = [(D1, 100, 1.0), (D2, 200, 2.0), (D3, 300, 3.0)]           # (date, total_volume, total_amount)
INIT_ROUND = [(D1, 100, 0.1), (D2, 200, 0.2), (D3, 300, 0.3)]     # (5) 用: 金額に浮動小数の誤差が出る組


def build_db(path, rows, null_cum=False):
    """初期行を入れた合成DBを作る。累計は逐次 += で作る(sum()やSQLのSUMは使わない)。"""
    con = sqlite3.connect(str(path))
    con.execute(DDL_CEA)
    con.execute(DDL_LOG)
    cum_v, cum_a = 0, 0.0
    for d, v, a in rows:
        cum_v += v
        cum_a += a
        con.execute(
            "INSERT INTO cea_daily (date, opening_price, high_price, low_price, closing_price,"
            " listed_volume, listed_amount, block_volume, block_amount, total_volume, total_amount,"
            " cum_volume_derived, cum_amount_derived) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (d, 1.0, 1.0, 1.0, 1.0, v, a, 0, 0.0, v, a,
             None if null_cum else cum_v, None if null_cum else cum_a),
        )
    con.commit()
    con.close()


def listed_row(date, vol, amt):
    return {"date": date, "opening_price": 1.0, "closing_price": 1.0, "high_price": 1.0,
            "low_price": 1.0, "listed_volume": vol, "listed_amount": amt}


def run_merge(mod, db_path, inject):
    """collector の DB_PATH を合成DBへ向けて merge_and_insert() を呼ぶ(表示は捨てる)。"""
    mod.DB_PATH = Path(db_path)
    listed = [listed_row(d, v, a) for d, v, a in inject]
    with contextlib.redirect_stdout(io.StringIO()):
        return mod.merge_and_insert(listed, [])


def read_rows(db_path):
    con = sqlite3.connect(str(db_path))
    rows = con.execute("SELECT date, total_volume, total_amount, cum_volume_derived, cum_amount_derived"
                       " FROM cea_daily ORDER BY date").fetchall()
    con.close()
    return rows


def find_violations(rows):
    """累計の整合違反を文字列のリストで返す(NULLは違反)。先頭行は0との差で見る。"""
    out = []
    prev_v, prev_a = 0, 0.0
    for d, tv, ta, cv, ca in rows:
        if cv is None or ca is None:
            out.append("%s: 累計がNULL" % d)
            prev_v = prev_a = None
            continue
        if prev_v is not None:
            if abs(cv - prev_v - (tv or 0)) > 0.5:
                out.append("%s: 出来高の隣接差が合わない (cum=%s 直前=%s total=%s)" % (d, cv, prev_v, tv))
            if abs(ca - prev_a - (ta or 0.0)) > 0.001:
                out.append("%s: 金額の隣接差が合わない (cum=%r 直前=%r total=%r)" % (d, ca, prev_a, ta))
        prev_v, prev_a = cv, ca
    if rows and rows[-1][3] is not None and rows[-1][4] is not None:
        sum_v = sum((r[1] or 0) for r in rows)
        sum_a = math.fsum((r[2] or 0.0) for r in rows)
        if rows[-1][3] != sum_v:
            out.append("最終行の出来高cum=%s が全履歴の合計=%s と違う" % (rows[-1][3], sum_v))
        if abs(rows[-1][4] - sum_a) > 0.001:
            out.append("最終行の金額cum=%r が全履歴の合計=%r と違う" % (rows[-1][4], sum_a))
    return out


def cum_vol(rows):
    return [r[3] for r in rows]


def detail(rows, viol):
    s = "違反=%d件 cum出来高(日付順)=%s" % (len(viol), cum_vol(rows))
    return s + (" 例: " + viol[0] if viol else "")


def case_1(mod):
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "china_ets.db"
        build_db(db, INIT)
        run_merge(mod, db, [(D0, 50, 0.5), (D4, 400, 4.0)])
        rows = read_rows(db)
        viol = find_violations(rows)
        return (not viol and cum_vol(rows) == [50, 150, 350, 650, 1050]), detail(rows, viol) + " 期待=[50,150,350,650,1050]"


def case_2(mod):
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "china_ets.db"
        build_db(db, INIT)
        before = read_rows(db)
        run_merge(mod, db, [(D4, 400, 4.0)])
        rows = read_rows(db)
        viol = find_violations(rows)
        expect_a = before[-1][4] + 4.0
        same_before = rows[:3] == before
        ok = (not viol and same_before and cum_vol(rows) == [100, 300, 600, 1000] and rows[-1][4] == expect_a)
        return ok, detail(rows, viol) + " 既存行不変=%s 金額(d4)==直前+4.0: %s" % (same_before, rows[-1][4] == expect_a)


def case_3(mod):
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "china_ets.db"
        build_db(db, INIT)
        run_merge(mod, db, [(D0, 50, 0.5)])
        rows = read_rows(db)
        viol = find_violations(rows)
        return (not viol and cum_vol(rows) == [50, 150, 350, 650]), detail(rows, viol) + " 期待=[50,150,350,650]"


def case_4(mod):
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "china_ets.db"
        build_db(db, INIT)
        before = read_rows(db)
        result = run_merge(mod, db, [])
        rows = read_rows(db)
        con = sqlite3.connect(str(db))
        logs = con.execute("SELECT market, records_added, status FROM fetch_log").fetchall()
        con.close()
        ok = (rows == before and result == (0, []) and len(logs) == 1 and logs[0][1] == 0 and logs[0][2] == "success")
        return ok, "既存行不変=%s 戻り値=%r fetch_log=%r" % (rows == before, result, logs)


def case_5(mod):
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "china_ets.db"
        build_db(db, INIT_ROUND)
        before = read_rows(db)
        prev = before[-1][4]
        plain = prev + 0.1
        valid = (plain != round(plain, 4))     # ケースの自己確認: 丸めると値が変わる組でなければケース無効
        if not valid:
            return False, "ケース無効: prev+0.1=%r が round4=%r と同じ＝丸めの有無を区別できない" % (plain, round(plain, 4))
        run_merge(mod, db, [(D4, 400, 0.1)])
        rows = read_rows(db)
        got = rows[-1][4]
        viol = find_violations(rows)
        ok = (got == plain and rows[:3] == before and not viol)
        return ok, "prev=%r 従来式(prev+0.1)=%r round4=%r 実測=%r ビット一致=%s 既存行不変=%s 違反=%d件" % (
            prev, plain, round(plain, 4), got, got == plain, rows[:3] == before, len(viol))


def case_6(mod):
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "china_ets.db"
        build_db(db, INIT, null_cum=True)
        run_merge(mod, db, [(D0, 50, 0.5)])
        rows = read_rows(db)
        viol = find_violations(rows)
        return (not viol and cum_vol(rows) == [50, 150, 350, 650]), detail(rows, viol) + " 期待=[50,150,350,650]"


def case_7(mod):
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "china_ets.db"
        build_db(db, INIT)
        run_merge(mod, db, [(DX, 70, 0.7)])
        rows = read_rows(db)
        viol = find_violations(rows)
        return (not viol and cum_vol(rows) == [100, 300, 370, 670]), detail(rows, viol) + " 期待=[100,300,370,670]"


CASES = [
    ("(1)", "後日着地 最古より前と最新より後を同時に注入", case_1),
    ("(2)", "通常日(陰性対照) 最新より後だけ", case_2),
    ("(3)", "後日着地のみ 最古より前だけ", case_3),
    ("(4)", "空run 新規0件", case_4),
    ("(5)", "丸めの陰性対照 金額は丸め無しとビット一致", case_5),
    ("(6)", "基点NULL 累計NULLの既存行の前に注入", case_6),
    ("(7)", "中間着地 既存行の間に1行", case_7),
]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default=str(DEFAULT_TARGET), help="検査する collector.py のpath")
    args = ap.parse_args()

    if not os.path.exists(args.target):                  # 対象が無い時は合格にしない
        print("[ERROR] 対象が見つかりません: %s" % args.target)
        return 2
    spec = importlib.util.spec_from_file_location("cea_collector_under_test", args.target)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    print("=== cea collector selftest (合成DB・本番0接触) ===")
    print("target: %s" % args.target)
    print("recompute_cumulative_from: %s" % ("あり" if hasattr(mod, "recompute_cumulative_from") else "なし"))
    print("ケース: %d\n" % len(CASES))

    fails = 0
    for cid, name, fn in CASES:
        try:
            ok, msg = fn(mod)
        except Exception as e:                           # 例外は FAIL として数える
            ok, msg = False, "例外: %s: %s" % (type(e).__name__, e)
        print("  %s: %s %s — %s" % ("OK" if ok else "FAIL", cid, name, msg))
        if not ok:
            fails += 1

    print("\n%d/%d OK" % (len(CASES) - fails, len(CASES)))
    print("走査範囲: 合成DB上の merge_and_insert() の累計列のみ(7ケース)。")
    print("非対象  : 本番DB／ネットワーク／fetch_tables() のHTMLパース／外部の監査スクリプト／実データでの値。")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

"""Acceptance tests for fetch_eu_ets.py's DB-sourced yearly stats.

Run inside a git worktree of this repo: ROOT resolves relative to this file's location,
so it always operates on the worktree's own data/, never production data.

Usage:
    python scripts/tests/test_fetch_eu_ets_db_source.py --run
    python scripts/tests/test_fetch_eu_ets_db_source.py --pre   (freeze production baseline)
"""
import argparse
import importlib.util
import json
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FETCH_SCRIPT = ROOT / "scripts" / "fetch_eu_ets.py"
PRICES_JSON = ROOT / "data" / "prices.json"
EU_DB = ROOT / "data" / "eu_ets.db"

sys.path.insert(0, str(ROOT / "scripts"))
import fetch_eu_ets  # noqa: E402

PROD_ROOT = Path(r"C:\Users\jin_z\Desktop\ets-convergence-dashboard")
PROD_PRICES_JSON = PROD_ROOT / "data" / "prices.json"
PROD_EU_DB = PROD_ROOT / "data" / "eu_ets.db"

# Built from parts / escapes so this list's own definition never contains the literal
# forbidden strings (this file gets diffed by the very check that reads this list).
FORBIDDEN_VOCAB = ["DD" + "#", "\u594f", "\u84bc\u609f", "\u8449\u5c71", "bias" + "#",
                   "w" + "ip", "neural" + "-core", "p" + "ane"]

RESULTS = []


def _report(label, ok, detail=""):
    RESULTS.append((label, ok, detail))
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {label}{': ' + detail if detail else ''}")


def _md5(path):
    import hashlib
    return hashlib.md5(path.read_bytes()).hexdigest()


def _run_fetch():
    proc = subprocess.run([sys.executable, str(FETCH_SCRIPT)], cwd=str(ROOT),
                           capture_output=True, text=True, timeout=60)
    return proc.returncode, proc.stdout + proc.stderr


def _year_row(data, year):
    return next((r for r in data["eu_eur"] if r["year"] == str(year)), None)


def _load_module_from_source(src, tmp_path):
    """Write `src` to `tmp_path` (kept alongside FETCH_SCRIPT so its own ROOT resolves
    the same repo) and load it as an independent module. Caller deletes tmp_path."""
    tmp_path.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(tmp_path.stem, tmp_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SABOTAGE_TMP = ROOT / "scripts" / "_sabotage_tmp_fetch_eu_ets.py"


def check_1a():
    print("\n=== \u2460a: fetch_eu_ets.py \u5b9f\u884c(\u7db2OK) ===")
    year = time.localtime().tm_year
    rc, out = _run_fetch()
    ok_rc = (rc == 0)
    ok_src = ("from eu_ets.db" in out)
    con = sqlite3.connect(str(EU_DB))
    n, avg, mx, mn = fetch_eu_ets.year_stats_from_db(con, year)
    con.close()
    data = json.loads(PRICES_JSON.read_text(encoding="utf-8"))
    row = _year_row(data, year)
    ok_n = (f"({n} trading days" in out)
    ok_row = (row is not None and row["avg_price"] == fetch_eu_ets.half_up(avg)
              and row["max_price"] == fetch_eu_ets.half_up(mx) and row["min_price"] == fetch_eu_ets.half_up(mn))
    ok = ok_rc and ok_src and ok_n and ok_row
    _report("\u2460a rc=0+from eu_ets.db+n\u4e00\u81f4+eu_eur\u5024\u4e00\u81f4", ok,
             f"rc={rc} src_hit={ok_src} n={n} row={row}")
    return ok, {"rc": rc, "row": row, "n": n}


def check_1b():
    print("\n=== \u2460b: \u51aa\u7b49(\u5373\u65e5\u518d\u5b9f\u884c) ===")
    md5_before = _md5(PRICES_JSON)
    mtime_before = PRICES_JSON.stat().st_mtime
    rc, out = _run_fetch()
    md5_after = _md5(PRICES_JSON)
    mtime_after = PRICES_JSON.stat().st_mtime
    ok = (rc == 0) and ("UNCHANGED" in out) and (md5_before == md5_after) and (mtime_before == mtime_after)
    _report("\u2460b UNCHANGED+md5/mtime\u4e0d\u5909", ok,
             f"rc={rc} md5_equal={md5_before == md5_after} mtime_equal={mtime_before == mtime_after}")
    return ok


def check_1c():
    print("\n=== \u2460c: DB\u304c\u6b63(\u967d\u6027\u5bfe\u7167) ===")
    year = time.localtime().tm_year
    backup = ROOT / "data" / "eu_ets.db.bak_1c"
    shutil.copy2(EU_DB, backup)
    try:
        con = sqlite3.connect(str(EU_DB))
        date, close = con.execute(
            f"SELECT date, close_price FROM eu_ets_daily WHERE date LIKE '{year}-%' ORDER BY date LIMIT 1"
        ).fetchone()
        con.execute("UPDATE eu_ets_daily SET close_price=? WHERE date=?", (close + 10, date))
        con.commit()
        n, avg, mx, mn = fetch_eu_ets.year_stats_from_db(con, year)
        con.close()
        expected_avg = fetch_eu_ets.half_up(avg)
        rc, out = _run_fetch()
        data = json.loads(PRICES_JSON.read_text(encoding="utf-8"))
        row = _year_row(data, year)
        ok = (rc == 0) and ("CHANGED" in out) and (row is not None) and (row["avg_price"] == expected_avg)
        _report("\u2460c CHANGED+DB\u518d\u8a08\u7b97\u5024\u4e00\u81f4(live\u4e0d\u4f7f\u7528)", ok,
                 f"rc={rc} expected_avg={expected_avg} row_avg={row['avg_price'] if row else None}")
    finally:
        shutil.copy2(backup, EU_DB)
        backup.unlink()
    return ok


def check_1d():
    print("\n=== \u2460d: \u534a\u7aef\u306e\u4e38\u3081(\u95a2\u6570\u5358\u4f4d) ===")
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE eu_ets_daily (date TEXT PRIMARY KEY, close_price REAL)")
    con.execute("INSERT INTO eu_ets_daily (date, close_price) VALUES ('2026-01-05', 59.955)")
    con.commit()
    n, avg, mx, mn = fetch_eu_ets.year_stats_from_db(con, 2026)
    con.close()
    got = fetch_eu_ets.half_up(mn)
    ok = (got == 59.96)
    sabotage = round(mn, 2)
    _report("\u2460d half_up(59.955)==59.96(sabotage=float round->59.95)", ok,
             f"half_up={got} float_round={sabotage}")
    return ok


def check_1e():
    print("\n=== \u2460e: COUNT 0(\u95a2\u6570\u5358\u4f4d)+main() cur.empty\u7d4c\u8def ===")
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE eu_ets_daily (date TEXT PRIMARY KEY, close_price REAL)")
    con.commit()
    year_stats = fetch_eu_ets.year_stats_from_db(con, 2026)
    con.close()
    action, new_row = fetch_eu_ets.decide_update(year_stats, None, 2026, {})
    ok_fn = (year_stats[0] == 0) and (action == "NO_ROWS") and (new_row is None)

    main_src = FETCH_SCRIPT.read_text(encoding="utf-8")
    ok_main = ("if cur.empty:" in main_src and 'print(f"no {year} rows yet' in main_src
               and "return 1" not in main_src.split("if cur.empty:")[1].split("\n\n")[0])
    ok = ok_fn and ok_main
    _report("\u2460e n=0->NO_ROWS(new_row=None)+main() cur.empty\u7d4c\u8defreturn0", ok,
             f"year_stats={year_stats} action={action} main_return0={ok_main}")
    return ok


def check_1f():
    print("\n=== \u2460f: DB file\u4e0d\u5728 ===")
    con = sqlite3.connect(str(EU_DB))
    total_before = con.execute("SELECT COUNT(*) FROM eu_ets_daily").fetchone()[0]
    con.close()
    md5_before = _md5(EU_DB)
    retreat = ROOT / "data" / "eu_ets.db.retreat"
    shutil.move(str(EU_DB), str(retreat))
    try:
        rc, out = _run_fetch()
        exists_after = EU_DB.exists()
        ok_missing_msg = ("eu_ets.db missing" in out)
    finally:
        shutil.move(str(retreat), str(EU_DB))
    con = sqlite3.connect(str(EU_DB))
    total_after = con.execute("SELECT COUNT(*) FROM eu_ets_daily").fetchone()[0]
    con.close()
    md5_after = _md5(EU_DB)
    ok = (rc == 1) and ok_missing_msg and (not exists_after) and (total_before == total_after) and (md5_before == md5_after)
    _report("\u2460f rc=1+missing\u30e1\u30c3\u30bb\u30fc\u30b8+\u5b9f\u884c\u5f8c\u4e0d\u5728+\u5fa9\u5143md5/\u884c\u6570\u4e0d\u5909", ok,
             f"rc={rc} exists_after={exists_after} total={total_before}->{total_after} md5_equal={md5_before == md5_after}")
    return ok


def check_1g():
    print("\n=== \u2460g: \u95a2\u6570\u3068main()\u306e\u7d50\u5408 ===")
    year = time.localtime().tm_year
    rc, out = _run_fetch()
    con = sqlite3.connect(str(EU_DB))
    n, avg, mx, mn = fetch_eu_ets.year_stats_from_db(con, year)
    con.close()
    expected_line = (f"avg={fetch_eu_ets.half_up(avg)} max={fetch_eu_ets.half_up(mx)} "
                      f"min={fetch_eu_ets.half_up(mn)}")
    ok = (expected_line in out)
    _report("\u2460g main()\u5b9f\u8d70print\u5024==\u95a2\u6570\u76f4\u547c\u3073\u51fa\u3057\u5024", ok,
             f"expected={expected_line} rc={rc}")
    return ok


def check_2():
    print("\n=== \u2461 INSERT OR IGNORE\u7d4c\u8def diff 0 ===")
    prod_src = (PROD_ROOT / "scripts" / "fetch_eu_ets.py").read_text(encoding="utf-8")
    wt_src = FETCH_SCRIPT.read_text(encoding="utf-8")
    needle_start = 'REQUIRED_COLS = ["Open", "High", "Low", "Close", "Volume"]'
    needle_end = "new_count = cur_db.rowcount"

    def extract(text):
        s = text.index(needle_start)
        e = text.index(needle_end) + len(needle_end)
        return text[s:e]
    ok = extract(prod_src) == extract(wt_src)
    _report("\u2461 REQUIRED_COLS~executemany \u9010\u8a9e\u4e00\u81f4", ok, "")
    return ok


def check_3():
    print("\n=== \u2462 \u516c\u958b repo \u8a9e\u5f59\u898f\u7d04 ===")
    proc = subprocess.run(["git", "diff", "master"], cwd=str(ROOT), capture_output=True, text=True)
    diff_text = proc.stdout
    hits = []
    for v in FORBIDDEN_VOCAB:
        if v.lower() in diff_text.lower():
            hits.append(v)
    ok = (len(hits) == 0)
    _report("\u2462 diff\u5168\u4f53 grep 0(\u8a9e\u5f59\u306e\u307f\u5bfe\u8c61)", ok, f"hits={hits}")
    return ok


def check_4():
    print("\n=== \u2463 \u5168\u6570\u30c1\u30a7\u30c3\u30af ===")
    import py_compile
    ok_compile = True
    for f in [FETCH_SCRIPT, Path(__file__)]:
        try:
            py_compile.compile(str(f), doraise=True)
        except Exception as e:
            ok_compile = False
            print(f"  [FAIL] py_compile {f}: {e}")
    _report("\u2463a py_compile", ok_compile, "")

    index_html = (ROOT / "index.html").read_text(encoding="utf-8")
    ok_fields = all(k in index_html for k in ["eu_eur", "avg_price"])
    _report("\u2463b index.html \u8aad\u307f\u624bfield\u540d\u4e0d\u5909", ok_fields, "")

    ok = ok_compile and ok_fields
    return ok


def freeze_pre(out_path):
    print("\n=== --pre: 本番ベースライン凍結 ===")
    year = time.localtime().tm_year
    con = sqlite3.connect(str(PROD_EU_DB))
    n, avg, mx, mn = fetch_eu_ets.year_stats_from_db(con, year)
    con.close()
    data = json.loads(PROD_PRICES_JSON.read_text(encoding="utf-8"))
    row = _year_row(data, year)
    frozen = {
        "frozen_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "prod_db_year_stats": {"n": n, "avg": avg, "max": mx, "min": mn},
        "prod_prices_json_row": row,
        "prod_prices_json_md5": _md5(PROD_PRICES_JSON),
        "prod_eu_ets_db_md5": _md5(PROD_EU_DB),
    }
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(frozen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[FROZEN] {out_path}")
    print(json.dumps(frozen, ensure_ascii=False, indent=2))


def selftest_1d():
    print("\n=== ①d selftest: half_upをfloat roundに戻すsabotage(一時copy上・対象fileは読むだけ) ===")
    md5_pre = _md5(FETCH_SCRIPT)
    orig_src = FETCH_SCRIPT.read_text(encoding="utf-8")
    needle = 'return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))'
    replacement = "return round(float(value), 2)  # SABOTAGED"
    if needle not in orig_src:
        print("  [SKIP] needle not found")
        _report("①d selftest(float round化->RED)", False, "SKIP: needle not found")
        return None
    sabotaged_src = orig_src.replace(needle, replacement, 1)
    module = _load_module_from_source(sabotaged_src, SABOTAGE_TMP)
    try:
        con = sqlite3.connect(":memory:")
        con.execute("CREATE TABLE eu_ets_daily (date TEXT PRIMARY KEY, close_price REAL)")
        con.execute("INSERT INTO eu_ets_daily (date, close_price) VALUES ('2026-01-05', 59.955)")
        con.commit()
        n, avg, mx, mn = module.year_stats_from_db(con, 2026)
        con.close()
        got = module.half_up(mn)
        is_red = (got == 59.95)
        print(f"  sabotaged half_up(59.955)={got} -> {'RED(期待通り)' if is_red else 'GREEN(検知失敗)'}")
    finally:
        SABOTAGE_TMP.unlink()
    md5_post = _md5(FETCH_SCRIPT)
    assert md5_pre == md5_post, f"FAIL: FETCH_SCRIPT was touched! pre={md5_pre} post={md5_post}"
    _report("①d selftest(float round化->59.95=RED)+対象file md5 pre==post", is_red,
             f"got={got} target_md5_unchanged={md5_pre == md5_post}")
    return is_red


def selftest_1e():
    print("\n=== ①e selftest: decide_updateがNO_ROWSでも書換行を返すsabotage(一時copy上) ===")
    md5_pre = _md5(FETCH_SCRIPT)
    orig_src = FETCH_SCRIPT.read_text(encoding="utf-8")
    needle = 'if n == 0:\n        return "NO_ROWS", None'
    replacement = ('if n == 0:\n        return "NO_ROWS", {"year": str(year), "avg_price": 0.0, '
                   '"max_price": 0.0, "min_price": 0.0, "phase": phase_map.get(year, "Phase 4")}'
                   '  # SABOTAGED')
    if needle not in orig_src:
        print("  [SKIP] needle not found")
        _report("①e selftest(NO_ROWSでも書換行->RED)", False, "SKIP: needle not found")
        return None
    sabotaged_src = orig_src.replace(needle, replacement, 1)
    module = _load_module_from_source(sabotaged_src, SABOTAGE_TMP)
    try:
        con = sqlite3.connect(":memory:")
        con.execute("CREATE TABLE eu_ets_daily (date TEXT PRIMARY KEY, close_price REAL)")
        con.commit()
        year_stats = module.year_stats_from_db(con, 2026)
        con.close()
        action, new_row = module.decide_update(year_stats, None, 2026, {})
        is_red = (action == "NO_ROWS" and new_row is not None)
        print(f"  sabotaged action={action} new_row={new_row} -> {'RED(期待通り)' if is_red else 'GREEN(検知失敗)'}")
    finally:
        SABOTAGE_TMP.unlink()
    md5_post = _md5(FETCH_SCRIPT)
    assert md5_pre == md5_post, f"FAIL: FETCH_SCRIPT was touched! pre={md5_pre} post={md5_post}"
    _report("①e selftest(NO_ROWSでも書換行を返す->RED)+対象file md5 pre==post", is_red,
             f"action={action} new_row={new_row} target_md5_unchanged={md5_pre == md5_post}")
    return is_red


def selftest_1f():
    print("\n=== ①f selftest: EU_DB.exists()確認を外すsabotage(一時copy上・db再生成を確認) ===")
    md5_pre = _md5(FETCH_SCRIPT)
    orig_src = FETCH_SCRIPT.read_text(encoding="utf-8")
    needle = ('    if not EU_DB.exists():\n'
              '        print(f"eu_ets.db missing: {EU_DB}")\n'
              '        return 1\n\n')
    if needle not in orig_src:
        print("  [SKIP] needle not found")
        _report("①f selftest(exists確認削除->db再生成=RED)", False, "SKIP: needle not found")
        return None
    sabotaged_src = orig_src.replace(needle, "", 1)
    SABOTAGE_TMP.write_text(sabotaged_src, encoding="utf-8")
    retreat = ROOT / "data" / "eu_ets.db.retreat_selftest"
    shutil.move(str(EU_DB), str(retreat))
    try:
        proc = subprocess.run([sys.executable, str(SABOTAGE_TMP)], cwd=str(ROOT),
                               capture_output=True, text=True, timeout=60)
        exists_after = EU_DB.exists()
        total_after = None
        if exists_after:
            con = sqlite3.connect(str(EU_DB))
            total_after = con.execute("SELECT COUNT(*) FROM eu_ets_daily").fetchone()[0]
            con.close()
        is_red = exists_after and (total_after is not None and total_after < 583)
        print(f"  sabotaged rc={proc.returncode} exists_after={exists_after} total_after={total_after} "
              f"-> {'RED(期待通り=db再生成)' if is_red else 'GREEN(検知失敗)'}")
    finally:
        SABOTAGE_TMP.unlink()
        if EU_DB.exists():
            EU_DB.unlink()
        shutil.move(str(retreat), str(EU_DB))
    md5_post = _md5(FETCH_SCRIPT)
    assert md5_pre == md5_post, f"FAIL: FETCH_SCRIPT was touched! pre={md5_pre} post={md5_post}"
    _report("①f selftest(exists確認削除->db再生成(583->約505)=RED)+対象file md5 pre==post", is_red,
             f"rc={proc.returncode} total_after={total_after} target_md5_unchanged={md5_pre == md5_post}")
    return is_red


def run_selftests():
    results = [selftest_1d(), selftest_1e(), selftest_1f()]
    confirmed = sum(1 for r in results if r is True)
    skipped = sum(1 for r in results if r is None)
    ok = (confirmed == 3 and skipped == 0)
    print(f"\n=== SELFTEST SUMMARY: {confirmed}/3 RED confirmed" + (f" skipped={skipped}" if skipped else "") + " ===")
    return ok


def run_all():
    checks = [check_1a, check_1b, check_1c, check_1d, check_1e, check_1f, check_1g,
              check_2, check_3, check_4]
    for c in checks:
        c()
    total = len(RESULTS)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    print(f"\n=== SUMMARY: {passed}/{total} PASS ===")
    for label, ok, detail in RESULTS:
        if not ok:
            print(f"  [FAIL] {label}: {detail}")
    return passed == total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--selftest", action="store_true", help="run sabotage checks for ①d/①e/①f")
    parser.add_argument("--pre", action="store_true")
    parser.add_argument("--out", default=None, help="output path for --pre (required with --pre)")
    args = parser.parse_args()
    if args.pre:
        if not args.out:
            parser.error("--pre requires --out <path>")
        freeze_pre(args.out)
        return
    ran = False
    ok = True
    if args.run:
        ran = True
        ok = run_all() and ok
    if args.selftest:
        ran = True
        ok = run_selftests() and ok
    if not ran:
        parser.print_help()
        return
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

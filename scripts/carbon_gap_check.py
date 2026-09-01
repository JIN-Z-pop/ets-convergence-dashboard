#!/usr/bin/env python3
"""carbon_gap_check.py - verify the carbon-market DBs have no missing trading days.

Part of the daily carbon cycle (gap-aware self-heal). READ-ONLY: it does not
mutate any DB. Backfill itself is done by re-running the collectors (which insert
any missing dates the source still exposes); this checker makes any remaining
hole VISIBLE so a silently-skipped/crashed cycle can never hide a permanent loss.

Uses market_holidays_2026.json to know which days SHOULD have data, so weekends
and holidays are never mis-flagged as gaps. Chinese (CEA/CCER) and Korean (KAU)
calendars differ (e.g. 2026-06-19 Dragon Boat: closed in CN, open in KR), so each
market is checked against its own calendar.

Gap classification (avoids false alarms from publication lag):
  - GAP  (interior): a missing trading day BEFORE the latest stored date.
                     A real hole the collector failed to fill -> investigate.
  - LAG  (trailing): missing trading day(s) AFTER the latest stored date.
                     Usually source publication lag / a not-yet-run cycle; will
                     fill on the next successful collection. Informational.

Exit code: 0 = no interior gaps (clean). 1 = interior gap found (needs attention).

Usage:
  python carbon_gap_check.py                 # check all markets, default 45-day window
  python carbon_gap_check.py --lookback 90   # widen the window
  python carbon_gap_check.py --self-test     # verify the gap logic itself
"""
import argparse
import datetime
import json
import sqlite3
import sys

HOLIDAYS = r"C:\Users\jin_z\market_holidays_2026.json"
CHINA_DB = r"C:\Users\jin_z\Desktop\china-ets-mcp\data\china_ets.db"
KOREA_DB = r"C:\Users\jin_z\Desktop\korea-ets-mcp\data\korea_ets.db"


def daterange(d0, d1):
    d = d0
    while d <= d1:
        yield d
        d += datetime.timedelta(days=1)


def load_closures(path):
    """Return (china_closure_set, korea_closure_set, cal_start).

    cal_start = Jan 1 of the earliest calendar year covered, used to clamp the
    scan window: dates before the calendar's coverage (e.g. a 2025 year-end
    closure when only the 2026 calendar is loaded) cannot be judged and must
    not be mis-flagged as gaps.
    """
    cal = json.load(open(path, encoding="utf-8"))
    china = set()
    for c in cal["china"]["closures"]:
        a, b = c["range"]
        a = datetime.date.fromisoformat(a)
        b = datetime.date.fromisoformat(b)
        china.update(daterange(a, b))
    korea = {datetime.date.fromisoformat(c["date"]) for c in cal["korea"]["closures"]}
    min_year = min(d.year for d in (china | korea))
    return china, korea, datetime.date(min_year, 1, 1)


def is_trading_day(d, closures):
    return d.weekday() < 5 and d not in closures


def expected_trading_days(start, end, closures):
    return [d for d in daterange(start, end) if is_trading_day(d, closures)]


def db_dates(db, query):
    con = sqlite3.connect(db)
    try:
        out = set()
        for (v,) in con.execute(query):
            try:
                out.add(datetime.date.fromisoformat(str(v)))
            except ValueError:
                pass
        return out
    finally:
        con.close()


def db_vintages(db, query):
    """Return {date: set(vintage_label)} from a (date, vintage) query."""
    con = sqlite3.connect(db)
    try:
        out = {}
        for (d, vintage) in con.execute(query):
            try:
                dt = datetime.date.fromisoformat(str(d))
            except ValueError:
                continue
            out.setdefault(dt, set()).add(str(vintage))
        return out
    finally:
        con.close()


def detect_vintage_drop(date_vintages):
    """Pure fn: {date: vintage_set} -> (dropped_set, latest_date, prev_date).

    Compares the two most recent dates present in the data (no calendar lookup
    needed - "most recent 2 trading days" is just the data's own last 2 dates).
    Returns (set(), None, None) when there are fewer than 2 dates to compare.
    """
    dates = sorted(date_vintages)
    if len(dates) < 2:
        return set(), None, None
    prev_d, latest_d = dates[-2], dates[-1]
    dropped = date_vintages[prev_d] - date_vintages[latest_d]
    return dropped, latest_d, prev_d


def fmt_vintage_drop(dropped, prev_d):
    names = ",".join(sorted(dropped))
    return (f"  !! VINTAGE-DROP: {names} (last={prev_d.isoformat()}) -- "
            f"annual rollover likely if Aug-Sep; verify KRX listing")


def check_market(name, dates, closures, today, lookback, cal_start=None):
    if not dates:
        return {"name": name, "latest": None, "interior": [], "trailing": [], "status": "NODATA"}
    latest = max(dates)
    start = today - datetime.timedelta(days=lookback)
    if cal_start and start < cal_start:
        start = cal_start  # don't scan before the calendar's coverage
    yesterday = today - datetime.timedelta(days=1)  # exclude today: EOD may not be published yet
    expected = expected_trading_days(start, yesterday, closures)
    missing = sorted(set(expected) - dates)
    interior = [d for d in missing if d < latest]   # hole before latest = real gap
    trailing = [d for d in missing if d > latest]   # behind the front = freshness lag
    status = "GAP" if interior else ("LAG" if trailing else "OK")
    return {"name": name, "latest": latest, "interior": interior, "trailing": trailing, "status": status}


def fmt(days):
    return ",".join(d.isoformat() for d in days) if days else "-"


def run(lookback, today=None):
    today = today or datetime.date.today()
    china, korea, cal_start = load_closures(HOLIDAYS)
    markets = [
        ("CEA  ", CHINA_DB, "SELECT date FROM cea_daily", china),
        ("CCER ", CHINA_DB, "SELECT date FROM ccer_daily", china),
        ("KAU  ", KOREA_DB, "SELECT DISTINCT date FROM kets_kau_ohlcv WHERE kau_type LIKE 'KAU%'", korea),
    ]
    print(f"=== carbon_gap_check  (today={today}, lookback={lookback}d) ===")
    results = []
    for name, db, query, closures in markets:
        try:
            dates = db_dates(db, query)
        except sqlite3.Error as e:
            print(f"  {name}  DB ERROR: {e}")
            results.append({"name": name, "status": "DBERR", "interior": [], "trailing": [], "latest": None})
            continue
        r = check_market(name.strip(), dates, closures, today, lookback, cal_start)
        results.append(r)
        latest = r["latest"].isoformat() if r["latest"] else "NONE"
        flag = {"OK": "OK", "LAG": "~ LAG", "GAP": "!! GAP", "NODATA": "!! NODATA"}[r["status"]]
        line = f"  {name}  latest={latest}  interior_gap={fmt(r['interior'])}  trailing={fmt(r['trailing'])}  -> {flag}"
        print(line)
    interior_hit = [r for r in results if r.get("interior")]
    err_hit = [r for r in results if r.get("status") in ("DBERR", "NODATA")]

    dropped, latest_d, prev_d = set(), None, None
    try:
        vintages = db_vintages(KOREA_DB, "SELECT date, kau_type FROM kets_kau_ohlcv WHERE kau_type LIKE 'KAU%'")
        dropped, latest_d, prev_d = detect_vintage_drop(vintages)
    except sqlite3.Error as e:
        print(f"  VINTAGE-DROP check DB ERROR: {e}")
    if dropped:
        print(fmt_vintage_drop(dropped, prev_d))

    print("-" * 60)
    if interior_hit or err_hit or dropped:
        parts = [f"{r['name'].strip()}:{fmt(r['interior'])}" for r in interior_hit]
        parts += [f"{r['name'].strip()}:{r['status']}" for r in err_hit]
        if dropped:
            parts.append(f"VINTAGE-DROP:{','.join(sorted(dropped))}")
        tail = ("(annual rollover likely if Aug-Sep -- verify KRX listing)"
                if (dropped and not interior_hit and not err_hit)
                else "(re-run collectors; if persists, source/out-of-window -> report)")
        print(f"RESULT: ATTENTION -> {', '.join(parts)}  {tail}")
        return 1
    lag_hit = [r for r in results if r.get("trailing")]
    if lag_hit:
        names = ", ".join(f"{r['name'].strip()}:{fmt(r['trailing'])}" for r in lag_hit)
        print(f"RESULT: ALL INTERIOR CLEAN  (trailing lag: {names} - normal publication lag / will fill next run)")
    else:
        print("RESULT: ALL CLEAN  (every expected trading day present, no gaps)")
    return 0


def self_test():
    """Verify the gap classification logic on synthetic data."""
    today = datetime.date(2026, 6, 27)
    china, korea, cal_start = load_closures(HOLIDAYS)
    ok = True

    # 1) holidays/weekends must NOT be expected: 6/19-21 closed for CN, 6/20-21 weekend
    exp = expected_trading_days(datetime.date(2026, 6, 15), datetime.date(2026, 6, 26), china)
    for bad in (datetime.date(2026, 6, 19), datetime.date(2026, 6, 20), datetime.date(2026, 6, 21)):
        if bad in exp:
            print(f"  FAIL: {bad} wrongly expected as CN trading day"); ok = False
    # KR traded 6/19 (not a KR holiday) -> must be expected
    exp_kr = expected_trading_days(datetime.date(2026, 6, 15), datetime.date(2026, 6, 26), korea)
    if datetime.date(2026, 6, 19) not in exp_kr:
        print("  FAIL: 6/19 should be a KR trading day"); ok = False

    # build a COMPLETE set over the exact window check_market scans (today-45 .. yesterday)
    lookback = 45
    start = today - datetime.timedelta(days=lookback)
    yesterday = today - datetime.timedelta(days=1)
    full = set(expected_trading_days(start, yesterday, china))

    # 2) interior hole detected: full set minus one interior trading day (6/24)
    holed = full - {datetime.date(2026, 6, 24)}
    r = check_market("TEST", holed, china, today, lookback)
    if r["status"] != "GAP" or datetime.date(2026, 6, 24) not in r["interior"]:
        print(f"  FAIL: interior hole 6/24 not detected -> {r}"); ok = False

    # 3) trailing lag (latest behind front), NOT flagged as interior GAP
    last3 = sorted(full)[-3:]
    behind = full - set(last3)
    r2 = check_market("TEST", behind, china, today, lookback)
    if r2["status"] != "LAG" or r2["interior"]:
        print(f"  FAIL: trailing lag misclassified -> {r2}"); ok = False

    # 4) complete set = OK
    r3 = check_market("TEST", full, china, today, lookback)
    if r3["status"] != "OK":
        print(f"  FAIL: complete set not OK -> {r3}"); ok = False

    # 5) vintage drop: KAU25 present the prior day, gone on the latest day
    dv_drop = {
        datetime.date(2026, 8, 31): {"KAU25", "KAU26"},
        datetime.date(2026, 9, 1): {"KAU26"},
    }
    dropped, _, prev_d = detect_vintage_drop(dv_drop)
    if dropped != {"KAU25"} or prev_d != datetime.date(2026, 8, 31):
        print(f"  FAIL: vintage drop not detected -> {dropped, prev_d}"); ok = False

    # 6) all vintages continue -> no alarm (#127.N: the opposite-answer case must be checked too)
    dv_continue = {
        datetime.date(2026, 8, 31): {"KAU25", "KAU26"},
        datetime.date(2026, 9, 1): {"KAU25", "KAU26"},
    }
    dropped2, _, _ = detect_vintage_drop(dv_continue)
    if dropped2:
        print(f"  FAIL: false vintage-drop alarm on continuous data -> {dropped2}"); ok = False

    print("SELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lookback", type=int, default=45, help="window (calendar days) to scan back")
    ap.add_argument("--self-test", action="store_true", help="verify the gap logic itself")
    args = ap.parse_args()
    sys.exit(self_test() if args.self_test else run(args.lookback))


if __name__ == "__main__":
    main()

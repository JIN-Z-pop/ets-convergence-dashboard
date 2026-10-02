"""Update data/prices.json china_cny / korea_krw yearly rows (and top-level as_of) from the
unified market DB, so the published yearly averages follow the daily collection.

Definitions (match the rows already published for finished years):
  china_cny  : market='CEA', no_trade=0, close_price not null, grouped by calendar year.
               avg/max/min = close price (2-decimal, half-up), total_volume = SUM(volume) (float).
  korea_krw  : every market LIKE 'KAU%' row with a close price, all vintages summed together
               (rows of vintages that did not trade are included on purpose: series continuity).
               avg = whole KRW (half-up, stored as float), max/min = int, trading_days = row count.
  as_of      : latest date per market {"china", "korea", "eu"} (eu from eu_ets.db; kept as is when
               that DB is not available).

Only rows whose JSON form differs are replaced, so an unchanged day leaves the file untouched.
The file is written with Path.write_text (same as fetch_eu_ets.py) so the checkout's line endings
are preserved. Paths of the unified DB come from local_paths ("smart_db"), never from this file.

Exit codes: 0 = ok (changed or unchanged) / 1 = a market had zero source rows (nothing written) /
            2 = a required DB file is missing (nothing written, no empty DB is created).
Usage: python scripts/update_yearly_prices.py [--dry-run] [--prices PATH] [--eu-db PATH]
"""
import argparse
import json
import sqlite3
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from local_paths import require  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PRICES_JSON = ROOT / "data" / "prices.json"
EU_DB = ROOT / "data" / "eu_ets.db"

CHINA_WHERE = "market='CEA' AND no_trade=0 AND close_price IS NOT NULL"
KOREA_WHERE = "market LIKE 'KAU%' AND close_price IS NOT NULL"


def agg_sql(where):
    return ("SELECT substr(date,1,4), COUNT(*), MAX(close_price), MIN(close_price), SUM(volume), MAX(date) "
            f"FROM ets_daily WHERE {where} GROUP BY 1 ORDER BY 1")


def closes_sql(where):
    return f"SELECT substr(date,1,4), close_price FROM ets_daily WHERE {where}"


def half_up(value, places=0):
    """Round half up on the decimal repr (Python's round() is banker's rounding)."""
    q = Decimal(1).scaleb(-places)
    return Decimal(str(value)).quantize(q, rounding=ROUND_HALF_UP)


def exact_avg_by_year(rows):
    """Mean of the stored closes per year, computed on their decimal text (not on float sums), so a
    true x.xx5 / x.5 tie is rounded half-up instead of being decided by float noise
    (SQLite AVG of 50.00 and 50.01 is 50.00499999999999)."""
    sums, counts = {}, {}
    for year, close in rows:
        sums[year] = sums.get(year, Decimal(0)) + Decimal(str(close))
        counts[year] = counts.get(year, 0) + 1
    return {y: sums[y] / Decimal(counts[y]) for y in sums}


def china_row(year, avg, mx, mn, volume):
    return {
        "year": year,
        "avg_price": float(half_up(avg, 2)),
        "max_price": float(half_up(mx, 2)),
        "min_price": float(half_up(mn, 2)),
        "total_volume": float(volume or 0),
    }


def korea_row(year, n, avg, mx, mn):
    return {
        "year": year,
        "avg_price": float(half_up(avg, 0)),
        "max_price": int(half_up(mx, 0)),
        "min_price": int(half_up(mn, 0)),
        "trading_days": int(n),
    }


def open_ro(path):
    """Open an existing SQLite file read-only. Never creates a file."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(str(p))
    return sqlite3.connect(p.resolve().as_uri() + "?mode=ro", uri=True)


def jdump(row):
    return json.dumps(row, ensure_ascii=False)


def merge_rows(existing, computed):
    """Replace rows whose JSON form differs, append unseen years in year order.
    Returns (new_list, changes) where changes = [(year, old_row_or_None, new_row)]."""
    by_year = {r["year"]: r for r in computed}
    out, changes, seen = [], [], set()
    for row in existing:
        y = row.get("year")
        new = by_year.get(y)
        seen.add(y)
        if new is not None and jdump(new) != jdump(row):
            changes.append((y, row, new))
            out.append(new)
        else:
            out.append(row)
    for y in sorted(by_year):
        if y not in seen:
            changes.append((y, None, by_year[y]))
            out.append(by_year[y])
    return out, changes


def describe(old, new):
    if old is None:
        return "new row " + jdump(new)
    parts = [f"{k} {old.get(k)}->{v}" for k, v in new.items() if jdump(old.get(k)) != jdump(v)]
    return ", ".join(parts)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="print the diff, write nothing")
    ap.add_argument("--prices", default=str(PRICES_JSON), help="prices.json to update")
    ap.add_argument("--eu-db", default=str(EU_DB), help="eu_ets.db (read-only, for as_of.eu)")
    args = ap.parse_args(argv)

    prices_path = Path(args.prices)
    try:
        smart_path = require("smart_db")
        smart = open_ro(smart_path)
    except (KeyError, FileNotFoundError) as e:
        print(f"[ERROR] unified market DB not available: {type(e).__name__}: {e}", file=sys.stderr)
        return 2

    china_src = smart.execute(agg_sql(CHINA_WHERE)).fetchall()
    korea_src = smart.execute(agg_sql(KOREA_WHERE)).fetchall()
    china_avg = exact_avg_by_year(smart.execute(closes_sql(CHINA_WHERE)).fetchall())
    korea_avg = exact_avg_by_year(smart.execute(closes_sql(KOREA_WHERE)).fetchall())
    smart.close()
    for label, src in (("china_cny", china_src), ("korea_krw", korea_src)):
        if not src:
            print(f"[ERROR] {label}: 0 source rows read (wrong market code or empty DB) - nothing written",
                  file=sys.stderr)
            return 1

    data = json.loads(prices_path.read_text(encoding="utf-8"))
    results = {}
    # src row = (year, n, max, min, sum_volume, max_date)
    for label, src, build in (
        ("china_cny", china_src, lambda r: china_row(r[0], china_avg[r[0]], r[2], r[3], r[4])),
        ("korea_krw", korea_src, lambda r: korea_row(r[0], r[1], korea_avg[r[0]], r[2], r[3])),
    ):
        computed = [build(r) for r in src]
        new_list, changes = merge_rows(data[label], computed)
        results[label] = (new_list, changes)
        rows_read = sum(r[1] for r in src)
        print(f"[{label}] source rows read={rows_read} years={len(src)} "
              f"changed={len(changes)} unchanged={len(src) - len(changes)}")
        for y, old, new in changes:
            print(f"  {y}: {describe(old, new)}")

    latest = {"china": max(r[5] for r in china_src), "korea": max(r[5] for r in korea_src)}
    eu_latest = None
    try:
        con = open_ro(args.eu_db)
        eu_latest = con.execute("SELECT MAX(date) FROM eu_ets_daily").fetchone()[0]
        con.close()
    except (FileNotFoundError, sqlite3.Error) as e:
        print(f"[WARN] eu_ets.db not readable ({type(e).__name__}): as_of.eu is left as is")
    old_as_of = data.get("as_of")
    new_as_of = {"china": latest["china"], "korea": latest["korea"]}
    if eu_latest:
        new_as_of["eu"] = eu_latest
    elif isinstance(old_as_of, dict) and "eu" in old_as_of:
        new_as_of["eu"] = old_as_of["eu"]
    as_of_changed = jdump(new_as_of) != jdump(old_as_of)
    print(f"[as_of] {'changed' if as_of_changed else 'unchanged'}: {jdump(old_as_of)} -> {jdump(new_as_of)}")

    any_change = as_of_changed or any(ch for _, ch in results.values())
    if not any_change:
        print("no change: prices.json untouched")
        return 0
    if args.dry_run:
        print("[DRY-RUN] nothing written")
        return 0
    for label, (new_list, _) in results.items():
        data[label] = new_list
    data["as_of"] = new_as_of
    prices_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("prices.json updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

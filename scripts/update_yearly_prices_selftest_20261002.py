#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""update_yearly_prices_selftest_20261002.py — stage_yearly_prices() / update_yearly_prices.py のselftest。

合成DB(一時ディレクトリ)だけを使い、本番のprices.json・統一正本・eu_ets.dbには一切触れない。
統一正本の差し替えは環境変数 ETS_LOCAL_PATHS(local_paths.py が読む設定JSON)で行う。

(1) 陽性: 変更あり -> stage=ok(alertsなし)・中国/韓国の行が合成DBの値になる・no_trade=1の行は中国から除外・
    eu_eur/fxは無変更・行のキー順と型(中国=全float・韓国 avg=float / max,min,日数=int)・as_ofが入る。
(2) 統一正本が空/不在 -> alertsが1件(stage Y)で prices.json は1バイトも変わらない・不在pathに空DBを作らない。
(3) 変更なし -> 2回目の実行でファイルのバイトもmtimeも変わらない。
(4) x.5の丸め: 平均が .xx5 / .5 ちょうどになる合成行で half-up(10001 / 50.01)。
    対照: Pythonのround()は偶数丸め(10000)・SQLiteのAVG(浮動小数の和)の直接丸めは 50.0 になる
    =このケースは half-up・厳密平均を、偶数丸め・浮動小数ノイズから区別できる。
加えて列挙: docstring・表示ラベル2か所・main()にYが載っている(ソースの目視代替)。

非対象: main()全体の実走(同日ガードにより本番の朝が初実走)・統一正本そのものの正しさ・実データでの値。
Usage: python scripts/update_yearly_prices_selftest_20261002.py
"""
import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent / "morning_ets_pipeline.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("morning_ets_pipeline", MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_smart(path, rows):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE ets_daily (market TEXT, date TEXT, close_price REAL, volume REAL, no_trade INTEGER)")
    con.executemany("INSERT INTO ets_daily VALUES (?,?,?,?,?)", rows)
    con.commit()
    con.close()


def make_eu(path, last_date):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE eu_ets_daily (date TEXT PRIMARY KEY, close_price REAL)")
    con.execute("INSERT INTO eu_ets_daily VALUES (?, 70.0)", (last_date,))
    con.commit()
    con.close()


def stale_prices():
    return {
        "china_cny": [{"year": "2025", "avg_price": 1.0, "max_price": 1.0, "min_price": 1.0, "total_volume": 1.0}],
        "korea_krw": [{"year": "2025", "avg_price": 1.0, "max_price": 1, "min_price": 1, "trading_days": 1}],
        "eu_eur": [{"year": "2025", "avg_price": 70.0, "max_price": 80.0, "min_price": 60.0, "phase": "Phase 4"}],
        "fx": {"KRW_USD": 0.0007},
    }


def write_prices(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run():
    m = _load_module()
    fails = 0

    def check(name, ok, detail=""):
        nonlocal fails
        print(f"  {'OK' if ok else 'FAIL'}: {name}" + (f" — {detail}" if detail else ""))
        if not ok:
            fails += 1

    saved_env = os.environ.get("ETS_LOCAL_PATHS")
    try:
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            eu_db = td / "eu_ets.db"
            make_eu(eu_db, "2026-10-01")

            def use_smart(smart_path):
                cfg = td / "local_paths_test.json"
                cfg.write_text(json.dumps({"smart_db": str(smart_path)}), encoding="utf-8")
                os.environ["ETS_LOCAL_PATHS"] = str(cfg)

            def stage(prices_path):
                return m.stage_yearly_prices(["--prices", str(prices_path), "--eu-db", str(eu_db)])

            # ---- (1) 陽性 ----
            smart = td / "smart1.db"
            make_smart(smart, [
                ("CEA", "2025-03-03", 100.00, 10, 0),
                ("CEA", "2025-03-04", 101.00, 20, 0),
                ("CEA", "2025-03-05", 999.00, 5, 1),          # no_trade=1 -> 中国から除外されること
                ("KAU25", "2025-03-03", 10000, 1, 0),
                ("KAU25", "2025-03-04", 10001, 1, 0),
                ("KAU26", "2025-03-04", 20000, 0, 1),         # 取引0日の銘柄も韓国は合算に入る
            ])
            use_smart(smart)
            prices = td / "prices1.json"
            write_prices(prices, stale_prices())
            before = json.loads(prices.read_text(encoding="utf-8"))
            result = stage(prices)
            after = json.loads(prices.read_text(encoding="utf-8"))
            check("(1) 陽性: stage=ok(alertsなし・list型)", result == [], f"result={result}")
            cn, kr = after["china_cny"][0], after["korea_krw"][0]
            check("(1) 中国行=終値のみ(no_trade=1除外)・キー順・全float",
                  list(cn.keys()) == ["year", "avg_price", "max_price", "min_price", "total_volume"]
                  and cn == {"year": "2025", "avg_price": 100.5, "max_price": 101.0, "min_price": 100.0,
                             "total_volume": 30.0}
                  and all(isinstance(cn[k], float) for k in ("avg_price", "max_price", "min_price", "total_volume")),
                  f"cn={cn}")
            check("(1) 韓国行=全KAU銘柄合算(3行)・avg=float / max,min,日数=int",
                  kr == {"year": "2025", "avg_price": 13334.0, "max_price": 20000, "min_price": 10000,
                         "trading_days": 3}
                  and isinstance(kr["avg_price"], float)
                  and all(type(kr[k]) is int for k in ("max_price", "min_price", "trading_days")),
                  f"kr={kr}")
            check("(1) eu_eur・fxは無変更", after["eu_eur"] == before["eu_eur"] and after["fx"] == before["fx"])
            check("(1) as_of={china,korea,eu}の最新日",
                  after.get("as_of") == {"china": "2025-03-04", "korea": "2025-03-04", "eu": "2026-10-01"},
                  f"as_of={after.get('as_of')}")

            # ---- (3) 変更なし(1の状態にもう一度) ----
            b1, m1 = prices.read_bytes(), prices.stat().st_mtime_ns
            result3 = stage(prices)
            b2, m2 = prices.read_bytes(), prices.stat().st_mtime_ns
            check("(3) 変更なし: 2回目はok・バイトもmtimeも不変", result3 == [] and b1 == b2 and m1 == m2,
                  f"result={result3} bytes_same={b1 == b2} mtime_same={m1 == m2}")

            # ---- (2) 統一正本が空 / 不在 ----
            empty = td / "smart_empty.db"
            make_smart(empty, [])
            use_smart(empty)
            prices2 = td / "prices2.json"
            write_prices(prices2, stale_prices())
            raw_before = prices2.read_bytes()
            result2 = stage(prices2)
            check("(2) 統一正本が空: alertsが1件(stage Y)で返る(OKに倒さない)",
                  len(result2) == 1 and result2[0].startswith("stage Y"), f"result={result2}")
            check("(2) 統一正本が空: prices.jsonは1バイトも変わらない", prices2.read_bytes() == raw_before)
            missing = td / "no_such_smart.db"
            use_smart(missing)
            result2b = stage(prices2)
            check("(2) 統一正本が不在: alertsが1件・prices.json不変・空DBを作らない",
                  len(result2b) == 1 and prices2.read_bytes() == raw_before and not missing.exists(),
                  f"result={result2b} created={missing.exists()}")

            # ---- (4) x.5 の丸め ----
            smart4 = td / "smart4.db"
            make_smart(smart4, [
                ("CEA", "2025-05-01", 50.00, 1, 0),
                ("CEA", "2025-05-02", 50.01, 1, 0),           # 平均 50.005 -> half-up 50.01
                ("KAU25", "2025-05-01", 10000, 1, 0),
                ("KAU25", "2025-05-02", 10001, 1, 0),         # 平均 10000.5 -> half-up 10001
            ])
            use_smart(smart4)
            prices4 = td / "prices4.json"
            write_prices(prices4, stale_prices())
            result4 = stage(prices4)
            got = json.loads(prices4.read_text(encoding="utf-8"))
            check("(4) x.5: 中国 50.005 -> 50.01 / 韓国 10000.5 -> 10001(half-up)",
                  result4 == [] and got["china_cny"][0]["avg_price"] == 50.01
                  and got["korea_krw"][0]["avg_price"] == 10001.0,
                  f"cn={got['china_cny'][0]['avg_price']} kr={got['korea_krw'][0]['avg_price']}")
            # 対照: 別の素朴な作りなら違う答えになる=このケースは区別できる。
            #   韓国: Pythonのround()は偶数丸め(10000) / 中国: SQLiteのAVG(浮動小数の和)を直接丸めると 50.00
            con = sqlite3.connect(smart4)
            naive_cn = con.execute("SELECT AVG(close_price) FROM ets_daily WHERE market='CEA'").fetchone()[0]
            con.close()
            from decimal import Decimal, ROUND_HALF_UP
            naive_cn_rounded = float(Decimal(str(naive_cn)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            check("(4) 対照: 偶数丸め(10000)・SQLite AVGの直接丸め(50.0)は別の答え=half-up・厳密平均と区別できる",
                  round(10000.5) == 10000 and naive_cn_rounded == 50.0,
                  f"round(10000.5)={round(10000.5)} naive_avg={naive_cn!r}->{naive_cn_rounded}")
    finally:
        if saved_env is None:
            os.environ.pop("ETS_LOCAL_PATHS", None)
        else:
            os.environ["ETS_LOCAL_PATHS"] = saved_env
    check("(復元) ETS_LOCAL_PATHSが元の状態に戻っている", os.environ.get("ETS_LOCAL_PATHS") == saved_env)

    # ---- 列挙: Yがdocstring・表示ラベル2か所・mainに載っている ----
    src = MODULE_PATH.read_text(encoding="utf-8")
    main_src = src[src.index("def main():"):]
    check("(列挙) docstringのstage一覧にY", "  Y update_yearly_prices.py" in (m.__doc__ or ""))
    check("(列挙) 表示ラベル2か所にY", "P 価格異常・Y 年次価格" in src and "A/B/C/D/E/P/Y/J/K/M/N" in src)
    check("(列挙) main()のH ok直後に record(\"Y\", ...) が在る(Hより後・Jより前)",
          main_src.index('stage_status["H"] = "ok"') < main_src.index('record("Y", stage_yearly_prices())')
          < main_src.index('record("J"'))

    print(f"\n=== {'ALL PASS' if fails == 0 else f'{fails} FAIL(S)'} "
          f"(4ケース+列挙・対象=stage_yearly_prices()/update_yearly_prices.py・非対象=main()全体の実走) ===")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(run())

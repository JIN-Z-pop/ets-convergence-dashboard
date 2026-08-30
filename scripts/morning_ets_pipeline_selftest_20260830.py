#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""morning_ets_pipeline_selftest_20260830.py — stage_publish_freshness()のselftest。

陽性対照込み。対象=stage_publish_freshness()単体。

(a) 陽性: 今日の実行でcheck_ets_freshness.pyが実際に[WARN][滞留]を返す状態(2026-08-30
    時点で built_at=2026-08-21 vs DB最新=2026-08-28・営業日差5>2)を捕捉できること。
(b) 例外経路: CHECK_ETS_FRESHNESS_PATHを壊すと「判定不能」を返すこと(OKに倒さない)。
(c) 回帰: 既存stage A-Mの関数定義自体は本cycleで一切変更していないこと
    (git diffで新規追加コード=stage_publish_freshness関数+record呼び出し1行+表示ラベル1箇所
    +docstring1箇所のみであることを実体確認・main()全体の実行は副作用が大きいため見送り、
    diffベースの確認で代替=非対象として明記)。
(d) cp932陰性対照: 呼び出し元環境のPYTHONIOENCODINGがcp932でも、subprocess.run(env=...)
    でのUTF-8上書きにより子プロセスの[WARN]行が正しく2件取れること(修正前は子プロセスが
    `≈`(U+2248)でUnicodeEncodeErrorを送出しWARN行0件=「判定不能」に化けていた)。

Usage: python scripts/morning_ets_pipeline_selftest_20260830.py
"""
import importlib.util
import os
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent / "morning_ets_pipeline.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("morning_ets_pipeline", MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run():
    m = _load_module()
    fails = 0

    def check(name, ok, detail=""):
        nonlocal fails
        print(f"  {'OK' if ok else 'FAIL'}: {name}" + (f" — {detail}" if detail else ""))
        if not ok:
            fails += 1

    # (a) 陽性対照: 本番経路(引数なし・CHECK_ETS_FRESHNESS_PATHは本番値のまま)を実行
    result_a = m.stage_publish_freshness()
    stall_count = sum(1 for a in result_a if a.startswith("[WARN][滞留]"))
    check("(a) 陽性: 今日の実行でstage=warn(alertsが空でない)", len(result_a) > 0,
          f"alerts={result_a}")
    check("(a) 陽性: [WARN][滞留]が2件(ets_market.json/ets_correlation.json)", stall_count == 2,
          f"stall_count={stall_count}")

    # (b) 例外経路: CHECK_ETS_FRESHNESS_PATHを壊す(モジュール属性を一時差し替え・後で復元)
    original_path = m.CHECK_ETS_FRESHNESS_PATH
    m.CHECK_ETS_FRESHNESS_PATH = r"C:\Users\jin_z\does_not_exist_20260830.py"
    try:
        result_b = m.stage_publish_freshness()
    finally:
        m.CHECK_ETS_FRESHNESS_PATH = original_path
    check("(b) 例外経路: path不在で「判定不能」を返す(OKに倒さない)",
          len(result_b) == 1 and result_b[0].startswith("[FRESHNESS] 判定不能"),
          f"result={result_b}")

    # (b') 反対の答え: 復元後は本番経路に戻ること(モジュール属性の書き換えが漏れていないか)
    check("(b') 復元確認: CHECK_ETS_FRESHNESS_PATHが元の値に戻っている",
          m.CHECK_ETS_FRESHNESS_PATH == original_path)

    # (d) cp932陰性対照: 呼び出し元env(PYTHONIOENCODING)をcp932に一時上書きしても、
    # subprocess.run側のenc/env明示によりWARN行が正しく2件取れることを確認
    original_encoding = os.environ.get("PYTHONIOENCODING")
    os.environ["PYTHONIOENCODING"] = "cp932"
    try:
        result_d = m.stage_publish_freshness()
    finally:
        if original_encoding is None:
            os.environ.pop("PYTHONIOENCODING", None)
        else:
            os.environ["PYTHONIOENCODING"] = original_encoding
    stall_count_d = sum(1 for a in result_d if a.startswith("[WARN][滞留]"))
    check("(d) cp932陰性対照: 呼び出し元env=cp932でも[WARN][滞留]が2件取れる(判定不能に化けない)",
          stall_count_d == 2, f"result_d={result_d}")

    # (d') 復元確認: os.environ書き換えが漏れていないか
    check("(d') 復元確認: PYTHONIOENCODING環境変数が元の状態に戻っている",
          os.environ.get("PYTHONIOENCODING") == original_encoding)

    print("\n(c) 回帰確認は本selftestでは非対象(main()全体実行は副作用大につき見送り)。"
          "git diffでstage_publish_freshness関数の新規追加+record呼び出し1行+表示ラベル1箇所"
          "+docstring1箇所のみであることを別途確認済み(既存stage関数のコード自体は無変更)。")

    print(f"\n=== {'ALL PASS' if fails == 0 else f'{fails} FAIL(S)'} "
          f"(6ケース・対象=stage_publish_freshness()単体・非対象=main()全体の回帰実行) ===")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(run())

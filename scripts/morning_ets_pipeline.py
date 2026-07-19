#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""morning_ets_pipeline.py — ETS朝ルーティン統合パイプライン(P3, 実装C拡張 強化案1-3)。

家内発注 2026-07-19 実装(経緯・担当=家内DD台帳2026-07-19参照)。

毎朝の収集(china/korea-ets-mcp内スクリプトによるスマートDB還流=本パイプライン範囲外=既存のまま)
の後に実行し、統一正本まで自動で届かせる。朝の恒久ルーティンから1コマンドで呼ばれる前提の
統合パイプライン。実行順:

  1. fetch_eu_ets.py → sync_eua_to_gods.py  (EU-ETS当日分取得+gods_eye.db反映。
     fetch失敗時はWARN継続=GXと同型の耐障害設計)
  2. fetch_gx_ets.py --date <today>  (GX-ETS当日分取得。金曜限定運用等の運用日でなくてもno_trade
     記録として毎日実行して問題ない=1回のPDF fetchのみで軽量。実行自体を毎日行うことで
     取引日を後から気付く事故を防ぐ=「金曜限定だから月に数回でいい」という間引き設計は
     やらない。設計判断 2026-07-19)
  3. build_ets_market_smart.py  (統一正本再構築+ets_monthly/ets_yearly view再定義。冪等・
     全消去再構築のため incremental化のコード変更は不要=既存のまま毎朝実行するだけで安全)
  4. ギャップ自動検知: market_holidays_2026.json突合
     - CEA/CCER/KAU/EUAは「無取引=異常」対象(休日でないのに最新日付が古い→gap_alert)
     - GXは「無取引=既定」(2025年度は11-12月毎週金曜限定運用)のため対象外。
       GXについては fetch自体が成功したか(ets_sync_log直近行のstatus)のみ確認する。
  4. 結果を ets_sync_log に集約記録。

Usage: python scripts/morning_ets_pipeline.py [--date YYYY-MM-DD]  (省略時=今日)
"""
import argparse
import json
import subprocess
import sqlite3
import sys
from datetime import datetime, timedelta

ROOT = r"C:\Users\jin_z\Desktop\ets-convergence-dashboard"
SMART = r"C:\Users\jin_z\.claude\databases\ets_market_smart.db"
HOLIDAYS_PATH = r"C:\Users\jin_z\market_holidays_2026.json"

# gap検知対象(GXを除く)。market値は ets_market_meta 準拠。holiday_keyはmarket_holidays_2026.jsonのtopキー。
GAP_CHECK_MARKETS = [
    ("CEA", "china"),
    ("CCER", "china"),
    ("KAU", "korea"),
    ("EUA", "eu_ets"),
]


def run(cmd):
    print(f"[RUN] {' '.join(cmd)}")
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print(p.stdout)
    if p.returncode != 0:
        print(p.stderr, file=sys.stderr)
    return p.returncode == 0


def load_holidays():
    with open(HOLIDAYS_PATH, encoding="utf-8") as f:
        return json.load(f)


def is_holiday(holidays, key, iso_date):
    dt = datetime.strptime(iso_date, "%Y-%m-%d")
    if dt.weekday() >= 5:  # Sat/Sun
        return True
    for c in holidays.get(key, {}).get("closures", []):
        if "date" in c and c["date"] == iso_date:
            return True
        if "range" in c and c["range"][0] <= iso_date <= c["range"][1]:
            return True
    return False


def check_gaps(target_date):
    holidays = load_holidays()
    conn = sqlite3.connect(SMART)
    alerts = []
    for market, holiday_key in GAP_CHECK_MARKETS:
        if is_holiday(holidays, holiday_key, target_date):
            continue
        if market == "KAU":
            # KAUはvintage別market値(KAU15〜KAU30)で格納されるため厳密一致では常にNoneになる。
            # 前方一致で系列全体のMAXを取り、現行vintageの最新日付を捕捉する(2026-07-20 gap_alert誤検知修正)。
            row = conn.execute(
                "SELECT MAX(date) FROM ets_daily WHERE market LIKE 'KAU%'"
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT MAX(date) FROM ets_daily WHERE market=?", (market,)
            ).fetchone()
        latest = row[0] if row else None
        if latest is None or latest < target_date:
            alerts.append(f"{market}: latest={latest} target={target_date} (非休日なのに未更新)")
    conn.close()
    return alerts


def log_pipeline_run(status, gap_alert):
    conn = sqlite3.connect(SMART)
    conn.execute(
        "INSERT INTO ets_sync_log (run_at,market,rows_inserted,rows_skipped,gap_alert,status) VALUES (?,?,?,?,?,?)",
        (datetime.now().isoformat(), "PIPELINE", 0, 0, gap_alert, status),
    )
    conn.commit()
    conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (省略時=今日)")
    ap.add_argument("--force", action="store_true", help="同日ガードを無視して強制再実行")
    args = ap.parse_args()
    target_date = args.date or datetime.now().strftime("%Y-%m-%d")

    # 同日ガード: 複数pane起床がそれぞれ本パイプラインを叩くと同一収集が重複する
    # (2026-07-19 同日8回重複の実測=葉山)。当日完走済み(OK/ALERT)ならskip。FAILは再実行を許す。
    if not args.force:
        today = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(SMART)
        done = conn.execute(
            "SELECT COUNT(*) FROM ets_sync_log"
            " WHERE market='PIPELINE' AND status IN ('OK','ALERT') AND substr(run_at,1,10)=?",
            (today,),
        ).fetchone()[0]
        conn.close()
        if done:
            print(f"[SKIP] 本日({today})のPIPELINEは既に{done}回完走済み。重複実行を回避します(--forceで強制再実行)。")
            return

    ok_eu_fetch = run([sys.executable, "scripts/fetch_eu_ets.py"])
    if not ok_eu_fetch:
        print("[WARN] fetch_eu_ets.py failed (yfinance網断・休場等の可能性。パイプライン続行)")
    else:
        ok_eu_sync = run([sys.executable, "scripts/sync_eua_to_gods.py"])
        if not ok_eu_sync:
            print("[WARN] sync_eua_to_gods.py failed (安全ガードabort等の可能性。パイプライン続行)")

    ok_gx = run([sys.executable, "scripts/fetch_gx_ets.py", "--date", target_date])
    if not ok_gx:
        # 当日分が未公表(まだ日報が出ていない等)の可能性もあるため、失敗しても後続は続行する。
        print(f"[WARN] fetch_gx_ets.py failed for {target_date} (日報未公表の可能性。パイプライン続行)")

    ok_build = run([sys.executable, "scripts/build_ets_market_smart.py"])
    if not ok_build:
        log_pipeline_run("FAIL(build)", None)
        print("[ERROR] build_ets_market_smart.py failed. Aborting gap check.", file=sys.stderr)
        sys.exit(1)

    alerts = check_gaps(target_date)
    gap_alert = "; ".join(alerts) if alerts else None
    status = "ALERT" if alerts else "OK"
    log_pipeline_run(status, gap_alert)

    print(f"=== morning_ets_pipeline: {status} ===")
    if alerts:
        print("[GAP ALERTS]")
        for a in alerts:
            print(f"  - {a}")
    else:
        print("gap check: no anomaly (CEA/CCER/KAU/EUA vs market_holidays_2026.json)")
    print("GX: no_trade=既定のためgap検知対象外。fetch実行結果は上記[RUN]出力を参照。")


if __name__ == "__main__":
    main()

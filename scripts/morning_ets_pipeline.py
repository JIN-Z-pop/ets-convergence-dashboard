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
KOREA = r"C:\Users\jin_z\.claude\databases\korea_ets_smart.db"
HOLIDAYS_PATH = r"C:\Users\jin_z\market_holidays_2026.json"

# gap検知対象(GXを除く)。market値は ets_market_meta 準拠。holiday_keyはmarket_holidays_2026.jsonのtopキー。
GAP_CHECK_MARKETS = [
    ("CEA", "china"),
    ("CCER", "china"),
    ("KAU", "korea"),
    ("EUA", "eu_ets"),
]

# 既知の発表ラグ許容(営業日単位、市場別)。0=前営業日必須(緩和なし)。
# 実測根拠(ets_sync_log PIPELINE ALERT履歴, 2026-07-19〜2026-08-07): CEA(carbonmarket.cn)と
# EUA(yfinance)は月に数回、ソース側の発表そのものが1営業日遅れ、次回実行で自己解消するパターンを
# 繰り返す(07-22/07-30/08-01/08-02=CEA、08-04=EUA。実行順序は全件で正常=china/koreaコレクター実行後に
# build_ets_market_smart.pyが走っていることを確認済み。原因はソース側発表タイミングであり収集障害ではない)。
# CCER/KAUには同型の実績なし=0のまま維持(実績のない市場まで一律に緩めると本当の障害検知が遅れるため)。
# 緩和は check_gaps()の「直近1点」判定のみに限定。真の複数日gapは check_recent_coverage()のF19 60日窓が
# 別軸(許容日数の影響を受けない)で捕捉するため、検知能力の後退にはならない。
GAP_LAG_TOLERANCE = {"CEA": 1, "CCER": 0, "KAU": 0, "EUA": 1}

# F19是正(oni_ets_t6, 2026-07-20): 直近被覆率検査対象(GXは特定日限定運用のため対象外=既存のgap検知
# 除外方針と同じ)。window_daysは「最近の穴」だけを拾う設計 — CEA等の既に原因調査・分類済みの
# 大きな historical gap(季節性・発行前等)を毎朝再アラートしてノイズ化させないため、
# 全履歴走査ではなく直近windowのみ見る。
COVERAGE_CHECK_MARKETS = [
    ("CEA", "china"),
    ("CCER", "china"),
    ("EUA", "eu_ets"),
    ("KAU", "korea"),
]
COVERAGE_WINDOW_DAYS = 60
KOREA_RECONCILE_MONTHS = 18
KOREA_RECONCILE_TOLERANCE = 1.0


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


def most_recent_business_day(holidays, key, target_date):
    """F11是正(oni_ets_t6 D8, 2026-07-20): target_date自体ではなく、その前営業日を
    market別休日カレンダーで逆算して返す。

    旧ロジックの欠陥: `latest < target_date` は target_date=当日が非休日である限り
    ほぼ常に真になる(当日分の終値は市場close後にしか存在しないため、朝パイプライン実行時点
    では原理的にまだ無い=毎朝100%誤検知していた可能性)。本関数は「前営業日までは来ているべき」
    という現実的な期待値を市場別に算出する(当日分の有無は問わない=前進的に厳しすぎない)。
    """
    dt = datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=1)
    while is_holiday(holidays, key, dt.strftime("%Y-%m-%d")):
        dt -= timedelta(days=1)
    return dt.strftime("%Y-%m-%d")


def check_gaps(target_date):
    holidays = load_holidays()
    conn = sqlite3.connect(SMART)
    alerts = []
    for market, holiday_key in GAP_CHECK_MARKETS:
        expected_latest = most_recent_business_day(holidays, holiday_key, target_date)
        for _ in range(GAP_LAG_TOLERANCE.get(market, 0)):
            expected_latest = most_recent_business_day(holidays, holiday_key, expected_latest)
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
        if latest is None or latest < expected_latest:
            tol = GAP_LAG_TOLERANCE.get(market, 0)
            tol_note = f",許容{tol}営業日込み" if tol else ""
            alerts.append(
                f"{market}: latest={latest} expected(直近営業日{tol_note})={expected_latest} target={target_date} (許容超過で未到達)"
            )
    conn.close()
    return alerts


def check_recent_coverage(target_date, window_days=COVERAGE_WINDOW_DAYS):
    """F19是正(oni_ets_t6, 2026-07-20): 直近window内の「行そのものが無い」型の穴を検出。

    check_gaps()は最新1点の鮮度のみ見るため、直近window内の途中(例: 収集が1日だけ飛んだ)を
    見逃す。既存の棚卸し手法(全市場営業日被覆率走査)を移植し、非休日なのに
    行が無い日を市場別休日カレンダーで判定して列挙する。CEA等の既に原因調査・分類済みの
    大きなhistorical gapはwindow外(60日超前)のため対象外=毎朝の再アラート化を回避。
    """
    holidays = load_holidays()
    window_start = (datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=window_days)).strftime("%Y-%m-%d")
    conn = sqlite3.connect(SMART)
    alerts = []
    for market, holiday_key in COVERAGE_CHECK_MARKETS:
        if market == "KAU":
            # KAUはvintage別market値(KAU15〜KAU30)で格納されるため、check_gaps()と同じ理由で
            # 前方一致+DISTINCT dateにより系列全体の営業日カバレッジを見る(2026-07-21 KAU25統一DB側
            # coverage未対応=祝日07-17を個別スクリプト側でのみ検知していた統一性ギャップの是正)。
            rows = conn.execute(
                "SELECT DISTINCT date FROM ets_daily WHERE market LIKE 'KAU%' AND date>=? ORDER BY date", (window_start,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT date FROM ets_daily WHERE market=? AND date>=? ORDER BY date", (market, window_start)
            ).fetchall()
        have = {r[0] for r in rows}
        missing = []
        dt = datetime.strptime(window_start, "%Y-%m-%d")
        end = datetime.strptime(target_date, "%Y-%m-%d")
        while dt < end:
            iso = dt.strftime("%Y-%m-%d")
            if iso not in have and not is_holiday(holidays, holiday_key, iso):
                missing.append(iso)
            dt += timedelta(days=1)
        if missing:
            alerts.append(
                f"{market}: 直近{window_days}日中 非休日欠落{len(missing)}件 {missing[:5]}{'...' if len(missing) > 5 else ''}"
            )
    conn.close()
    return alerts


def check_korea_monthly_reconciliation(months=KOREA_RECONCILE_MONTHS, tolerance=KOREA_RECONCILE_TOLERANCE):
    """F19是正(oni_ets_t6, 2026-07-20): 韓国一次公式月次集計(korea_ets_smart.db kets_market_monthly)
    と統一正本(ets_daily KAU系SUM(volume))の月次突合ゲート。

    build_ets_market_smart.pyのコメントに「非突合(federation参照のまま)」と明記されている通り、
    buildは意図的にこの一次公式値と接合していない(korea側は別系統のvintage別market値で保持する
    設計のため)。本関数はbuildを変更せず、独立の物差しとして月次量が乖離していないかを検算する
    後付けgate(蒼悟のT5cov.py手法を移植・直近18ヶ月・許容差1(浮動小数点誤差吸収))。
    """
    korea = sqlite3.connect(f"file:{KOREA}?mode=ro", uri=True)
    smart = sqlite3.connect(f"file:{SMART}?mode=ro", uri=True)
    rows = korea.execute(
        "SELECT year, month, kau_exchange_vol FROM kets_market_monthly "
        "WHERE kau_exchange_vol IS NOT NULL ORDER BY year, month"
    ).fetchall()
    alerts = []
    for y, m, official_vol in rows[-months:]:
        prefix = f"{y:04d}-{m:02d}"
        daily_sum = smart.execute(
            "SELECT SUM(volume) FROM ets_daily WHERE market LIKE 'KAU%' AND substr(date,1,7)=?", (prefix,)
        ).fetchone()[0] or 0
        diff = (official_vol or 0) - daily_sum
        if abs(diff) >= tolerance:
            alerts.append(f"KAU月次突合: {prefix} 公式={official_vol:.0f} 正本SUM={daily_sum:.0f} 差分={diff:.0f}")
    korea.close()
    smart.close()
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
    coverage_alerts = check_recent_coverage(target_date)
    korea_alerts = check_korea_monthly_reconciliation()
    all_alerts = alerts + coverage_alerts + korea_alerts
    gap_alert = "; ".join(all_alerts) if all_alerts else None
    status = "ALERT" if all_alerts else "OK"
    log_pipeline_run(status, gap_alert)

    print(f"=== morning_ets_pipeline: {status} ===")
    if alerts:
        print("[GAP ALERTS] (直近営業日鮮度)")
        for a in alerts:
            print(f"  - {a}")
    else:
        print("gap check: no anomaly (CEA/CCER/KAU/EUA vs market_holidays_2026.json)")
    if coverage_alerts:
        print(f"[COVERAGE ALERTS] (直近{COVERAGE_WINDOW_DAYS}日内の欠落, F19)")
        for a in coverage_alerts:
            print(f"  - {a}")
    else:
        markets_label = "/".join(m for m, _ in COVERAGE_CHECK_MARKETS)
        print(f"coverage check: no anomaly (直近{COVERAGE_WINDOW_DAYS}日, {markets_label}, F19)")
    if korea_alerts:
        print("[KOREA RECONCILE ALERTS] (F19)")
        for a in korea_alerts:
            print(f"  - {a}")
    else:
        print(f"korea reconcile check: no anomaly (直近{KOREA_RECONCILE_MONTHS}ヶ月, F19)")
    print("GX: no_trade=既定のためgap検知対象外。fetch実行結果は上記[RUN]出力を参照。")


if __name__ == "__main__":
    main()

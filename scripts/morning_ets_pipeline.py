#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""morning_ets_pipeline.py — ETS朝ルーティン統合パイプライン。

初版実装 2026-07-19。
P1+P2+P4統合 2026-08-23実装(設計=`ets_morning_unify_surgery_spec_20260823.md` v0.7
sha256[:12]=e3345225de51)。

毎朝の収集〜統一正本〜配信〜監査を1本のpipelineに統合。stage構成(この順で凍結・§2X-1):
  A cea_carbonmarket_collector.py (WARN継続)      B ccer_daily_data_collector.py (WARN継続)
  C korea fetch_krx_ets.py (絶対パス呼び・移設せず WARN継続)
  D carbon_gap_check.py (repo層gap検査・READ-ONLY・alert化継続)
  E sync_smart_market.py (exit 0=OK/1=alert/2=凍結flag=INFO扱いでskip)
  F fetch_eu_ets.py→sync_eua_to_gods.py (既存・WARN継続)
  G fetch_gx_ets.py --date + GX coverage自動backfill (既存・WARN継続)
  H build_ets_market_smart.py (既存・FAILでabort)
  I check_gaps/check_recent_coverage/korea_reconcile (既存smart層検査・alert集約)
  J china/korea docs/index.html再生成+鮮度自己検査 (新設)
  K 監査器 ets_db_audit.py (ERROR>0=alert)
  M 着地確認 3repoの未commit/未push検知 (検知のみ・commit/pushはしない。2026-08-28新設)
  L 結果集約→ets_sync_log(STAGES要約・§2X-5)+alertファイル書出(§2h')

同日ガード(既存流用・変更なし): 当日PIPELINE行がOK/ALERTならskip(--forceで強制)。

🔴S7本番切替時のschtasks登録コマンド形の記録のみ(§2X-6・登録自体はS7実施・本日は未登録):
  タスク名 ETS_MorningPipeline / DAILY 04:50 JST
  cmd /c cd /d "C:\\Users\\jin_z\\Desktop\\ets-convergence-dashboard" && "<python実体フルパス>" ^
    "C:\\Users\\jin_z\\Desktop\\ets-convergence-dashboard\\scripts\\morning_ets_pipeline.py" ^
    >> "C:\\Users\\jin_z\\Desktop\\ets-convergence-dashboard\\logs\\morning_pipeline.log" 2>&1
  前提: logs\\ ディレクトリの存在(S7①'で機械に依らず先に作成・mkdir自体は本pipeline冒頭にも
  安全のため実装済み=二重防御)。既存 CarbonMarket_AnomalyDetect(7:30/12:00)・
  ClaudeAutoWake-Morning(05:00)は触らない。

Usage: python scripts/morning_ets_pipeline.py [--date YYYY-MM-DD]  (省略時=今日)
"""
import argparse
import json
import os
import re
import subprocess
import sqlite3
import sys
from datetime import datetime, timedelta

ROOT = r"C:\Users\jin_z\Desktop\ets-convergence-dashboard"
GX_COVERAGE_MONTHS_BACK = 3  # 直近~90日相当をカバー(他市場のF19 60日窓より広めの安全マージン)
SMART = r"C:\Users\jin_z\.claude\databases\ets_market_smart.db"
KOREA = r"C:\Users\jin_z\.claude\databases\korea_ets_smart.db"
HOLIDAYS_PATH = r"C:\Users\jin_z\market_holidays_2026.json"

# P1+P2+P4統合(ets_morning_unify_surgery_spec_20260823.md v0.7 sha=e3345225de51)
LOGS_DIR = os.path.join(ROOT, "logs")
ALERT_PATH = os.path.join(LOGS_DIR, "morning_alert_latest.txt")
KOREA_FETCH_SCRIPT = r"C:\Users\jin_z\Desktop\korea-ets-mcp\scripts\fetch_krx_ets.py"
AUDIT_SCRIPT = r"C:\Users\jin_z\Desktop\neural-core\data\tests\ets_db_audit.py"
CHINA_MCP_DIR = r"C:\Users\jin_z\Desktop\china-ets-mcp"
KOREA_MCP_DIR = r"C:\Users\jin_z\Desktop\korea-ets-mcp"
CHINA_HTML = os.path.join(CHINA_MCP_DIR, "docs", "index.html")
KOREA_HTML = os.path.join(KOREA_MCP_DIR, "docs", "index.html")

# stage M(着地確認)の対象。公開branch名はrepoごとに異なるため定数に持たず実測解決する。
# 第4要素=(DBの相対パス, 最新日クエリ, 未着地日数クエリ)。
# 追跡下のSQLiteは読み書きの有無に関わらず実行のたびにバイナリが変わる
# (実測2026-08-28: サイズ同一・差分0行のままdirty化)ため、バイナリ差分では見ない。
# DBは「commit済み版に載っていない営業日が何日分あるか」で見る。
GIT_REPOS = [
    ("convergence", ROOT, None),
    ("china", CHINA_MCP_DIR, ("data/china_ets.db", "SELECT MAX(date) FROM cea_daily",
                              "SELECT COUNT(*) FROM cea_daily WHERE date > ?")),
    ("korea", KOREA_MCP_DIR, ("data/korea_ets.db", "SELECT MAX(date) FROM kets_kau_ohlcv",
                              "SELECT COUNT(DISTINCT date) FROM kets_kau_ohlcv WHERE date > ?")),
]
# 未着地が何営業日分たまったらalertにするか。1=当日取得分のみ未着地(pipelineはcommitしない
# ため機械実行の時点では必ずこの状態=正常)。2以上=前日以前の分も着地しておらず放置されている。
LANDING_LAG_ALERT_DAYS = 2

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


def run_capture(cmd, cwd=None):
    """run()同様だがreturncodeと標準出力を両方返す(exit値を多値判定するstage用)。"""
    print(f"[RUN] {' '.join(cmd)}")
    p = subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True)
    print(p.stdout)
    if p.returncode != 0:
        print(p.stderr, file=sys.stderr)
    return p.returncode, p.stdout


def stage_collectors():
    """stage A/B: CEA/CCER collector(移設先=scripts/相対)。失敗はWARN継続(各stage独立試行)。

    collector実行失敗=**異常**(データが1件も入らない)につきalert化する(常態/異常軸・
    approved 2026-08-23。F/G/E-rc2の「常態」とは対称的にA/B/C/J/Kは
    「実行できないこと自体が普段起きてはいけない異常」——alert化しないと「実行が壊れて
    いるのに記録がOKと言う」= 本手術が潰そうとしている問題の裏返しになる)。
    """
    alerts = []
    if not run([sys.executable, "scripts/cea_carbonmarket_collector.py"]):
        alerts.append("stage A(CEA collector) failed - WARN継続")
    if not run([sys.executable, "scripts/ccer_daily_data_collector.py"]):
        alerts.append("stage B(CCER collector) failed - WARN継続")
    return alerts


def stage_korea_fetch():
    """stage C: korea fetch_krx_ets.py(絶対パス呼び・移設しない=最小侵襲)。失敗はWARN継続。
    A/Bと同型で異常扱い=alert化する(常態/異常軸)。
    """
    if not run([sys.executable, KOREA_FETCH_SCRIPT]):
        return ["stage C(korea fetch_krx_ets.py) failed - WARN継続"]
    return []


def _extract_result_line(output, prefix):
    for line in output.splitlines():
        if line.startswith(prefix):
            return line
    return None


def stage_gap_check():
    """stage D: carbon_gap_check.py(repo層gap検査・READ-ONLY)。exit!=0=alert収集して継続。"""
    rc, out = run_capture([sys.executable, "scripts/carbon_gap_check.py"])
    if rc == 0:
        return []
    line = _extract_result_line(out, "RESULT: ATTENTION")
    return [f"stage D(carbon_gap_check): {line or ('exit=%d' % rc)}"]


def stage_sync():
    """stage E: sync_smart_market.py。exit 3値を区別: 0=OK/1=alert/2=凍結flag=INFO扱いでskip
    (2=凍結flagは**意図的な運用状態=常態**につきalert化しない。常態/異常軸・approved 08-23)。
    """
    rc, out = run_capture([sys.executable, "scripts/sync_smart_market.py"])
    if rc == 2:
        print("[INFO] stage E(sync_smart_market.py) は凍結中(SYNC_FREEZE_oni_ets.flag)。alert化せずskip記録。")
        return []
    if rc == 1:
        line = _extract_result_line(out, "RESULT: FAIL")
        return [f"stage E(sync_smart_market): {line or 'exit=1'}"]
    return []


def run_in(cmd, cwd, pythonpath=None):
    """run()同様だがcwdを指定できる版(china/korea-ets-mcpはパッケージ相対import前提=cwd必須)。

    🔴S6サンドボックス検証で実発見(2026-08-23): cwd自体が存在しない場合
    subprocess.run()はreturncode!=0を返すのではなくOSError(Windows実測=NotADirectoryError)
    を送出し、try/exceptの無いこの関数を経由してpipeline全体をクラッシュさせる
    ("1市場/1機能の失敗が他を止めない"というstage J設計の前提=WARN継続を破壊する)。
    china/korea-ets-mcpディレクトリが将来移動/削除された場合も同型で全損しうるため、
    ここでOSErrorを捕捉しFalse(=呼び出し元でWARN継続)へ倒す。

    🔴S8初回機械実行で実発見(2026-08-25): 上記docstringの「cwd必須」は
    **cwdだけで足りる**という前提を含んでいたが実体は違った。両repoともパッケージは
    src/レイアウト(src/china_ets_mcp/)のため、cwdをrepo直下にしてもsrcはsys.pathに
    入らず ModuleNotFoundError で必ず失敗する(両方向対照で確認: PYTHONPATH無し=再現/
    src=解消)。結果stage Jが毎朝失敗し公開HTML 2本が停滞した。手順書(ANSの手紙)側には
    最初から `PYTHONPATH=src` が書かれており、pipeline統合時に落ちた=設計と実体の乖離
    envはWindowsで完全置換となるため os.environ を必ず継承する。
    """
    print(f"[RUN in {cwd}] {' '.join(cmd)}")
    env = None
    if pythonpath:
        env = {**os.environ, "PYTHONPATH": pythonpath}
        print(f"[RUN env] PYTHONPATH={pythonpath}")
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    except OSError as e:
        print(f"[WARN] cwd起動失敗(継続): {cwd}: {e}", file=sys.stderr)
        return False
    print(p.stdout)
    if p.returncode != 0:
        print(p.stderr, file=sys.stderr)
    return p.returncode == 0


def stage_html_refresh():
    """stage J(P4): china/korea docs/index.html再生成+鮮度自己検査(HTML内最新日付 vs DB max_date)。

    再生成コマンド自体の実行失敗もalert化する(常態/異常軸・approved 08-23: 本番でchina/
    korea-ets-mcpは在る前提=失敗は異常。今回のダミーパスは検証用の人為であって常態ではない)。
    """
    alerts = []
    if not run_in([sys.executable, "-m", "china_ets_mcp.cli"], CHINA_MCP_DIR,
                  pythonpath=os.path.join(CHINA_MCP_DIR, "src")):
        alerts.append("stage J(china html再生成) failed - WARN継続")
    if not run_in([sys.executable, "-m", "korea_ets_mcp.cli"], KOREA_MCP_DIR,
                  pythonpath=os.path.join(KOREA_MCP_DIR, "src")):
        alerts.append("stage J(korea html再生成) failed - WARN継続")
    alerts += check_html_freshness(
        "china", CHINA_HTML, SMART, "SELECT MAX(date) FROM ets_daily WHERE market IN ('CEA','CCER')"
    )
    alerts += check_html_freshness(
        "korea", KOREA_HTML, SMART, "SELECT MAX(date) FROM ets_daily WHERE market LIKE 'KAU%'"
    )
    return alerts


def _max_date_in_html(html_path):
    """生成HTML内に埋め込まれたJSONから 'date':'YYYY-MM-DD' 系の最大値を抽出する。

    テンプレート実装(dashboard.py)非依存の緩い抽出=正規表現(#127: 生成ロジックの
    正しさそのものは非対象、鮮度=最新日付が反映されているかのみを見る)。
    """
    if not os.path.exists(html_path):
        return None
    text = open(html_path, encoding="utf-8", errors="replace").read()
    dates = re.findall(r'"date"\s*:\s*"(\d{4}-\d{2}-\d{2})"', text)
    return max(dates) if dates else None


def check_html_freshness(label, html_path, db_path, query):
    html_max = _max_date_in_html(html_path)
    if html_max is None:
        return [f"{label} HTML鮮度検査: {html_path} に日付データが見当たらない(生成失敗の可能性)"]
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    row = conn.execute(query).fetchone()
    conn.close()
    db_max = row[0] if row else None
    if db_max is not None and html_max < db_max:
        return [f"{label} HTML鮮度検査: HTML内最新={html_max} < DB最新={db_max} (再生成漏れの可能性)"]
    return []


def stage_audit():
    """stage K(P3): ets_db_audit.py。ERROR>0(exit=1)=alert化して継続(異常)。"""
    rc, out = run_capture([sys.executable, AUDIT_SCRIPT])
    if rc == 0:
        return []
    line = _extract_result_line(out, "SUMMARY:")
    return [f"stage K(ets_db_audit): {line or ('exit=%d' % rc)}"]


def _git(args, cwd, raw=False):
    """git実行。(ok, stdout)を返す。git不在・タイムアウトも失敗として扱い例外を外へ出さない。

    raw=True は strip() を掛けない。status --porcelain は先頭2文字が状態列で
    1行目の先頭が空白になりうるため、strip()するとパスが1文字欠ける(実測で検出)。
    """
    try:
        p = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60)
        return p.returncode == 0, (p.stdout if raw else p.stdout.strip())
    except (OSError, subprocess.SubprocessError) as e:
        return False, str(e)


def _publish_branch(cwd):
    """公開branchを origin/HEAD から解決する。解決不能ならNone。

    main/master決め打ちを避けるための実測解決。実測(2026-08-28)で3リポジトリの
    公開branchは master / public / master と揃っておらず、決め打ちの差分コマンドは
    fatalで空を返す=「未pushが無い」と読み違える経路になる。
    """
    ok, out = _git(["symbolic-ref", "refs/remotes/origin/HEAD"], cwd)
    prefix = "refs/remotes/"
    if ok and out.startswith(prefix):
        return out[len(prefix):]
    return None


def _committed_db_max_date(repo, db_rel, query, ref="HEAD"):
    """commit済み版のDBから最新日を読む。取得不能ならNone(=判定不能)。

    公開されているのは作業ツリーではなくcommit済みの中身なので、
    「公開データが古いままか」はこの版を読まないと分からない。
    """
    tmp = os.path.join(LOGS_DIR, "_committed_db_tmp.sqlite")
    try:
        p = subprocess.run(["git", "show", f"{ref}:{db_rel}"], cwd=repo,
                           capture_output=True, timeout=120)
        if p.returncode != 0 or not p.stdout:
            return None
        with open(tmp, "wb") as f:
            f.write(p.stdout)
        conn = sqlite3.connect(f"file:{tmp}?mode=ro", uri=True)
        row = conn.execute(query).fetchone()
        conn.close()
        return row[0] if row else None
    except (OSError, subprocess.SubprocessError, sqlite3.Error):
        return None
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def _worktree_db_query(repo, db_rel, query, params=()):
    path = os.path.join(repo, db_rel.replace("/", os.sep))
    if not os.path.exists(path):
        return None
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        row = conn.execute(query, params).fetchone()
        conn.close()
        return row[0] if row else None
    except sqlite3.Error:
        return None


def stage_landing_check():
    """stage M: 成果物の着地(commit/push)確認。

    stage JはHTMLを再生成するが、再生成物が公開へ着地したかは従来どの検査も見て
    いなかった。pipelineがOKと宣言しても未commit/未pushのまま公開が止まりうる
    (実測2026-08-28: 機械完走の一方でprices.jsonは未commitのまま残っていた)。

    alertに上げるのは「放置」と「構造的異常」だけ。本pipelineはstage JでHTMLを再生成
    するがcommitはしないため、機械実行の時点では必ず未着地になる。これをそのまま
    alertにすると毎朝ALERTが立ち続け、本物の異常が埋もれる(実測2026-08-28: alert化
    した初版は通し実行でstatusをOKからALERTへ変えた)。よって当日分の未着地は
    INFOに留め、前日以前も着地していない場合にのみalertへ上げる。

    捕捉(alert) = 未pushのcommit(機械はcommitしないので存在すれば取りこぼし) /
           未着地が LANDING_LAG_ALERT_DAYS 営業日分以上たまっていること /
           gitリポジトリ不在・status失敗・公開branch解決不能・DB読取不能。
    捕捉(INFO のみ) = 未commitの追跡ファイル件数 / 当日分だけの未着地。
    非捕捉 = 公開サイトが実際に配信している内容(Pagesビルド結果) / untrackedファイル
           (意図的な非公開物と区別できないため数えない) / commit内容の妥当性 /
           DBのバイナリ差分(実行のたびに変わるためcommit漏れの指標にならない)。

    本stageは検知のみ。commitもpushも行わない(公開行為は人の判断に残す)。
    """
    alerts = []
    for label, repo, db_spec in GIT_REPOS:
        if not os.path.isdir(os.path.join(repo, ".git")):
            alerts.append(f"stage M({label}): gitリポジトリが見当たらない {repo}")
            continue
        ok, out = _git(["status", "--porcelain", "--untracked-files=no"], repo, raw=True)
        if not ok:
            alerts.append(f"stage M({label}): git status失敗 {out[:120]}")
            continue
        all_dirty = [ln[3:] for ln in out.splitlines() if ln.strip()]
        dirty_paths = [p for p in all_dirty if not p.endswith(".db")]
        dirty = dirty_paths
        db_skipped = len(all_dirty) - len(dirty_paths)
        branch = _publish_branch(repo)
        if branch is None:
            alerts.append(f"stage M({label}): 公開branchをorigin/HEADから解決できない"
                          f"(未push件数は判定不能=OKに倒さない)")
            unpushed = None
        else:
            ok2, out2 = _git(["log", f"{branch}..HEAD", "--oneline"], repo)
            if not ok2:
                alerts.append(f"stage M({label}): 未push件数の取得に失敗 {out2[:120]}")
                unpushed = None
            else:
                unpushed = len([ln for ln in out2.splitlines() if ln.strip()])
        if unpushed:
            alerts.append(f"stage M({label}): {branch}へ未pushのcommit{unpushed}件")

        db_note = ""
        if db_spec:
            db_rel, db_max_query, db_lag_query = db_spec
            committed = _committed_db_max_date(repo, db_rel, db_max_query)
            worktree = _worktree_db_query(repo, db_rel, db_max_query)
            if committed is None or worktree is None:
                alerts.append(f"stage M({label}): DB最新日を読めない"
                              f"(commit済={committed} 作業版={worktree}) = 判定不能")
                db_note = " / DB最新日=判定不能"
            elif committed < worktree:
                lag = _worktree_db_query(repo, db_rel, db_lag_query, (committed,))
                if lag is None:
                    alerts.append(f"stage M({label}): 未着地日数を数えられない = 判定不能")
                    db_note = " / DB未着地=判定不能"
                elif lag >= LANDING_LAG_ALERT_DAYS:
                    alerts.append(f"stage M({label}): 公開DBに未着地の日が{lag}営業日分 "
                                  f"(commit済={committed} < 作業版={worktree}) — 前日以前も未着地")
                    db_note = f" / DB未着地{lag}営業日分(commit済={committed})"
                else:
                    db_note = (f" / DB未着地{lag}営業日分=当日分のみ"
                               f"(commit済={committed} 作業版={worktree})")
            else:
                db_note = f" / DB最新日={committed}(一致)"

        print(f"[INFO ] LANDING       {label}: 未commit{len(dirty)}件 / "
              f"未push{'判定不能' if unpushed is None else str(unpushed) + '件'} "
              f"(公開branch={branch or '解決不能'}){db_note}"
              f"{f' / DBバイナリ差分{db_skipped}件は非対象' if db_skipped else ''}")
    return alerts


def write_alert_file(status, target_date, all_alerts):
    """stage L(§2h'): alertをファイルへ全置換書出(機械=書く/AIが読んで=送る、の機械側半分)。

    書出失敗はtry/exceptで包み継続(stdoutへ残す)。dir自体はpipeline冒頭で確保済み前提
    (mkdir失敗はそちらでFAILへ倒す=ここでは前提が満たされている想定)。
    """
    try:
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        lines = [f"{status} {target_date} {now}"]
        lines.extend(all_alerts)
        with open(ALERT_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"[ALERT-FILE] wrote {ALERT_PATH} ({len(all_alerts)} alert(s))")
    except OSError as e:
        print(f"[WARN] alertファイル書出失敗(継続): {e}", file=sys.stderr)


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
    後付けgate(既存手法を移植・直近18ヶ月・許容差1(浮動小数点誤差吸収))。
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


def check_and_backfill_gx_coverage(target_date, months_back=GX_COVERAGE_MONTHS_BACK):
    """GX-ETS coverage対象化(approved 2026-08-20「gap/coverage検知の対象化」)。

    背景: GXは他市場と違い「無取引=既定」(2025年度は11-12月毎週金曜限定運用)のため
    GAP_CHECK_MARKETS/COVERAGE_CHECK_MARKETSから意図的に除外されている。しかしこれは
    「実取引の有無」を問わない話であって、「日報PDFそのものが存在するのに記録が
    raw_gx_ets_daily(gods_eye.db)に無い」という別種の見逃しは検知できていなかった。
    実例(2026-08-20発見): 2026-08-17〜19の3営業日分のPDFは解決可能だったが記録が
    欠落していた。原因=毎日の実行が`--date <today>`単発のみで、「当日分が未公表→
    翌日以降にPDF が遅れて公開される」ケースの再取得(backfill)が組み込まれていなかった
    構造的な穴。

    設計: 他市場のような休日カレンダー突合ではなく、fetch_gx_ets.list_available_dates()
    が返す「PDFリンクが実在する日付集合」そのものを正とし、raw_gx_ets_dailyとの差分を
    missingとして検知する。検知したら該当日をfetch_gx_ets.py --dateで自動再取得し
    (CEA/CCER/KRXコレクターの「遡及で自動的に穴を塞ぐ」設計思想と揃える)、それでも
    埋まらない日だけをalertとして返す。当日(target_date)自体はまだ未公表の可能性が
    高いため対象外(通常のfetch_gx_ets.py --date実行側でカバー済み)。
    """
    this_dir = os.path.dirname(os.path.abspath(__file__))
    if this_dir not in sys.path:
        sys.path.insert(0, this_dir)
    from fetch_gx_ets import list_available_dates, yyyymmdd_to_iso, GODS_DB as GX_GODS

    url_map = list_available_dates(months_back=months_back)
    conn = sqlite3.connect(GX_GODS)
    have = {r[0] for r in conn.execute("SELECT date FROM raw_gx_ets_daily").fetchall()}
    conn.close()

    all_isos = {yyyymmdd_to_iso(ymd) for ymd in url_map}
    missing = sorted(iso for iso in all_isos if iso < target_date and iso not in have)
    if not missing:
        return []

    print(f"[GX-COVERAGE] 記録漏れ{len(missing)}件検知、自動backfillを試みます: {missing}")
    for iso in missing:
        run([sys.executable, "scripts/fetch_gx_ets.py", "--date", iso])

    conn = sqlite3.connect(GX_GODS)
    have_after = {r[0] for r in conn.execute("SELECT date FROM raw_gx_ets_daily").fetchall()}
    conn.close()
    still_missing = [d for d in missing if d not in have_after]
    if still_missing:
        return [f"GX coverage: 自動backfill後も記録漏れ残存 {still_missing}"]
    return []


def log_pipeline_run(status, gap_alert, stage_status=None):
    """§2X-5: 既存gap_alert列にSTAGES要約を後方互換で前置(旧None/alert列挙をそのまま包含)。

    罠B確認済み(実装前に事前調査): ets_sync_log.gap_alert列の読み手は
    tef_evaluate.py/weekly_mri_collect.py の2件のみヒットしたが、いずれも
    別システム側の同名 gap_alerts であり無関係。実際の読み手は別途2件確認済み
    (market='PIPELINE'限定+部分一致=前置で壊れない)のみ=実装してよい。
    """
    if stage_status:
        stages_str = " ".join(f"{k}={v}" for k, v in stage_status.items())
        prefix = f"STAGES: {stages_str}"
        gap_alert = f"{prefix} | ALERTS: {gap_alert}" if gap_alert else prefix
    conn = sqlite3.connect(SMART)
    conn.execute(
        "INSERT INTO ets_sync_log (run_at,market,rows_inserted,rows_skipped,gap_alert,status) VALUES (?,?,?,?,?,?)",
        (datetime.now().astimezone().isoformat(timespec="seconds"), "PIPELINE", 0, 0, gap_alert, status),
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
    # (2026-07-19 同日8回重複の実測)。当日完走済み(OK/ALERT)ならskip。FAILは再実行を許す。
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

    # 🔴 mkdir=pipeline冒頭(同日ガード直後・stage Aの前、v0.5是正)。通知経路の可用性は
    # 使うのは最後(stage L)でも確保は最初。mkdir失敗はtry/exceptで握り潰さずFAILへ倒す
    # (schtasks実行時のstdoutは誰も読まない=通知経路の喪失を「静かな継続」にしない)。
    os.makedirs(LOGS_DIR, exist_ok=True)

    stage_status = {}
    all_alerts = []

    def record(name, alerts, ok_label="ok", warn_label="warn"):
        stage_status[name] = warn_label if alerts else ok_label
        all_alerts.extend(alerts)

    record("A_B", stage_collectors())
    record("C", stage_korea_fetch())
    record("D", stage_gap_check())
    record("E", stage_sync())

    # F: yfinance網断/休場は常態的に起きうる失敗につきalert化しない(常態/異常軸・
    # approved 08-23。stage_statusのwarnはSTAGES要約に残るが
    # all_alertsには入れない=最終status判定に影響しない、という既存実装のまま維持する)。
    ok_eu_fetch = run([sys.executable, "scripts/fetch_eu_ets.py"])
    if not ok_eu_fetch:
        print("[WARN] fetch_eu_ets.py failed (yfinance網断・休場等の可能性。パイプライン続行)")
        stage_status["F"] = "warn"
    else:
        ok_eu_sync = run([sys.executable, "scripts/sync_eua_to_gods.py"])
        if not ok_eu_sync:
            print("[WARN] sync_eua_to_gods.py failed (安全ガードabort等の可能性。パイプライン続行)")
            stage_status["F"] = "warn"
        else:
            stage_status["F"] = "ok"

    # G: GX日報未公表は金曜限定運用下の平日の常態(F同様alert化しない・常態/異常軸)。
    # ただしbackfillしても記録漏れが残るケース(gx_coverage_alerts)は本物のデータ異常
    # なのでこちらはall_alertsへ入れる(下記I節)=同じstage内でも常態/異常は別に判定する。
    ok_gx = run([sys.executable, "scripts/fetch_gx_ets.py", "--date", target_date])
    if not ok_gx:
        # 当日分が未公表(まだ日報が出ていない等)の可能性もあるため、失敗しても後続は続行する。
        print(f"[WARN] fetch_gx_ets.py failed for {target_date} (日報未公表の可能性。パイプライン続行)")

    gx_coverage_alerts = check_and_backfill_gx_coverage(target_date)
    stage_status["G"] = "warn" if (not ok_gx or gx_coverage_alerts) else "ok"

    ok_build = run([sys.executable, "scripts/build_ets_market_smart.py"])
    if not ok_build:
        stage_status["H"] = "fail"
        log_pipeline_run("FAIL(build)", None, stage_status)
        write_alert_file("FAIL(build)", target_date, all_alerts + ["stage H(build_ets_market_smart) failed - abort"])
        print("[ERROR] build_ets_market_smart.py failed. Aborting gap check.", file=sys.stderr)
        sys.exit(1)
    stage_status["H"] = "ok"

    alerts = check_gaps(target_date)
    coverage_alerts = check_recent_coverage(target_date)
    korea_alerts = check_korea_monthly_reconciliation()
    stage_status["I"] = "warn" if (alerts or coverage_alerts or korea_alerts or gx_coverage_alerts) else "ok"
    all_alerts += alerts + coverage_alerts + korea_alerts + gx_coverage_alerts

    record("J", stage_html_refresh())
    record("K", stage_audit())
    record("M", stage_landing_check())

    # §2h「完遂」の再定義: J(HTML鮮度)/K(監査器)のalertもrecord()でall_alertsへ
    # 集約済みのため、ここで初めてstatus判定する時点で両方が反映されている=
    # 「配布した」でなく「監査器+鮮度検査PASS」をもってOKと言える(宣言と実体の一致)。
    gap_alert = "; ".join(all_alerts) if all_alerts else None
    status = "ALERT" if all_alerts else "OK"
    stage_status["L"] = "ok"
    log_pipeline_run(status, gap_alert, stage_status)
    write_alert_file(status, target_date, all_alerts)

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
    if gx_coverage_alerts:
        print("[GX COVERAGE ALERTS] (記録漏れ=PDFは存在するが取得できていない日、自動backfill後もなお残存)")
        for a in gx_coverage_alerts:
            print(f"  - {a}")
    else:
        print(f"GX coverage check: no anomaly (直近{GX_COVERAGE_MONTHS_BACK}ヶ月分, 記録漏れ0件/自動backfillで解消)。no_trade自体は既定のため対象外。")

    # stage A/B/C/D/E/J/K(P1+P2+P4統合分)のalertは record() でall_alertsへ集約済み。
    # 個別リストで再抽出はせず、既存4分類(alerts/coverage/korea/gx)に含まれない残りを表示する。
    new_stage_alerts = [a for a in all_alerts
                        if a not in alerts and a not in coverage_alerts
                        and a not in korea_alerts and a not in gx_coverage_alerts]
    if new_stage_alerts:
        print("[STAGE ALERTS] (A/B collector・C korea・D gap_check・E sync・J html鮮度・K audit)")
        for a in new_stage_alerts:
            print(f"  - {a}")
    else:
        print("stage A/B/C/D/E/J/K: no anomaly")
    print(f"STAGES summary: {' '.join(f'{k}={v}' for k, v in stage_status.items())}")
    print(f"[ALERT-FILE] {ALERT_PATH}")


if __name__ == "__main__":
    main()

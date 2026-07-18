#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_ets_market_smart.py — ETS一元化P1: 統一正本DB(ets_market_smart.db)構築スクリプト。

奏(editor) P1発注 2026-07-18夜(金博士様GO)。葉山(actor)実装。系譜=家内DD台帳2026-07-18(鬼検証是正/保全P0)参照。

既存ソースDB(china_ets_smart.db / korea_ets_smart.db / gods_eye.db)は読み取り専用(read-only URI接続)。
本スクリプトが書き込むのは ets_market_smart.db(新設・単一正本)のみ。

再構築可能(冪等): 実行の都度 ets_daily/ets_market_meta/ets_source を全消去して再構築する。
ets_correction/ets_sync_log は追記専用(履歴として蓄積・消さない)。

自己修復設計(2026-07-18夜 CCER 2024-01-22 regression教訓 — smart DBへの手動補正がrepo mirrorで
黙って巻き戻された事故 — の反省): ets_correction台帳に登録された補正は、生データ読み込み後に
毎回re-applyする。ソース側が将来再びregressionを起こしても、本スクリプト再実行で自己修復する。

Usage: python scripts/build_ets_market_smart.py   (ets-convergence-dashboardルートから)
"""
import sqlite3
from datetime import datetime

SMART = r"C:\Users\jin_z\.claude\databases\ets_market_smart.db"
CHINA = r"C:\Users\jin_z\.claude\databases\china_ets_smart.db"
KOREA = r"C:\Users\jin_z\.claude\databases\korea_ets_smart.db"
GODS = r"C:\Users\jin_z\.claude\databases\gods_eye.db"

DAILY_COLS = "market,date,open_price,high_price,low_price,close_price,currency,volume,amount,no_trade,source_id,fetched_at"
DAILY_PLACEHOLDERS = ",".join("?" * 12)

SOURCES = [
    (1, "CNEEEX (Shanghai Environment and Energy Exchange)", "https://overview.cneeex.com/qgtpfqjy/mrgk/",
     "web scrape (closed 2025-12)", "CEA原初出典。2025-12閉鎖"),
    (2, "carbonmarket.cn", "https://carbonmarket.cn/ets/cets/",
     "HTML table scrape (Table1掛牌+Table2大宗)", "CEA現行出典(2025-12-25〜)。china smartに出自列が無いため全CEA行をid2扱い(簡潔優先、遷移史はmeta.notesに記載)"),
    (3, "CCER Official (Beijing Green Exchange)", "https://www.ccer.com.cn/wcm/ccer/html/2502lshq/index.html",
     "JSON API (/wcm/ccer/data/2502lshq.json)", "CCER出典"),
    (4, "KRX (Korea Exchange)", None, "kets collector (ohlcv + daily_price)", "KAU/KCU/KOC全permit_type共通出典"),
    (5, "yfinance CO2.L (SparkChange Physical Carbon EUA ETC, EUR建て)", None,
     "yfinance Ticker.history(period='2y')", "EUA出典。列名price_usdは歴史的負債=実体EUR(2026-07-18鬼検証で確定)"),
    (6, "NASDAQ ICE_EUA1 Settle (EUR)", None, None, "未使用・P2予約"),
    (7, "JPXカーボン・クレジット市場日報", "https://www.jpx.co.jp/equities/carbon-credit/daily/index.html",
     "PDF fetch(索引/archivesページでURL解決→PDFテーブル抽出、銘柄コード5051000行のみ抽出)",
     "GX-ETS超過削減枠出典。設計=docs/gx_ets_acquisition_design_20260719.md、取得=scripts/fetch_gx_ets.py"),
]

MARKET_META = [
    # P1 market定義正文v1.1(奏裁定 2026-07-18 22:14, 蒼悟逆FB反映)確定: 9 family行
    ("CEA", "中国CEA(全国ETS)", "China-ETS", "上海環境能源交易所", "CNY", "2021-07-16",
     "全国碳配額。出典遷移: CNEEEX(〜2025-12)→carbonmarket.cn(2025-12-25〜)"),
    ("CCER", "中国CCER(自主削減)", "China-ETS", "北京緑色交易所", "CNY", "2024-01-22",
     "avg_price=0かつdaily_volume=0の日はno_trade=1(無取引日、127件)。2024-01-22は欠損補正済(ets_correction参照)"),
    ("KAU", "韓国KAU(K-ETS 排出権・vintage別)", "K-ETS", "KRX", "KRW", "2015-01-12",
     "vintage別market値(KAU15〜KAU30)。ohlcv系(2021-, OHLCV優先)+終値歴史(2015-)の2系統統合。重複2649件中不一致1件(KAU22 2023-07-10)はohlcv優先で採用・ets_sync_logに記録"),
    ("KCU", "韓国KCU(相殺クレジット)", "K-ETS", "KRX", "KRW", None,
     "vintage別market値(KCU15〜KCU26)。kets_market_daily_priceのみ出典(終値のみ、OHLCV無し)"),
    ("KOC", "韓国KOC(オフセットクレジット)", "K-ETS", "KRX", "KRW", None,
     "期間別market値(KOC, KOC20-22等)。kets_market_daily_priceのみ出典(終値のみ、OHLCV無し)"),
    ("i-KCU", "韓国i-KCU(国際相殺クレジット)", "K-ETS", "KRX", "KRW", None,
     "vintage別market値(i-KCU23〜26)。kets_market_daily_priceのみ出典(終値のみ、OHLCV無し)"),
    ("i-KOC", "韓国i-KOC(国際オフセットクレジット)", "K-ETS", "KRX", "KRW", None,
     "期間別market値(i-KOC21-26等)。kets_market_daily_priceのみ出典(終値のみ、OHLCV無し)"),
    ("EUA", "EU EUA(EU-ETS)", "EU-ETS", "SparkChange CO2.L ETC/ICE系", "EUR", "2021-10-18",
     "列名の歴史的負債に注意(実体はEUR・2026-07-18確定)。2026-04-22は欠損補正済(S1a, ets_correction参照)"),
    ("GX", "日本GX-ETS", "GX-ETS", "JPX(東京証券取引所)カーボン・クレジット市場", "JPY", "2025-07-01",
     "超過削減枠(銘柄コード5051000)。取引単位1t-CO2/価格刻み1円(JPX制度概要ページ確認2026-07-19)。"
     "series_start=機械遡及可能な索引/archivesページの実データ最古日(2026-07-19 backfill実行で確認)。"
     "制度としての取引対象化は2024年11月〜(複数出典で月単位確認済みだが日次は未確認)だが、"
     "archives-13.html以降は404(2026-07-19実測)=同一経路でのそれ以遠の遡及はサイト側制約で不可能、"
     "2024-11〜2025-06分は別経路要検討(金博士様判断待ち・未着手)。"
     "実取引はFY2025 11-12月の毎週金曜限定運用中の2025-11-14/21の2日のみ確認(価格1800円/t-CO2)。"
     "no_trade多数(247日中245日)は想定内(特定日限定運用のため)。"),
]

# (market, date, field, wrong_value, corrected_value, evidence, decided_by, dd_ref)
CORRECTIONS = [
    ("CCER", "2024-01-22", "close_price", "0.0", "63.51",
     "daily_amount 23835280 / daily_volume 375315 = 63.5074 (round 2)",
     "奏(金博士様承認 DEFECT-C, regression復元裁定 2026-07-18夜)", "3148"),
]

ALLOWED_CORRECTION_FIELDS = {
    "open_price", "high_price", "low_price", "close_price", "currency", "volume", "amount", "no_trade",
}


def log(smart, run_at, market, inserted, skipped, gap_alert, status):
    smart.execute(
        "INSERT INTO ets_sync_log (run_at,market,rows_inserted,rows_skipped,gap_alert,status) VALUES (?,?,?,?,?,?)",
        (run_at, market, inserted, skipped, gap_alert, status),
    )


def reset_tables(smart):
    smart.execute("DELETE FROM ets_daily")
    smart.execute("DELETE FROM ets_market_meta")
    smart.execute("DELETE FROM ets_source")


def load_cea(smart, china, run_at):
    rows = china.execute(
        "SELECT date, opening_price, high_price, low_price, closing_price, total_volume, total_amount, fetched_at "
        "FROM cn_ets_market_cea_daily ORDER BY date"
    ).fetchall()
    data = [("CEA", d, o, h, l, c, "CNY", v, a, 0, 2, fa) for d, o, h, l, c, v, a, fa in rows]
    smart.executemany(f"INSERT INTO ets_daily ({DAILY_COLS}) VALUES ({DAILY_PLACEHOLDERS})", data)
    log(smart, run_at, "CEA", len(data), 0, None, "loaded")
    return len(data)


def load_ccer(smart, china, run_at):
    rows = china.execute(
        "SELECT date, avg_price, daily_volume, daily_amount, fetched_at FROM cn_ets_market_ccer_daily ORDER BY date"
    ).fetchall()
    data = []
    no_trade_count = 0
    for d, avg_price, vol, amt, fa in rows:
        no_trade = 1 if (avg_price == 0 and vol == 0) else 0
        # no_trade日はclose/volume/amountを揃えてNULL化(蒼悟observation 2026-07-19: GX(=NULL)とCCER(=0)の
        # volume表現不統一を解消。NULL採用理由=SQL集計整合性: AVG(volume)は無取引日を分母から正しく除外できる
        # (偽の0を混在させるとAVGが不当に押し下げられる)。CCER源自体は0を明示するがDB層で正規化する。
        close = None if no_trade else avg_price
        vol_out = None if no_trade else vol
        amt_out = None if no_trade else amt
        no_trade_count += no_trade
        data.append(("CCER", d, None, None, None, close, "CNY", vol_out, amt_out, no_trade, 3, fa))
    smart.executemany(f"INSERT INTO ets_daily ({DAILY_COLS}) VALUES ({DAILY_PLACEHOLDERS})", data)
    log(smart, run_at, "CCER", len(data), 0, None, f"loaded(no_trade={no_trade_count})")
    return len(data), no_trade_count


def load_kau(smart, korea, run_at):
    ohlcv_rows = korea.execute(
        "SELECT date, kau_type, open_price, high_price, low_price, close_price, volume, fetched_at "
        "FROM kets_market_kau_ohlcv ORDER BY date"
    ).fetchall()
    data_ohlcv = [(kt, d, o, h, l, c, "KRW", v, None, 0, 4, fa) for d, kt, o, h, l, c, v, fa in ohlcv_rows]
    smart.executemany(f"INSERT INTO ets_daily ({DAILY_COLS}) VALUES ({DAILY_PLACEHOLDERS})", data_ohlcv)
    log(smart, run_at, "KAU_ohlcv", len(data_ohlcv), 0, None, "loaded(priority)")

    before = smart.execute("SELECT COUNT(*) FROM ets_daily").fetchone()[0]
    daily_rows = korea.execute(
        "SELECT date, permit_type, closing_price, fetched_at FROM kets_market_daily_price ORDER BY date"
    ).fetchall()
    data_daily = [(pt, d, None, None, None, c, "KRW", None, None, 0, 4, fa) for d, pt, c, fa in daily_rows]
    smart.executemany(f"INSERT OR IGNORE INTO ets_daily ({DAILY_COLS}) VALUES ({DAILY_PLACEHOLDERS})", data_daily)
    after = smart.execute("SELECT COUNT(*) FROM ets_daily").fetchone()[0]
    actual_inserted = after - before
    skipped = len(data_daily) - actual_inserted
    log(smart, run_at, "KAU_KCU_KOC_daily_price", actual_inserted, skipped, None,
        "loaded(ohlcv-overlap skipped)")
    log(smart, run_at, "KAU22", 0, 0, None,
        "ohlcv/daily_price重複2649件中不一致1件: KAU22 2023-07-10 ohlcv=10300 vs daily_price=10350 → ohlcv優先採用(奏裁定 2026-07-18)")
    return len(data_ohlcv), len(data_daily), actual_inserted, skipped


def load_eua(smart, gods, run_at):
    rows = gods.execute("SELECT date, price_usd, volume, fetched_at FROM raw_eu_ets_daily ORDER BY date").fetchall()
    data = [("EUA", d, None, None, None, p, "EUR", v, None, 0, 5, fa) for d, p, v, fa in rows]
    smart.executemany(f"INSERT INTO ets_daily ({DAILY_COLS}) VALUES ({DAILY_PLACEHOLDERS})", data)
    log(smart, run_at, "EUA", len(data), 0, None, "loaded")
    return len(data)


def load_gx(smart, gods, run_at):
    rows = gods.execute(
        "SELECT date, open_price, high_price, low_price, close_price, volume, no_trade, fetched_at "
        "FROM raw_gx_ets_daily ORDER BY date"
    ).fetchall()
    data = [("GX", d, o, h, l, c, "JPY", v, None, nt, 7, fa) for d, o, h, l, c, v, nt, fa in rows]
    smart.executemany(f"INSERT INTO ets_daily ({DAILY_COLS}) VALUES ({DAILY_PLACEHOLDERS})", data)
    n_notrade = sum(1 for row in data if row[9] == 1)
    log(smart, run_at, "GX", len(data), 0, None, f"loaded(no_trade={n_notrade})")
    return len(data), n_notrade


def ensure_corrections(smart, run_at):
    existing = set(smart.execute("SELECT market,date,field FROM ets_correction").fetchall())
    inserted = 0
    for market, date, field, wrong, corrected, evidence, decided_by, dd_ref in CORRECTIONS:
        if (market, date, field) not in existing:
            smart.execute(
                "INSERT INTO ets_correction (market,date,field,wrong_value,corrected_value,evidence,decided_by,dd_ref,applied_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (market, date, field, wrong, corrected, evidence, decided_by, dd_ref, run_at),
            )
            inserted += 1
    return inserted


def reapply_corrections(smart):
    """Idempotent: re-running always drives ets_daily to the same corrected state."""
    rows = smart.execute("SELECT market,date,field,corrected_value FROM ets_correction").fetchall()
    applied = 0
    for market, date, field, corrected_value in rows:
        if field not in ALLOWED_CORRECTION_FIELDS:
            raise ValueError(f"ets_correction: disallowed field {field!r}")
        if field == "close_price":
            cur = smart.execute(
                "UPDATE ets_daily SET close_price=?, no_trade=0 WHERE market=? AND date=?",
                (float(corrected_value), market, date),
            )
        else:
            cur = smart.execute(
                f"UPDATE ets_daily SET {field}=? WHERE market=? AND date=?",
                (corrected_value, market, date),
            )
        applied += cur.rowcount
    return applied


PERIOD_VIEW_SQL = """
CREATE VIEW {view_name} AS
WITH d AS (
    SELECT *, strftime('{fmt}', date) AS period
    FROM ets_daily
    WHERE no_trade = 0 AND close_price IS NOT NULL
),
ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY market, period ORDER BY date ASC) AS rn_first,
        ROW_NUMBER() OVER (PARTITION BY market, period ORDER BY date DESC) AS rn_last
    FROM d
)
SELECT
    market,
    period,
    MIN(date) AS period_start,
    MAX(date) AS period_end,
    MAX(CASE WHEN rn_first = 1 THEN COALESCE(open_price, close_price) END) AS open,
    MAX(COALESCE(high_price, close_price)) AS high,
    MIN(COALESCE(low_price, close_price)) AS low,
    MAX(CASE WHEN rn_last = 1 THEN close_price END) AS close,
    SUM(volume) AS volume,
    SUM(amount) AS amount,
    MAX(currency) AS currency,
    COUNT(*) AS trading_days
FROM ranked
GROUP BY market, period
ORDER BY market, period
"""


def create_period_views(smart):
    """月次/年次 集計view (CP1充足, 奏発注 2026-07-19 [発注]月次年次view実装).

    ets_dailyから導出(実表ではない・再構築不要=viewは常に最新ets_dailyを反映)。
    規約:
    - no_trade=1行は集計から除外(取引実績のない日を0や欠測で埋めない=L1E)。
    - open=期間初日のCOALESCE(open_price, close_price)/close=期間終日のclose_price。
      理由: close_priceのみ全market 100%充足(open/high/low_priceはCEA等一部market限定で、
      KCU/KOC/CCER/EUA等は終値のみの系列=実データ物的確認2026-07-19)。open_priceがある
      market(CEA等)は真の始値を使い、無いmarketは初日終値を代用(手計算突合でCEA 2026-06の
      open=82.5(真の始値)と一致確認済み=COALESCE適用前は82.01(初日終値)を誤って返していた
      defectをここで検出・修正)。
    - high/lowはCOALESCE(high_price/low_price, close_price): 真のOHLC値がある行はそれを使い、
      終値のみの行はclose_priceを上下限の代用値として扱う(過大/過小主張を避けるための保守的近似)。
    - 該当期間に取引実績が1件もないmarketは行ごと不在(fabricationを避ける=L1E)。GXはこの理由で
      ほとんどの月/年に行が存在しない(2025-11のみ実績あり)。
    - 韓国の一次公式月次集計(korea_ets_smart.db kets_market_monthly)とは非突合(federation参照の
      ままとし、本viewはets_daily由来の導出系と明記。突合検証は必要になった時点で別途)。
    """
    smart.execute("DROP VIEW IF EXISTS ets_monthly")
    smart.execute(PERIOD_VIEW_SQL.format(view_name="ets_monthly", fmt="%Y-%m"))
    smart.execute("DROP VIEW IF EXISTS ets_yearly")
    smart.execute(PERIOD_VIEW_SQL.format(view_name="ets_yearly", fmt="%Y"))


def main():
    run_at = datetime.now().isoformat()
    smart = sqlite3.connect(SMART)
    smart.execute("PRAGMA foreign_keys = ON")
    china = sqlite3.connect(f"file:{CHINA}?mode=ro", uri=True)
    korea = sqlite3.connect(f"file:{KOREA}?mode=ro", uri=True)
    gods = sqlite3.connect(f"file:{GODS}?mode=ro", uri=True)

    reset_tables(smart)
    smart.executemany("INSERT INTO ets_source (id,name,url,method,notes) VALUES (?,?,?,?,?)", SOURCES)
    smart.executemany(
        "INSERT INTO ets_market_meta (market,name_ja,system_name,exchange,currency,series_start,notes) VALUES (?,?,?,?,?,?,?)",
        MARKET_META,
    )

    n_cea = load_cea(smart, china, run_at)
    n_ccer, n_notrade = load_ccer(smart, china, run_at)
    n_ohlcv, n_daily_src, n_daily_ins, n_daily_skip = load_kau(smart, korea, run_at)
    n_eua = load_eua(smart, gods, run_at)
    try:
        n_gx, n_gx_notrade = load_gx(smart, gods, run_at)
    except sqlite3.OperationalError as e:
        if "no such table" not in str(e):
            raise
        n_gx, n_gx_notrade = 0, 0
        log(smart, run_at, "GX", 0, 0, None, "skipped(raw_gx_ets_daily not yet populated)")

    ins_corr = ensure_corrections(smart, run_at)
    applied1 = reapply_corrections(smart)
    applied2 = reapply_corrections(smart)

    create_period_views(smart)

    smart.commit()

    total = smart.execute("SELECT COUNT(*) FROM ets_daily").fetchone()[0]
    print("=== build_ets_market_smart: initial construction ===")
    print(f"CEA={n_cea}  CCER={n_ccer}(no_trade={n_notrade})  "
          f"KAU_ohlcv={n_ohlcv}  daily_price(src={n_daily_src} inserted={n_daily_ins} skipped={n_daily_skip})  "
          f"EUA={n_eua}  GX={n_gx}(no_trade={n_gx_notrade})")
    print(f"total ets_daily rows = {total}")
    print(f"corrections: newly_inserted={ins_corr}  applied_run1={applied1}  applied_run2={applied2}")

    china.close(); korea.close(); gods.close(); smart.close()


if __name__ == "__main__":
    main()

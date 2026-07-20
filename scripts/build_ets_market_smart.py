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

CREATE_ETS_AUCTION_SQL = """
CREATE TABLE IF NOT EXISTS ets_auction (
  auction_date TEXT NOT NULL,
  auction_time TEXT,
  auction_name TEXT NOT NULL,
  contract TEXT,
  status TEXT,
  auction_price_eur REAL,
  min_bid_eur REAL, max_bid_eur REAL, mean_eur REAL, median_eur REAL,
  volume_tco2 INTEGER,
  total_bids_tco2 INTEGER,
  cover_ratio REAL,
  bidders INTEGER,
  successful_bidders INTEGER,
  revenue_eur REAL,
  zone TEXT,
  file_year INTEGER NOT NULL,
  source_id INTEGER NOT NULL REFERENCES ets_source(id),
  fetched_at TEXT,
  PRIMARY KEY (auction_date, auction_name)
)
"""
AUCTION_COLS = ("auction_date,auction_time,auction_name,contract,status,"
                 "auction_price_eur,min_bid_eur,max_bid_eur,mean_eur,median_eur,"
                 "volume_tco2,total_bids_tco2,cover_ratio,bidders,successful_bidders,"
                 "revenue_eur,zone,file_year,fetched_at,source_id")
AUCTION_PLACEHOLDERS = ",".join("?" * 20)

SOURCES = [
    (1, "CNEEEX (Shanghai Environment and Energy Exchange)", "https://overview.cneeex.com/qgtpfqjy/mrgk/",
     "web scrape (収集は2025-12まで、現行出典はid2)",
     "CEA原初出典。当家の収集は2025-12まで(現行出典はid2 carbonmarket.cn)。"
     "サイト自体は2026-07-21実測で稼働確認(生HTTP 200・個別URL到達可、oni_ets_t7 CEA backfill 180件で実証)"),
    (2, "carbonmarket.cn", "https://carbonmarket.cn/ets/cets/",
     "HTML table scrape (Table1掛牌+Table2大宗)", "CEA現行出典(2025-12-25〜)。china smartに出自列が無いため全CEA行をid2扱い(簡潔優先、遷移史はmeta.notesに記載)"),
    (3, "CCER Official (Beijing Green Exchange)", "https://www.ccer.com.cn/wcm/ccer/html/2502lshq/index.html",
     "JSON API (/wcm/ccer/data/2502lshq.json)", "CCER出典"),
    (4, "KRX (Korea Exchange)", None, "kets collector (ohlcv + daily_price)", "KAU/KCU/KOC全permit_type共通出典"),
    (5, "yfinance CO2.L (SparkChange Physical Carbon EUA ETC, EUR建て)", None,
     "yfinance Ticker.history(period='2y')", "EUA出典。列名price_usdは歴史的負債=実体EUR(2026-07-18鬼検証で確定)"),
    (6, "NASDAQ ICE_EUA1 Settle (EUR)", None, None, "不使用確定(2026-07-20金博士様裁定・有料断念)"),
    (7, "JPXカーボン・クレジット市場日報", "https://www.jpx.co.jp/equities/carbon-credit/daily/index.html",
     "PDF fetch(索引/archivesページでURL解決→PDFテーブル抽出、銘柄コード5051000行のみ抽出)",
     "GX-ETS超過削減枠出典。設計=docs/gx_ets_acquisition_design_20260719.md、取得=scripts/fetch_gx_ets.py"),
    (8, "FSR Figure_1.csv (Florence School of Regulation, EUI)",
     "https://fsr.eui.eu/wp-content/uploads/2024/10/Figure_1.csv",
     "公式配布CSV直取得(md5=43af6218d0b671f50f2e77d0f1c1cc9b・2026-07-20取得)",
     "EUA歴史価格2005-2024。掲載頁=https://fsr.eui.eu/eu-emission-trading-system-eu-ets/。"
     "FSR一次系列は非明示→出典表記は「FSR公表データ」(誠実な不確実性)"),
    (9, "EEX EUA Primary Market Auction Report", "https://public.eex-group.com/eex/eua-auction-report/index.html",
     "local xls/xlsx (md5-pinned, data/sources/eua_hist/)",
     "一次市場オークション結果2017-2026(価格+volume付き)。歴史層=gods_eye.raw_eua_auction_eex(恒久)。"
     "ets_dailyには混ぜず新表ets_auctionへ格納(同日複数オークション・落札価格≠二次市場終値のため)"),
]

MARKET_META = [
    # P1 market定義正文v1.1(奏裁定 2026-07-18 22:14, 蒼悟逆FB反映)確定: 9 family行
    # D2是正(oni_ets_t6 F2案b, 2026-07-20): volume_unit列追加(全market必須充足)。
    # EUAのみ証券出来高(ETC口数)・他markets全てtCO2 — 単位混在防止(桁差1/500の理由=単位差)
    ("CEA", "中国CEA(全国ETS)", "China-ETS", "上海環境能源交易所", "CNY", "2021-07-16",
     "全国碳配額。出典遷移: CNEEEX(〜2025-12)→carbonmarket.cn(2025-12-25〜)", "tCO2"),
    ("CCER", "中国CCER(自主削減)", "China-ETS", "北京緑色交易所", "CNY", "2024-01-22",
     "avg_price=0かつdaily_volume=0の日はno_trade=1(無取引日、127件)。2024-01-22は欠損補正済(ets_correction参照)", "tCO2"),
    ("KAU", "韓国KAU(K-ETS 排出権・vintage別)", "K-ETS", "KRX", "KRW", "2015-01-12",
     "vintage別market値(KAU15〜KAU30)。ohlcv系(2021-, OHLCV優先)+終値歴史(2015-)の2系統統合。重複2649件中不一致1件(KAU22 2023-07-10)はohlcv優先で採用・ets_sync_logに記録", "tCO2"),
    ("KCU", "韓国KCU(相殺クレジット)", "K-ETS", "KRX", "KRW", None,
     "vintage別market値(KCU15〜KCU26)。kets_market_daily_priceのみ出典(終値のみ、OHLCV無し)", "tCO2"),
    ("KOC", "韓国KOC(オフセットクレジット)", "K-ETS", "KRX", "KRW", None,
     "期間別market値(KOC, KOC20-22等)。kets_market_daily_priceのみ出典(終値のみ、OHLCV無し)", "tCO2"),
    ("i-KCU", "韓国i-KCU(国際相殺クレジット)", "K-ETS", "KRX", "KRW", None,
     "vintage別market値(i-KCU23〜26)。kets_market_daily_priceのみ出典(終値のみ、OHLCV無し)", "tCO2"),
    ("i-KOC", "韓国i-KOC(国際オフセットクレジット)", "K-ETS", "KRX", "KRW", None,
     "期間別market値(i-KOC21-26等)。kets_market_daily_priceのみ出典(終値のみ、OHLCV無し)", "tCO2"),
    ("EUA", "EU EUA(EU-ETS)", "EU-ETS", "SparkChange CO2.L ETC(LSE上場)", "EUR", "2005-03-09",
     "出典遷移: FSR歴史(〜2021-10-17)→CO2.L現行(2021-11-04〜、2021-10-18〜11-03の13日はLSE上場前ティックのためpre_listing除外)。列名の歴史的負債に注意(実体はEUR・2026-07-18確定)。2026-04-22は欠損補正済(S1a, ets_correction参照)。CO2.Lは100%現物担保ETC(ICE先物連動ではない、HANetf公式確認2026-07-20)", "ETC口数(株数)。他marketのtCO2とは非互換単位=同一軸比較禁止"),
    ("GX", "日本GX-ETS", "GX-ETS", "JPX(東京証券取引所)カーボン・クレジット市場", "JPY", "2025-07-01",
     "超過削減枠(銘柄コード5051000)。取引単位1t-CO2/価格刻み1円(JPX制度概要ページ確認2026-07-19)。"
     "series_start=機械遡及可能な索引/archivesページの実データ最古日(2026-07-19 backfill実行で確認)。"
     "制度としての取引対象化は2024年11月〜(複数出典で月単位確認済みだが日次は未確認)だが、"
     "archives-13.html以降は404(2026-07-19実測)=同一経路でのそれ以遠の遡及はサイト側制約で不可能、"
     "2024-11〜2025-06分は別経路要検討(金博士様判断待ち・未着手)。"
     "実取引はFY2025 11-12月の毎週金曜限定運用中の2025-11-14/21の2日のみ確認(価格1800円/t-CO2)。"
     "no_trade多数(247日中245日)は想定内(特定日限定運用のため)。", "tCO2"),
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
    smart.execute("DELETE FROM ets_auction")
    smart.execute("DELETE FROM ets_market_meta")
    smart.execute("DELETE FROM ets_source")


def load_cea(smart, china, run_at):
    rows = china.execute(
        "SELECT date, opening_price, high_price, low_price, closing_price, total_volume, total_amount, fetched_at "
        "FROM cn_ets_market_cea_daily ORDER BY date"
    ).fetchall()
    # D1是正(oni_ets_t6 F1, 奏裁定2026-07-20): 2021-07-16(CEA取引開始日)のみ原典自体がo/h/l=0
    # (市場初日でOHLC未公表の欠測表現・価格0元は非実勢)。close/volume/amountは史実のため不変保全。
    # 他日のo/h/l非ゼロ値(low>close 5行・2023-12-12等)は原典忠実のため対象外(D1-2)。
    data = []
    for d, o, h, l, c, v, a, fa in rows:
        if d == "2021-07-16" and o == 0 and h == 0 and l == 0:
            o, h, l = None, None, None
        data.append(("CEA", d, o, h, l, c, "CNY", v, a, 0, 2, fa))
    smart.executemany(f"INSERT INTO ets_daily ({DAILY_COLS}) VALUES ({DAILY_PLACEHOLDERS})", data)
    log(smart, run_at, "CEA", len(data), 0, None, "loaded(2021-07-16 o/h/l 0→NULL:市場初日欠測)")
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
    # D1是正(oni_ets_t6 F1): korea_ets_smart.db側collectorがOHLC breakdown未取得日をo/h/l/v=0で表現
    # (2026-03-04一括fetch分等)。価格0ウォンは非実勢のため欠測NULLへ変換、closeのみ実勢値として残す。
    # no_tradeは元値のまま(=0)維持: 取引自体は発生しclose有り=「OHLC無し」と「無取引」は別概念(D1-4)。
    # raw korea_ets_smart.dbは不可侵(read-only)・変換はこのINSERT時点のみ。
    zerofill_count = 0
    data_ohlcv = []
    for d, kt, o, h, l, c, v, fa in ohlcv_rows:
        if o == 0 and h == 0 and l == 0 and v in (0, None) and c not in (None, 0):
            zerofill_count += 1
            o, h, l, v = None, None, None, None
        data_ohlcv.append((kt, d, o, h, l, c, "KRW", v, None, 0, 4, fa))
    smart.executemany(f"INSERT INTO ets_daily ({DAILY_COLS}) VALUES ({DAILY_PLACEHOLDERS})", data_ohlcv)
    log(smart, run_at, "KAU_ohlcv", len(data_ohlcv), 0, None, f"loaded(priority, zerofill_to_null={zerofill_count})")

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
    """EUA歴史層(FSR, source_id=8)+現行層(CO2.L, source_id=5)の2系列mergeロード。

    2026-07-19投入分(EEXオークション998行)を直接ets_dailyへ書いたところ、翌日の本スクリプト
    再実行(reset_tables()の全消去)で消滅した反省を踏まえ、歴史データはgods_eye.db(buildソース側)に
    恒久保持し、揮発層(ets_daily)への
    投入は本関数が毎回行う。期間重複assertは歴史層の汚染混入を投入前に検出し中断する安全弁。
    """
    overlap = gods.execute(
        "SELECT COUNT(*) FROM raw_eua_hist_fsr WHERE date >= '2021-10-18'"
    ).fetchone()[0]
    if overlap:
        raise RuntimeError(
            f"EUA hist/current overlap: raw_eua_hist_fsr has {overlap} row(s) on/after 2021-10-18 "
            "(overlaps raw_eu_ets_daily start). Aborting load to avoid double-counting."
        )

    hist_rows = gods.execute(
        "SELECT date, price_eur, loaded_at FROM raw_eua_hist_fsr ORDER BY date"
    ).fetchall()
    hist_data = [("EUA", d, None, None, None, p, "EUR", None, None, 0, 8, la) for d, p, la in hist_rows]
    smart.executemany(f"INSERT INTO ets_daily ({DAILY_COLS}) VALUES ({DAILY_PLACEHOLDERS})", hist_data)
    log(smart, run_at, "EUA_hist_fsr", len(hist_data), 0, None, "loaded")

    cur_rows = gods.execute("SELECT date, price_usd, volume, fetched_at FROM raw_eu_ets_daily ORDER BY date").fetchall()
    cur_data = [("EUA", d, None, None, None, p, "EUR", v, None, 0, 5, fa) for d, p, v, fa in cur_rows]
    smart.executemany(f"INSERT INTO ets_daily ({DAILY_COLS}) VALUES ({DAILY_PLACEHOLDERS})", cur_data)
    log(smart, run_at, "EUA", len(cur_data), 0, None, "loaded")

    # D6是正(oni_ets_t6 F3案B, 奏執行裁定): CO2.L LSE Primary Listing=2021-11-04(HANetf公式)より前の
    # 13行(2021-10-18〜11-03, volume=0)は上場前でvolumeの実勢性が未確認。削除せず可逆フラグのみ付与
    # (pre_listing=1)し、集計(ets_monthly/yearly view)・配信(build_ets_market.py)側で除外する。
    # 誠実な不確実性の保全(D6-3): 価格自体の正体(何を表す値か)は未到達のため断定しない。
    n_pre_listing = smart.execute(
        "UPDATE ets_daily SET pre_listing=1 WHERE market='EUA' AND source_id=5 AND date<'2021-11-04'"
    ).rowcount
    log(smart, run_at, "EUA_pre_listing_flag", 0, 0, None,
        f"flagged(pre_listing={n_pre_listing}, boundary=2021-11-04 LSE listing)")

    return len(hist_data), len(cur_data)


def load_eua_auction(smart, gods, run_at):
    """EUAオークション系列(EEX一次市場, source_id=9)ロード。

    歴史層はgods_eye.db raw_eua_auction_eex(恒久・build非破壊、2026-07-20葉山投入)。本関数は
    そこからread-onlyで読み、ets_market_smart.db側の揮発層ets_auctionへ全件再構築する。
    ets_daily/EUA日次(id8+id5, load_eua())とは別表・非接触 — 同日複数オークション(DE/EU/PL別)が
    あり(market,date)粒度に合わない上、落札価格と二次市場終値は意味が別のため。
    """
    rows = gods.execute(
        "SELECT auction_date,auction_time,auction_name,contract,status,"
        "auction_price_eur,min_bid_eur,max_bid_eur,mean_eur,median_eur,"
        "volume_tco2,total_bids_tco2,cover_ratio,bidders,successful_bidders,"
        "revenue_eur,zone,file_year,loaded_at "
        "FROM raw_eua_auction_eex ORDER BY auction_date, auction_name"
    ).fetchall()
    data = [r + (9,) for r in rows]
    smart.executemany(f"INSERT INTO ets_auction ({AUCTION_COLS}) VALUES ({AUCTION_PLACEHOLDERS})", data)
    log(smart, run_at, "EUA_auction_eex", len(data), 0, None, "loaded")
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
    WHERE no_trade = 0 AND close_price IS NOT NULL AND pre_listing = 0
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
    smart.execute(CREATE_ETS_AUCTION_SQL)
    china = sqlite3.connect(f"file:{CHINA}?mode=ro", uri=True)
    korea = sqlite3.connect(f"file:{KOREA}?mode=ro", uri=True)
    gods = sqlite3.connect(f"file:{GODS}?mode=ro", uri=True)

    reset_tables(smart)
    smart.executemany("INSERT INTO ets_source (id,name,url,method,notes) VALUES (?,?,?,?,?)", SOURCES)
    smart.executemany(
        "INSERT INTO ets_market_meta (market,name_ja,system_name,exchange,currency,series_start,notes,volume_unit) VALUES (?,?,?,?,?,?,?,?)",
        MARKET_META,
    )

    n_cea = load_cea(smart, china, run_at)
    n_ccer, n_notrade = load_ccer(smart, china, run_at)
    n_ohlcv, n_daily_src, n_daily_ins, n_daily_skip = load_kau(smart, korea, run_at)
    n_eua_hist, n_eua_cur = load_eua(smart, gods, run_at)
    n_eua_auction = load_eua_auction(smart, gods, run_at)
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
    total_auction = smart.execute("SELECT COUNT(*) FROM ets_auction").fetchone()[0]
    print("=== build_ets_market_smart: initial construction ===")
    print(f"CEA={n_cea}  CCER={n_ccer}(no_trade={n_notrade})  "
          f"KAU_ohlcv={n_ohlcv}  daily_price(src={n_daily_src} inserted={n_daily_ins} skipped={n_daily_skip})  "
          f"EUA_hist_fsr={n_eua_hist}+EUA_cur={n_eua_cur}(total={n_eua_hist + n_eua_cur})  "
          f"EUA_auction_eex={n_eua_auction}  "
          f"GX={n_gx}(no_trade={n_gx_notrade})")
    print(f"total ets_daily rows = {total}")
    print(f"total ets_auction rows = {total_auction}")
    print(f"corrections: newly_inserted={ins_corr}  applied_run1={applied1}  applied_run2={applied2}")

    china.close(); korea.close(); gods.close(); smart.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fetch_gx_ets.py — GX-ETS(超過削減枠)取得スクリプト。

奏(editor) 発注 2026-07-19(金博士様GO)。葉山(actor)実装。設計正本=docs/gx_ets_acquisition_design_20260719.md。

出典: JPXカーボン・クレジット市場日報(PDF, 営業日ごと)
https://www.jpx.co.jp/equities/carbon-credit/daily/index.html
制度名="超過削減枠"(銘柄コード5051000)の行のみ抽出。

2段階fetch: (1)索引/archivesページHTMLから対象日PDFのURLを解決(ハッシュ様セグメントは
日付から予測不可のため必須) (2)PDFをテーブル抽出(pdfplumber)し銘柄コード5051000行を読む。

書込み先: gods_eye.db の raw_gx_ets_daily (新設・build_ets_market_smart.pyのEU/raw_eu_ets_daily
パターンに倣う read-only-source用の中間staging層)。ets_market_smart.db 本体はbuild_ets_market_smart.py
側でのみ書き込む(本スクリプトはgods_eye.dbのみ書込み)。

Usage:
  python scripts/fetch_gx_ets.py --date 2026-07-17          # 単日
  python scripts/fetch_gx_ets.py --month 2026-07            # 当該月の索引/archiveページを走査し全営業日試行
  python scripts/fetch_gx_ets.py --backfill-months 13       # 直近Nヶ月(索引ページのプルダウン機械遡及可能分)
  python scripts/fetch_gx_ets.py --dry-run ...               # DB書込みなし・パース結果表示のみ
"""
import argparse
import io
import re
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime, date

import pdfplumber

INDEX_URL = "https://www.jpx.co.jp/equities/carbon-credit/daily/index.html"
ARCHIVE_URL_FMT = "https://www.jpx.co.jp/equities/carbon-credit/daily/archives-{:02d}.html"
GODS_DB = r"C:\Users\jin_z\.claude\databases\gods_eye.db"
TICKER = "5051000"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

PDF_LINK_RE = re.compile(r'href="([^"]*?/(\d{8})_cc_quotations\.pdf)"')


def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def resolve_pdf_urls_from_page(html_bytes):
    """archivesページ/indexページのHTMLから {YYYYMMDD: 絶対URL} を全件抽出。"""
    text = html_bytes.decode("utf-8", errors="replace")
    out = {}
    for rel_url, yyyymmdd in PDF_LINK_RE.findall(text):
        if rel_url.startswith("http"):
            abs_url = rel_url
        else:
            abs_url = "https://www.jpx.co.jp" + rel_url
        out[yyyymmdd] = abs_url
    return out


def list_available_dates(months_back=0):
    """indexページ(当月)+archives-01..NNページから日付->PDF URLのdictを構築。"""
    all_urls = {}
    html = http_get(INDEX_URL)
    all_urls.update(resolve_pdf_urls_from_page(html))
    for i in range(1, months_back + 1):
        url = ARCHIVE_URL_FMT.format(i)
        try:
            html = http_get(url)
        except Exception as e:
            print(f"[WARN] archive page {i} ({url}) fetch failed: {e}", file=sys.stderr)
            continue
        all_urls.update(resolve_pdf_urls_from_page(html))
        time.sleep(0.3)
    return all_urls


HEADER_KEYS = ["制度名", "分類名", "方法論名", "銘柄コード"]


def parse_gx_row(pdf_bytes, source_url):
    """PDFバイト列から銘柄コード5051000行を抽出。戻り値: dict or None(該当行なし)。"""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        page = pdf.pages[0]
        table = page.extract_table()
    if not table:
        raise ValueError(f"table extraction failed (no table found): {source_url}")
    header = table[0]
    # ヘッダは複数行に分割されて結合されているケルースがあるため、
    # 「銘柄コード」を含む列インデックスを名前でなく位置ベースで確定(PDF層構造は固定=設計ノート1.2確認済み)。
    # 実測列順(2026-05-29/07-17両サンプルで確認済み):
    # 0制度名 1分類名 2方法論名 3銘柄コード 4基準値段_値段 5基準値段_日付 6基準値段_区分
    # 7始値 8区分_始 9高値 10区分_高 11安値 12区分_安 13終値 14区分_終 15売買高
    # 16翌日基準値段_値段 17翌日基準値段_日付 18翌日基準値段_区分
    target_row = None
    for row in table[1:]:
        if row and len(row) > 3 and row[3] and TICKER in row[3]:
            target_row = row
            break
    if target_row is None:
        raise ValueError(f"ticker {TICKER} row not found in table: {source_url}")

    def cell(i):
        return target_row[i].strip() if i < len(target_row) and target_row[i] else None

    kizyun_str = cell(4)
    no_session = kizyun_str is None or "立会なし" in kizyun_str

    def num(i):
        v = cell(i)
        if v is None or v == "-":
            return None
        return float(v.replace(",", ""))

    close_price = num(13)
    # no_trade=1 の2ケース: (a)立会自体なし(区分なし) (b)セッションは開催されたが約定なし(終値欄が"-")。
    # 後者はバックフィル検証で2025-11-07/11-28/12-05/12-12/12-19/12-26に実在確認(セッションありno_trade=0のまま
    # close_price=Noneになる論理的欠陥だった=実装中に発見・是正)。
    no_trade = 1 if (no_session or close_price is None) else 0

    return {
        "no_trade": no_trade,
        "open_price": num(7),
        "high_price": num(9),
        "low_price": num(11),
        "close_price": close_price,
        "volume": num(15),
        "source_url": source_url,
    }


def ensure_table(gods):
    gods.execute("""
        CREATE TABLE IF NOT EXISTS raw_gx_ets_daily (
            date TEXT PRIMARY KEY,
            open_price REAL,
            high_price REAL,
            low_price REAL,
            close_price REAL,
            volume REAL,
            no_trade INTEGER NOT NULL DEFAULT 0,
            source_url TEXT,
            fetched_at TEXT
        )
    """)


def write_row(gods, iso_date, parsed, fetched_at):
    gods.execute(
        "INSERT OR REPLACE INTO raw_gx_ets_daily "
        "(date, open_price, high_price, low_price, close_price, volume, no_trade, source_url, fetched_at) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (iso_date, parsed["open_price"], parsed["high_price"], parsed["low_price"],
         parsed["close_price"], parsed["volume"], parsed["no_trade"], parsed["source_url"], fetched_at),
    )


def yyyymmdd_to_iso(s):
    return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD 単日")
    ap.add_argument("--month", help="YYYY-MM (未使用・将来拡張用に予約)")
    ap.add_argument("--backfill-months", type=int, default=0, help="当月含め遡るarchivesページ数(直近N-1ヶ月分)")
    ap.add_argument("--dry-run", action="store_true", help="DB書込みなし。パース結果を表示のみ")
    args = ap.parse_args()

    months_back = max(args.backfill_months - 1, 0) if args.backfill_months else 12
    print(f"[INFO] resolving PDF URLs (index + {months_back} archive pages)...")
    url_map = list_available_dates(months_back=months_back)
    print(f"[INFO] resolved {len(url_map)} dates with PDF links "
          f"(range: {min(url_map) if url_map else 'N/A'} .. {max(url_map) if url_map else 'N/A'})")

    if args.date:
        target_yyyymmdd = args.date.replace("-", "")
        targets = {target_yyyymmdd: url_map.get(target_yyyymmdd)}
        if targets[target_yyyymmdd] is None:
            print(f"[ERROR] {args.date}: no PDF link found in resolved index/archive pages", file=sys.stderr)
            sys.exit(1)
    else:
        targets = url_map

    gods = None
    if not args.dry_run:
        gods = sqlite3.connect(GODS_DB)
        ensure_table(gods)

    ok, fail, notrade = 0, 0, 0
    fail_dates = []
    for yyyymmdd in sorted(targets):
        pdf_url = targets[yyyymmdd]
        iso_date = yyyymmdd_to_iso(yyyymmdd)
        try:
            pdf_bytes = http_get(pdf_url)
            parsed = parse_gx_row(pdf_bytes, pdf_url)
        except Exception as e:
            print(f"[FAIL] {iso_date}: {e}", file=sys.stderr)
            fail += 1
            fail_dates.append(iso_date)
            continue
        tag = "no_trade" if parsed["no_trade"] else f"close={parsed['close_price']} vol={parsed['volume']}"
        print(f"[OK] {iso_date}: {tag}")
        if parsed["no_trade"]:
            notrade += 1
        ok += 1
        if gods is not None:
            write_row(gods, iso_date, parsed, datetime.now().isoformat())
        time.sleep(0.2)

    if gods is not None:
        gods.commit()
        total = gods.execute("SELECT COUNT(*) FROM raw_gx_ets_daily").fetchone()[0]
        gods.close()
        print(f"[DB] raw_gx_ets_daily total rows now = {total}")

    print(f"=== summary: ok={ok} (no_trade={notrade}) fail={fail} ===")
    if fail_dates:
        print(f"failed dates: {fail_dates}")


if __name__ == "__main__":
    main()

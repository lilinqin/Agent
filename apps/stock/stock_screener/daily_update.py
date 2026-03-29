#!/usr/bin/python3
"""
A股每日增量更新脚本

执行内容：
  1. 刷新所有行业 + 概念板块行情（当天涨跌、强弱、成员股价格）
  2. 对所有股票追加当天新K线（只拉最近几天，不重复拉全量）
  3. 更新新闻（可选）

建议在每个交易日收盘后（15:30 以后）运行。

用法：
  python daily_update.py              # 完整更新（板块 + K线 + 新闻）
  python daily_update.py --no-boards  # 跳过板块刷新，只追加K线
  python daily_update.py --no-news    # 跳过新闻
  python daily_update.py --stock 600519  # 只更新单只股票
"""

import akshare as ak
import time
import argparse
from datetime import datetime
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

import db
from data_updater import (
    scrape_board, calculate_strength,
    get_kline_incremental, get_stock_news,
)

MAX_WORKERS = 3  # 东财并发不能太高，否则触发SSL封禁


def refresh_boards():
    """刷新全部板块当日行情（涨跌、强弱、成员股价格）"""
    print("=" * 60)
    print("  第一步：刷新板块行情")
    print("=" * 60)

    for board_type, label in [('industry', '行业'), ('concept', '概念')]:
        boards = db.get_boards(board_type)
        if not boards:
            print(f"⚠️  {label}板块无数据，请先运行 init_all.py")
            continue

        board_names = [b['name'] for b in boards]
        print(f"\n🔄 刷新 {len(board_names)} 个{label}板块...")
        ok = 0
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(scrape_board, name, board_type): name
                for name in board_names
            }
            for future in tqdm(as_completed(futures), total=len(futures), desc=f"  {label}"):
                board_name, stocks = future.result()
                if not stocks:
                    continue
                strength, score, up, down, avg_chg = calculate_strength(stocks)
                db.upsert_board(board_name, board_type, len(stocks), strength, score,
                                up, down, round(avg_chg, 2))
                db.replace_board_stocks(board_name, board_type, stocks)
                ok += 1
        print(f"✅ {label}板块刷新: {ok} 个")


def update_klines(symbols: list):
    """增量追加当天K线（每只股只拉最近几天）"""
    print("\n" + "=" * 60)
    print(f"  第二步：增量K线更新（{len(symbols)} 只股票）")
    print("=" * 60)

    ok, fail = 0, 0
    for i, symbol in enumerate(tqdm(symbols, desc="  日K增量")):
        stock_row = db.get_stock(symbol)
        listed = stock_row.get('listed_date', '') if stock_row else ''
        klines = get_kline_incremental(symbol, listed_date=listed)
        if klines:
            ok += 1
        else:
            fail += 1

        if (i + 1) % 200 == 0:
            time.sleep(2)

    print(f"✅ K线更新完成：成功 {ok}，失败 {fail}")


def update_news(symbols: list):
    """更新新闻（每只股票最新10条）"""
    print("\n" + "=" * 60)
    print(f"  第三步：新闻更新（{len(symbols)} 只股票）")
    print("=" * 60)

    ok = 0
    for symbol in tqdm(symbols, desc="  新闻"):
        news = get_stock_news(symbol)
        if news:
            db.replace_news(symbol, news)
            ok += 1
        time.sleep(0.1)

    print(f"✅ 新闻更新: {ok} 条有新闻的股票")


def update_single(symbol: str, with_news: bool = True):
    """更新单只股票"""
    print(f"\n📈 更新 {symbol}...")
    stock_row = db.get_stock(symbol)
    listed = stock_row.get('listed_date', '') if stock_row else ''
    klines = get_kline_incremental(symbol, listed_date=listed)
    print(f"   K线: {len(klines)} 条")
    if with_news:
        news = get_stock_news(symbol)
        if news:
            db.replace_news(symbol, news)
        print(f"   新闻: {len(news)} 条")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A股每日增量更新')
    parser.add_argument('--no-boards', action='store_true', help='跳过板块刷新')
    parser.add_argument('--no-news',   action='store_true', help='跳过新闻更新')
    parser.add_argument('--stock',     type=str,            help='只更新单只股票')
    args = parser.parse_args()

    start = datetime.now()
    print(f"\n🚀 每日更新开始: {start.strftime('%Y-%m-%d %H:%M:%S')}")

    if args.stock:
        update_single(args.stock, with_news=not args.no_news)
    else:
        if not args.no_boards:
            refresh_boards()

        symbols = db.get_all_symbols()
        if not symbols:
            print("⚠️  板块数据为空，请先运行 init_all.py")
        else:
            update_klines(symbols)
            if not args.no_news:
                update_news(symbols)

    elapsed = datetime.now() - start
    print(f"\n⏱  总耗时: {elapsed}")
    print("✅ 每日更新完成！")

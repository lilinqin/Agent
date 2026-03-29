#!/usr/bin/python3
"""
A股数据初始化脚本

执行内容：
  1. 从东方财富拉取所有行业板块 + 概念板块，写入 SQLite
  2. 遍历全部股票（来自板块成员），从 AKShare 拉取从上市至今的完整日K线
  3. 写入新闻（可选，--no-news 跳过）

用法：
  python init_all.py                # 初始化全部（板块 + 全量K线 + 新闻）
  python init_all.py --no-news      # 跳过新闻，速度更快
  python init_all.py --stock 600519 # 仅初始化单只股票
  python init_all.py --boards-only  # 仅刷新板块，不拉K线

耗时估计：
  板块采集（468行业+440概念）: ~20分钟
  全量K线（~5000只 × 约20年）: ~3-5小时（受限于 AKShare 频率）
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
    get_full_kline_history, get_stock_news,
)

MAX_WORKERS = 3        # 东财并发不能太高，否则触发SSL封禁
SLEEP_BETWEEN = 0.5   # 全量K线每只间隔，避免被限流


def _fetch_with_retry(fn, desc='', waits=(10, 30, 60)):
    """带指数退避重试的调用，适用于东财接口"""
    for attempt, wait in enumerate(waits):
        try:
            return fn()
        except Exception as e:
            if attempt < len(waits) - 1:
                print(f"   {desc} 第{attempt+1}次失败，{wait}s后重试: {str(e)[-60:]}")
                time.sleep(wait)
            else:
                raise


def init_boards():
    """拉取全部行业 + 概念板块，写入 SQLite"""
    print("=" * 60)
    print("  第一步：采集行业 & 概念板块")
    print("=" * 60)

    # 行业板块
    print("\n📋 获取行业板块列表...")
    industry_df = _fetch_with_retry(ak.stock_board_industry_name_em, '行业板块列表')
    industry_names = industry_df['板块名称'].tolist()
    print(f"✅ {len(industry_names)} 个行业板块")

    print(f"\n🏭 并发采集行业板块 (workers={MAX_WORKERS})...")
    ind_ok = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(scrape_board, name, 'industry'): name for name in industry_names}
        for future in tqdm(as_completed(futures), total=len(futures), desc="  行业"):
            board_name, stocks = future.result()
            if not stocks:
                continue
            strength, score, up, down, avg_chg = calculate_strength(stocks)
            db.upsert_board(board_name, 'industry', len(stocks), strength, score,
                            up, down, round(avg_chg, 2))
            db.replace_board_stocks(board_name, 'industry', stocks)
            ind_ok += 1
    print(f"✅ 行业板块写入: {ind_ok} 个")

    # 概念板块
    print("\n📋 获取概念板块列表...")
    concept_df = _fetch_with_retry(ak.stock_board_concept_name_em, '概念板块列表')
    concept_names = concept_df['板块名称'].tolist()
    print(f"✅ {len(concept_names)} 个概念板块")

    print(f"\n💡 并发采集概念板块 (workers={MAX_WORKERS})...")
    con_ok = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(scrape_board, name, 'concept'): name for name in concept_names}
        for future in tqdm(as_completed(futures), total=len(futures), desc="  概念"):
            board_name, stocks = future.result()
            if not stocks:
                continue
            strength, score, up, down, avg_chg = calculate_strength(stocks)
            db.upsert_board(board_name, 'concept', len(stocks), strength, score,
                            up, down, round(avg_chg, 2))
            db.replace_board_stocks(board_name, 'concept', stocks)
            con_ok += 1
    print(f"✅ 概念板块写入: {con_ok} 个")
    return ind_ok, con_ok


def get_listed_date(symbol: str) -> str:
    """从东财拉取上市日期"""
    try:
        df = ak.stock_individual_info_em(symbol=symbol)
        if df is not None and not df.empty:
            for row in df.to_dict('records'):
                if '上市时间' in str(row.get('item', '')):
                    return str(row.get('value', ''))
    except Exception:
        pass
    return ''


def init_klines(symbols: list, with_news: bool = True):
    """遍历股票列表，全量拉取历史K线（从上市日至今）"""
    print("\n" + "=" * 60)
    print(f"  第二步：全量K线初始化（{len(symbols)} 只股票）")
    print("=" * 60)

    ok, skip, fail = 0, 0, 0
    for i, symbol in enumerate(tqdm(symbols, desc="  全量K线")):
        # 已有数据的跳过（支持断点续传）
        existing = db.get_klines(symbol, period='daily', limit=1)
        if existing:
            skip += 1
            continue

        listed_date = get_listed_date(symbol)
        time.sleep(0.1)  # 避免连续调用东财接口过快

        klines = get_full_kline_history(symbol, listed_date=listed_date)
        if klines:
            db.upsert_klines(symbol, klines, period='daily')
            ok += 1
        else:
            fail += 1

        # 写股票基本信息（name 从 board_stocks 里取）
        with db.get_conn() as conn:
            row = conn.execute(
                'SELECT name FROM board_stocks WHERE symbol=? LIMIT 1', (symbol,)
            ).fetchone()
            name = row['name'] if row else symbol
        db.upsert_stock(symbol, name, listed_date)

        if with_news:
            news = get_stock_news(symbol)
            if news:
                db.replace_news(symbol, news)

        # 每100只暂停一下，避免触发限流
        if (i + 1) % 100 == 0:
            print(f"\n   已处理 {i+1}/{len(symbols)}，成功 {ok}，跳过 {skip}，失败 {fail}")
            time.sleep(3)
        else:
            time.sleep(SLEEP_BETWEEN)

    print(f"\n✅ 完成！成功 {ok}，跳过（已有数据）{skip}，失败 {fail}")


def init_single(symbol: str):
    print(f"\n📈 初始化单只股票: {symbol}")
    listed_date = get_listed_date(symbol)
    print(f"   上市日期: {listed_date or '未知'}")

    klines = get_full_kline_history(symbol, listed_date=listed_date)
    if klines:
        db.upsert_klines(symbol, klines, period='daily')
        print(f"   ✅ K线写入: {len(klines)} 条（{klines[0]['date']} ~ {klines[-1]['date']}）")
    else:
        print("   ❌ K线拉取失败")

    with db.get_conn() as conn:
        row = conn.execute(
            'SELECT name FROM board_stocks WHERE symbol=? LIMIT 1', (symbol,)
        ).fetchone()
        name = row['name'] if row else symbol
    db.upsert_stock(symbol, name, listed_date)

    news = get_stock_news(symbol)
    if news:
        db.replace_news(symbol, news)
        print(f"   ✅ 新闻写入: {len(news)} 条")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A股数据初始化')
    parser.add_argument('--no-news',     action='store_true', help='跳过新闻拉取')
    parser.add_argument('--boards-only', action='store_true', help='仅刷新板块，不拉K线')
    parser.add_argument('--stock',       type=str,            help='仅初始化单只股票')
    args = parser.parse_args()

    start = datetime.now()
    print(f"\n🚀 开始时间: {start.strftime('%Y-%m-%d %H:%M:%S')}")

    if args.stock:
        init_single(args.stock)
    elif args.boards_only:
        init_boards()
    else:
        init_boards()
        symbols = db.get_all_symbols()
        print(f"\n📊 板块中共 {len(symbols)} 只股票")
        init_klines(symbols, with_news=not args.no_news)

    elapsed = datetime.now() - start
    print(f"\n⏱  总耗时: {elapsed}")

#!/usr/bin/python3
"""
从东方财富顺序拉取每只股票从上市至今的完整K线，写入SQLite。

- 顺序执行（不并发），避免限流
- 已有 > 1023 条日K的股票跳过（说明已有完整历史）
- 支持断点续传
- 重试退避：5s / 30s / 90s

用法：
  python fetch_full_history.py            # 全量
  python fetch_full_history.py --stock 600519  # 单只
"""

import akshare as ak
import time
import argparse
from datetime import datetime
from tqdm import tqdm

import db
from data_updater import get_full_kline_history

SLEEP_BETWEEN = 0.3   # 每只间隔，避免限流


def get_listed_date(symbol: str) -> str:
    try:
        df = ak.stock_individual_info_em(symbol=symbol)
        if df is not None and not df.empty:
            for row in df.to_dict('records'):
                if '上市时间' in str(row.get('item', '')):
                    return str(row.get('value', ''))
    except Exception:
        pass
    return ''


def fetch_all(symbols: list):
    print(f"\n共 {len(symbols)} 只股票，顺序拉取完整K线...\n")
    ok, skip, fail = 0, 0, 0

    for i, symbol in enumerate(tqdm(symbols, desc="东财全量K线")):
        # 已有完整历史则跳过（断点续传）
        existing = db.get_klines(symbol, period='daily', limit=1025)
        if len(existing) > 1023:
            skip += 1
            continue

        try:
            klines = get_full_kline_history(symbol, listed_date='')
            if klines:
                db.upsert_klines(symbol, klines, period='daily')
                ok += 1
            else:
                fail += 1
        except Exception as e:
            print(f"\n  [{symbol}] 异常跳过: {e}")
            fail += 1

        if (i + 1) % 100 == 0:
            print(f"\n  进度 {i+1}/{len(symbols)}  成功 {ok}  跳过 {skip}  失败 {fail}")

        time.sleep(SLEEP_BETWEEN)

    print(f"\n✅ 完成！成功 {ok}，跳过（已有完整数据）{skip}，失败 {fail}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--stock', type=str, help='只处理单只股票')
    args = parser.parse_args()

    start = datetime.now()
    print(f"🚀 开始: {start.strftime('%Y-%m-%d %H:%M:%S')}")

    if args.stock:
        listed_date = get_listed_date(args.stock)
        klines = get_full_kline_history(args.stock, listed_date=listed_date)
        if klines:
            db.upsert_klines(args.stock, klines, period='daily')
            print(f"✅ {args.stock}: {len(klines)} 条 ({klines[0]['date']} ~ {klines[-1]['date']})")
        else:
            print(f"❌ {args.stock}: 获取失败")
    else:
        symbols = db.get_all_symbols()
        fetch_all(symbols)

    print(f"⏱  耗时: {datetime.now() - start}")

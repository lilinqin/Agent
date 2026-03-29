#!/usr/bin/python3
"""
A股数据增量更新脚本（并发版本）

数据源分工：
  新浪财经  quotes.sina.cn      日K线历史（增量追加，免费稳定）
  东财妙想  AKShare stock_news_em  资讯/新闻
  AKShare   stock_board_*_em   板块成员（行业/概念）
  AKShare   stock_individual_info_em  个股上市日期

用法：
  python data_updater.py --full          # 全量刷新板块数据（写 SQLite）
  python data_updater.py --incremental   # 每日增量：只追加当天新K线
  python data_updater.py --stock 600519  # 更新单只股票
"""

import akshare as ak
import pandas as pd
import time
import json
import os
import re
import argparse
import requests
from datetime import datetime
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

import db

TODAY = datetime.now().strftime('%Y-%m-%d')

SLEEP_BETWEEN = 0.1
MAX_WORKERS = 10

SINA_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Referer': 'https://finance.sina.com.cn/',
}


# ── 股票代码转新浪格式 ─────────────────────────────────────────────────────────

def to_sina_symbol(symbol: str) -> str:
    """000001 → sz000001，600519 → sh600519"""
    if symbol.startswith('6') or symbol.startswith('9'):
        return f'sh{symbol}'
    return f'sz{symbol}'


# ── 新浪财经：K线（quotes.sina.cn）────────────────────────────────────────────

def get_sina_kline(symbol: str, scale: int = 240, datalen: int = 1023) -> list:
    """
    获取A股K线数据（新浪财经 quotes.sina.cn）
    scale: 240=日K
    返回 [{date, open, close, high, low, volume, amount, change_pct}, ...]
    """
    full_symbol = to_sina_symbol(symbol)
    url = (
        f'https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_kline='
        f'/CN_MarketDataService.getKLineData'
        f'?symbol={full_symbol}&scale={scale}&ma=no&datalen={datalen}'
    )

    for attempt in range(3):
        try:
            resp = requests.get(url, headers=SINA_HEADERS, timeout=10)
            resp.raise_for_status()
            text = resp.text.strip()

            # 跳过反爬虫脚本前缀 /*<script>...</script>*/
            script_end = text.find('*/')
            if script_end != -1:
                text = text[script_end + 2:].strip()

            if not text.startswith('var '):
                if attempt < 2:
                    time.sleep(2 * (attempt + 1))
                    continue
                return []

            start = text.find('([')
            end = text.rfind('])')
            if start == -1 or end == -1 or end <= start:
                return []

            data = json.loads(text[start + 1: end + 1])
            return [
                {
                    'date': item['day'],
                    'open': float(item.get('open', 0)),
                    'close': float(item.get('close', 0)),
                    'high': float(item.get('high', 0)),
                    'low': float(item.get('low', 0)),
                    'volume': int(item.get('volume', 0)),
                    'amount': 0.0,
                    'change_pct': 0.0,
                }
                for item in data if item.get('day')
            ]

        except (requests.RequestException, json.JSONDecodeError, ValueError, KeyError) as e:
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
            else:
                print(f"   [K线] {symbol} 获取失败: {e}")

    return []


# ── 新浪财经：实时行情（hq.sinajs.cn）────────────────────────────────────────

def get_sina_realtime(symbols: list) -> dict:
    """
    批量获取实时行情（hq.sinajs.cn，GBK编码，一次最多200只）
    返回 {symbol: {name, open, close, prev_close, high, low, volume, amount, change_pct}}
    """
    if not symbols:
        return {}

    result = {}
    batch_size = 200
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i: i + batch_size]
        sina_codes = ','.join(to_sina_symbol(s) for s in batch)
        url = f'https://hq.sinajs.cn/list={sina_codes}'
        try:
            resp = requests.get(url, headers=SINA_HEADERS, timeout=10)
            resp.raise_for_status()
            text = resp.content.decode('gbk', errors='replace')

            for line in text.strip().split(';'):
                line = line.strip()
                if not line:
                    continue
                m = re.match(r'var hq_str_(\w+)="(.+)"', line)
                if not m:
                    continue
                code = m.group(1)
                fields = m.group(2).split(',')
                if len(fields) < 32:
                    continue

                sym = code[2:]
                prev_close = float(fields[2]) if fields[2] else 0
                close = float(fields[3]) if fields[3] else 0
                change_pct = round((close - prev_close) / prev_close * 100, 2) if prev_close else 0

                result[sym] = {
                    'symbol': sym,
                    'name': fields[0],
                    'open': float(fields[1]) if fields[1] else 0,
                    'prev_close': prev_close,
                    'close': close,
                    'high': float(fields[4]) if fields[4] else 0,
                    'low': float(fields[5]) if fields[5] else 0,
                    'volume': int(float(fields[8])) if fields[8] else 0,
                    'amount': float(fields[9]) if fields[9] else 0,
                    'change_pct': change_pct,
                }
        except Exception as e:
            print(f"   [实时] 批次 {i//batch_size+1} 获取失败: {e}")

    return result


# ── 东财妙想（AKShare）：板块成员 ─────────────────────────────────────────────

def scrape_board(board_name: str, board_type: str = 'industry'):
    """获取板块成分股（含实时涨跌数据）"""
    try:
        if board_type == 'industry':
            df = ak.stock_board_industry_cons_em(symbol=board_name)
        else:
            df = ak.stock_board_concept_cons_em(symbol=board_name)

        if df is None or df.empty:
            return board_name, []

        stocks = []
        for _, row in df.iterrows():
            stocks.append({
                'symbol': str(row.get('代码', '')).zfill(6),
                'name': str(row.get('名称', '')),
                'close': float(row.get('最新价', 0)) if pd.notna(row.get('最新价')) else 0,
                'change_pct': float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else 0,
                'volume': int(row.get('成交量', 0)) if pd.notna(row.get('成交量')) else 0,
                'turnover': float(row.get('换手率', 0)) if pd.notna(row.get('换手率')) else 0,
            })

        time.sleep(SLEEP_BETWEEN)
        return board_name, stocks
    except Exception:
        time.sleep(SLEEP_BETWEEN)
        return board_name, []


def calculate_strength(stocks: list):
    if not stocks:
        return '中性', 50, 0, 0, 0.0
    total = len(stocks)
    up = sum(1 for s in stocks if s.get('change_pct', 0) > 0)
    down = sum(1 for s in stocks if s.get('change_pct', 0) < 0)
    avg = sum(s.get('change_pct', 0) for s in stocks) / total
    ratio = up / total
    if avg > 2 and ratio > 0.7:
        return '强势', 85, up, down, avg
    elif avg > 0.5 and ratio > 0.55:
        return '偏强', 65, up, down, avg
    elif avg < -2 and ratio < 0.3:
        return '弱势', 20, up, down, avg
    elif avg < -0.5 and ratio < 0.45:
        return '偏弱', 35, up, down, avg
    return '中性', 50, up, down, avg


# ── AKShare（东方财富）：全量K线历史（首次入库用）────────────────────────────────

def get_full_kline_history(symbol: str, listed_date: str, period: str = 'daily') -> list:
    """从上市日期拉取全量历史K线（AKShare / 东方财富），内置指数退避重试"""
    ak_period = {'daily': 'daily', 'weekly': 'weekly', 'monthly': 'monthly'}.get(period, 'daily')
    start = listed_date.replace('-', '') if listed_date else '19900101'
    end = datetime.now().strftime('%Y%m%d')

    waits = [5, 30, 90]  # 指数退避：5s、30s、90s
    for attempt, wait in enumerate(waits):
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol, period=ak_period,
                start_date=start, end_date=end, adjust='qfq'
            )
            if df is None or df.empty:
                return []
            return [
                {
                    'date': str(row.get('日期', '')),
                    'open': float(row.get('开盘', 0)),
                    'close': float(row.get('收盘', 0)),
                    'high': float(row.get('最高', 0)),
                    'low': float(row.get('最低', 0)),
                    'volume': int(row.get('成交量', 0)),
                    'amount': float(row.get('成交额', 0)),
                    'change_pct': float(row.get('涨跌幅', 0)),
                }
                for _, row in df.iterrows() if row.get('日期')
            ]
        except Exception as e:
            err = str(e)
            if attempt < len(waits) - 1:
                print(f"   [全量K线] {symbol} 第{attempt+1}次失败，{wait}s后重试: {err[-60:]}")
                time.sleep(wait)
            else:
                print(f"   [全量K线] {symbol} 放弃: {err[-60:]}")
    return []


def get_kline_incremental(symbol: str, listed_date: str = '') -> list:
    """
    智能日K线获取：
    - DB 无数据  → 新浪拉近4年数据（1023根日K）
    - DB 有数据  → 新浪只拉「上次最新日期」之后的新K线并追加
    INSERT OR REPLACE 天然去重，幂等安全
    """
    existing = db.get_klines(symbol, period='daily', limit=1)
    if not existing:
        klines = get_sina_kline(symbol, scale=240, datalen=1023)
        if klines:
            db.upsert_klines(symbol, klines, period='daily')
        return klines

    last_date = existing[-1]['date']
    from datetime import datetime as _dt
    try:
        days_since = (_dt.now() - _dt.strptime(last_date, '%Y-%m-%d')).days
    except ValueError:
        days_since = 7
    datalen = max(7, days_since + 5)

    klines = get_sina_kline(symbol, scale=240, datalen=datalen)
    if klines:
        db.upsert_klines(symbol, klines, period='daily')
    return klines


# ── 东财妙想（AKShare）：新闻 ─────────────────────────────────────────────────

def get_stock_news(symbol: str) -> list:
    news = []
    try:
        df = ak.stock_news_em(symbol=symbol)
        if df is not None and not df.empty:
            for _, row in df.head(10).iterrows():
                news.append({
                    'type': 'stock',
                    'source': '',
                    'title': str(row.get('新闻标题', '')),
                    'pub_date': str(row.get('发布时间', '')),
                    'url': str(row.get('新闻链接', '')),
                })
    except Exception:
        pass
    return news


# ── 全量刷新板块数据（写 SQLite）─────────────────────────────────────────────

def full_refresh():
    print("=" * 60)
    print("  A股数据全量刷新（SQLite）")
    print("=" * 60)

    # 1. 行业板块
    print("\n📋 获取行业板块列表...")
    try:
        industry_df = ak.stock_board_industry_name_em()
        industry_names = industry_df['板块名称'].tolist()
    except Exception as e:
        print(f"❌ 失败: {e}")
        return
    print(f"✅ {len(industry_names)} 个行业板块")

    print(f"\n🏭 并发采集行业板块 (workers={MAX_WORKERS})...")
    industry_count = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(scrape_board, name, 'industry'): name for name in industry_names}
        for future in tqdm(as_completed(futures), total=len(futures), desc="  行业板块"):
            board_name, stocks = future.result()
            if not stocks:
                continue
            strength, score, up, down, avg_chg = calculate_strength(stocks)
            db.upsert_board(board_name, 'industry', len(stocks), strength, score,
                            up, down, round(avg_chg, 2))
            db.replace_board_stocks(board_name, 'industry', stocks)
            industry_count += 1

    print(f"✅ 行业板块已写入: {industry_count} 个")

    # 2. 概念板块
    print("\n📋 获取概念板块列表...")
    try:
        concept_df = ak.stock_board_concept_name_em()
        concept_names = concept_df['板块名称'].tolist()
    except Exception as e:
        print(f"❌ 失败: {e}")
        concept_names = []
    print(f"✅ {len(concept_names)} 个概念板块")

    print(f"\n💡 并发采集概念板块 (workers={MAX_WORKERS})...")
    concept_count = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(scrape_board, name, 'concept'): name for name in concept_names}
        for future in tqdm(as_completed(futures), total=len(futures), desc="  概念板块"):
            board_name, stocks = future.result()
            if not stocks:
                continue
            strength, score, up, down, avg_chg = calculate_strength(stocks)
            db.upsert_board(board_name, 'concept', len(stocks), strength, score,
                            up, down, round(avg_chg, 2))
            db.replace_board_stocks(board_name, 'concept', stocks)
            concept_count += 1

    print(f"✅ 概念板块已写入: {concept_count} 个")
    print("\n" + "=" * 60)
    print(f"  全量刷新完成！行业 {industry_count} 个 / 概念 {concept_count} 个")
    print("=" * 60)


# ── 单只股票详情更新 ──────────────────────────────────────────────────────────

def update_stock_detail(symbol: str):
    # 上市日期（东财）
    listed_date = ''
    try:
        df = ak.stock_individual_info_em(symbol=symbol)
        if df is not None and not df.empty:
            for row in df.to_dict('records'):
                if '上市时间' in str(row.get('item', '')):
                    listed_date = str(row.get('value', ''))
                    break
    except Exception:
        pass

    # 从 board_stocks 查 name
    boards = db.get_symbol_boards(symbol)
    name = symbol
    with db.get_conn() as conn:
        row = conn.execute(
            'SELECT name FROM board_stocks WHERE symbol=? LIMIT 1', (symbol,)
        ).fetchone()
        if row:
            name = row['name']

    # K线增量
    daily_klines = get_kline_incremental(symbol, listed_date=listed_date)

    # 新闻
    news = get_stock_news(symbol)
    db.replace_news(symbol, news)

    # 写股票基本信息
    db.upsert_stock(symbol, name, listed_date)

    return {
        'symbol': symbol, 'name': name,
        'klines': len(daily_klines), 'news': len(news),
        'industries': len(boards['industries']),
        'concepts': len(boards['concepts']),
    }


# ── 增量更新所有股票 ──────────────────────────────────────────────────────────

def incremental_update():
    print("=" * 60)
    print("  A股数据增量更新（SQLite）")
    print("=" * 60)

    symbols = db.get_all_symbols()
    print(f"\n📊 共 {len(symbols)} 只股票（来自板块数据）")

    for i, symbol in enumerate(tqdm(symbols, desc="  日K增量")):
        # 上市日期从 stocks 表取（如果有）
        stock_row = db.get_stock(symbol)
        listed = stock_row.get('listed_date', '') if stock_row else ''
        get_kline_incremental(symbol, listed_date=listed)

        news = get_stock_news(symbol)
        db.replace_news(symbol, news)

        if (i + 1) % 100 == 0:
            time.sleep(2)

    print("\n" + "=" * 60)
    print(f"  增量更新完成！{len(symbols)} 只股票")
    print("=" * 60)


def update_single_stock(symbol: str):
    print(f"\n📈 更新股票: {symbol}")
    result = update_stock_detail(symbol)
    print(f"✅ {result['name']} 更新完成 | K线 {result['klines']} 条 | 新闻 {result['news']} 条")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--full', action='store_true', help='全量刷新板块数据')
    parser.add_argument('--incremental', action='store_true', help='增量更新股票详情')
    parser.add_argument('--stock', type=str, help='更新单只股票')
    args = parser.parse_args()

    if args.stock:
        update_single_stock(args.stock)
    elif args.full:
        full_refresh()
    elif args.incremental:
        incremental_update()
    else:
        full_refresh()

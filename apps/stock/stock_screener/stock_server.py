#!/usr/bin/python3
"""
股票数据 HTTP 服务

数据源分工：
  新浪财经  hq.sinajs.cn        实时行情（免费稳定，GBK编码）
  新浪财经  quotes.sina.cn      K线历史（日K，增量追加）
  东财妙想  AKShare stock_news_em  资讯/新闻
  AKShare   stock_individual_info_em  个股基本信息
  SQLite    stocks.db           所有数据（K线/板块/新闻）

启动: python stock_server.py
访问: http://localhost:5000/api/stock/000001
"""

from flask import Flask, jsonify, request
import akshare as ak
import json
import re
import time
import requests
from datetime import datetime
from functools import wraps

import db

app = Flask(__name__)

SINA_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Referer': 'https://finance.sina.com.cn/',
}


# ── 新浪财经：实时行情（hq.sinajs.cn）────────────────────────────────────────

def get_sina_realtime(symbol: str) -> dict | None:
    """获取单只股票实时行情（先查 SQLite，过期则从新浪拉取）"""
    cached = db.get_realtime(symbol)
    if cached:
        updated = datetime.strptime(cached['updated_at'], '%Y-%m-%d %H:%M:%S')
        if (datetime.now() - updated).seconds < 300:
            return cached

    if symbol.startswith('6') or symbol.startswith('9'):
        sina_code = f'sh{symbol}'
    else:
        sina_code = f'sz{symbol}'

    try:
        resp = requests.get(f'https://hq.sinajs.cn/list={sina_code}',
                            headers=SINA_HEADERS, timeout=8)
        resp.raise_for_status()
        text = resp.content.decode('gbk', errors='replace')

        m = re.search(r'var hq_str_\w+="(.+)"', text)
        if not m:
            return cached
        fields = m.group(1).split(',')
        if len(fields) < 32:
            return cached

        prev_close = float(fields[2]) if fields[2] else 0
        close = float(fields[3]) if fields[3] else 0
        change_pct = round((close - prev_close) / prev_close * 100, 2) if prev_close else 0

        data = {
            'symbol': symbol,
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
        db.upsert_realtime(data)
        return data
    except Exception as e:
        print(f"Realtime error {symbol}: {e}")
        return cached


# ── 周K/月K：从日K聚合 ───────────────────────────────────────────────────────

def _aggregate(daily: list, key_fn) -> list:
    from collections import OrderedDict
    groups = OrderedDict()
    for k in daily:
        key = key_fn(k['date'])
        groups.setdefault(key, []).append(k)
    result = []
    for bars in groups.values():
        result.append({
            'date': bars[0]['date'],
            'open': bars[0]['open'],
            'close': bars[-1]['close'],
            'high': max(b['high'] for b in bars),
            'low': min(b['low'] for b in bars),
            'volume': sum(b['volume'] for b in bars),
            'amount': sum(b.get('amount', 0) for b in bars),
            'change_pct': round(
                (bars[-1]['close'] - bars[0]['open']) / bars[0]['open'] * 100, 2
            ) if bars[0]['open'] else 0.0,
        })
    return result


def _week_key(date_str: str) -> str:
    from datetime import datetime, timedelta
    d = datetime.strptime(date_str, '%Y-%m-%d')
    monday = d - timedelta(days=d.weekday())
    return monday.strftime('%Y-%m-%d')


def aggregate_weekly(daily: list) -> list:
    return _aggregate(daily, _week_key)


def aggregate_monthly(daily: list) -> list:
    return _aggregate(daily, lambda d: d[:7])


# ── 技术指标计算 ──────────────────────────────────────────────────────────────

def calculate_ma(klines: list, periods: list) -> dict:
    if not klines:
        return {p: None for p in periods}
    closes = [k['close'] for k in klines]
    return {
        p: round(sum(closes[-p:]) / p, 2) if len(closes) >= p else None
        for p in periods
    }


def calculate_kdj(klines: list, n: int = 9) -> dict:
    if not klines or len(klines) < n:
        return {'k': None, 'd': None, 'j': None}
    lows = [k['low'] for k in klines]
    highs = [k['high'] for k in klines]
    closes = [k['close'] for k in klines]
    k_vals, d_vals = [50.0], [50.0]
    for i in range(len(closes)):
        if i < n - 1:
            continue
        lo = min(lows[i - n + 1: i + 1])
        hi = max(highs[i - n + 1: i + 1])
        rsv = (closes[i] - lo) / (hi - lo) * 100 if hi != lo else 50
        k = 2 / 3 * k_vals[-1] + 1 / 3 * rsv
        d = 2 / 3 * d_vals[-1] + 1 / 3 * k
        k_vals.append(k)
        d_vals.append(d)
    return {
        'k': round(k_vals[-1], 2),
        'd': round(d_vals[-1], 2),
        'j': round(3 * k_vals[-1] - 2 * d_vals[-1], 2),
    }


# ── 基本信息 ──────────────────────────────────────────────────────────────────

def get_stock_profile(symbol: str) -> dict:
    """读 stocks 表基本信息，industries/concepts 从 board_stocks 查"""
    cached = db.get_stock(symbol)
    boards = db.get_symbol_boards(symbol)

    result = {
        'symbol': symbol,
        'name': symbol,
        'listed_date': '',
        'industries': boards['industries'],
        'concepts': boards['concepts'],
    }

    if cached:
        result['name'] = cached.get('name', symbol)
        result['listed_date'] = cached.get('listed_date', '')
        return result

    # 没有缓存，从东财拉取
    try:
        df = ak.stock_individual_info_em(symbol=symbol)
        if df is not None and not df.empty:
            for row in df.to_dict('records'):
                item = str(row.get('item', ''))
                val = str(row.get('value', ''))
                if '股票简称' in item:
                    result['name'] = val
                elif '上市时间' in item:
                    result['listed_date'] = val
    except Exception as e:
        print(f"Profile error {symbol}: {e}")

    # 从 board_stocks 补充 name（如果东财没拿到）
    if result['name'] == symbol:
        with db.get_conn() as conn:
            row = conn.execute(
                'SELECT name FROM board_stocks WHERE symbol=? LIMIT 1', (symbol,)
            ).fetchone()
            if row:
                result['name'] = row['name']

    db.upsert_stock(symbol, result['name'], result['listed_date'])
    return result


# ── API 路由 ──────────────────────────────────────────────────────────────────

@app.route('/api/stock/<symbol>', methods=['GET'])
def get_stock(symbol):
    profile = get_stock_profile(symbol)
    listed_date = profile.get('listed_date', '')
    industries = profile.get('industries', [])
    concepts = profile.get('concepts', [])

    daily_klines = db.get_klines(symbol, period='daily', limit=99999)
    if not daily_klines:
        from data_updater import get_sina_kline
        daily_klines = get_sina_kline(symbol, scale=240, datalen=1023)
        if daily_klines:
            db.upsert_klines(symbol, daily_klines, period='daily')

    weekly_klines  = aggregate_weekly(daily_klines)
    monthly_klines = aggregate_monthly(daily_klines)

    daily_ma   = calculate_ma(daily_klines,   [5, 10, 20, 30, 60, 120, 250])
    weekly_ma  = calculate_ma(weekly_klines,  [5, 10, 20, 30])
    monthly_ma = calculate_ma(monthly_klines, [5, 10, 20, 30])
    daily_kdj   = calculate_kdj(daily_klines)
    weekly_kdj  = calculate_kdj(weekly_klines)
    monthly_kdj = calculate_kdj(monthly_klines)

    return jsonify({
        'status': 'ok',
        'symbol': symbol,
        'name': profile.get('name', symbol),
        'listed_date': listed_date,
        'industries': industries,
        'concepts': concepts,
        'klines': {
            'daily':   daily_klines,
            'weekly':  weekly_klines,
            'monthly': monthly_klines,
        },
        'indicators': {
            'daily':   {'ma': daily_ma,   'kdj': daily_kdj},
            'weekly':  {'ma': weekly_ma,  'kdj': weekly_kdj},
            'monthly': {'ma': monthly_ma, 'kdj': monthly_kdj},
        },
        'updated_at': datetime.now().strftime('%Y-%m-%d'),
    })


@app.route('/api/boards', methods=['GET'])
def get_boards():
    board_type = request.args.get('type', 'industry')
    boards = db.get_boards(board_type)
    updated_at = db.get_boards_updated_at(board_type)
    return jsonify({
        'status': 'ok',
        'type': board_type,
        'count': len(boards),
        'updated_at': updated_at,
        'items': boards,
    })


@app.route('/api/boards/<board_type>/<path:board_name>', methods=['GET'])
def get_board_detail(board_type, board_name):
    boards = db.get_boards(board_type)
    board = next((b for b in boards if b['name'] == board_name), None)
    if not board:
        return jsonify({'status': 'not_found'}), 404

    stocks = db.get_board_stocks(board_name, board_type)
    return jsonify({
        'status': 'ok',
        'name': board_name,
        'type': board_type,
        'total_stocks': board['total_stocks'],
        'strength': board['strength'],
        'strength_score': board['strength_score'],
        'up_count': board['up_count'],
        'down_count': board['down_count'],
        'avg_change': board['avg_change'],
        'updated_at': board['updated_at'],
        'stocks': stocks,
    })


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    print("=" * 50)
    print("  股票数据服务启动中...")
    print("  访问: http://localhost:5000/api/stock/000001")
    print("  板块: http://localhost:5000/api/boards?type=industry")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)

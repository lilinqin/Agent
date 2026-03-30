#!/usr/bin/python3
"""
SQLite 数据库层
存储：股票基本信息、K线、实时行情、新闻、板块（行业/概念）及成员股
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '../stock-analyzer/data/stocks.db')


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_conn() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS stocks (
                symbol      TEXT PRIMARY KEY,
                name        TEXT,
                listed_date TEXT,
                updated_at  TEXT
            );

            CREATE TABLE IF NOT EXISTS klines (
                symbol      TEXT NOT NULL,
                period      TEXT NOT NULL DEFAULT 'daily',
                date        TEXT NOT NULL,
                open        REAL,
                close       REAL,
                high        REAL,
                low         REAL,
                volume      INTEGER,
                amount      REAL,
                change_pct  REAL,
                PRIMARY KEY (symbol, period, date)
            );
            CREATE INDEX IF NOT EXISTS idx_klines_symbol_period ON klines(symbol, period);

            CREATE TABLE IF NOT EXISTS realtime (
                symbol      TEXT PRIMARY KEY,
                name        TEXT,
                open        REAL,
                close       REAL,
                prev_close  REAL,
                high        REAL,
                low         REAL,
                volume      INTEGER,
                amount      REAL,
                change_pct  REAL,
                updated_at  TEXT
            );

            CREATE TABLE IF NOT EXISTS news (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol      TEXT,
                type        TEXT,
                source      TEXT,
                title       TEXT,
                pub_date    TEXT,
                url         TEXT,
                created_at  TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_news_symbol ON news(symbol);

            CREATE TABLE IF NOT EXISTS boards (
                name           TEXT NOT NULL,
                type           TEXT NOT NULL,
                total_stocks   INTEGER,
                strength       TEXT,
                strength_score INTEGER,
                up_count       INTEGER,
                down_count     INTEGER,
                avg_change     REAL,
                fund_inflow    REAL,
                amount         REAL,
                rank_in_type   TEXT,
                description    TEXT,
                updated_at     TEXT,
                PRIMARY KEY (name, type)
            );
            CREATE INDEX IF NOT EXISTS idx_boards_type ON boards(type);

            CREATE TABLE IF NOT EXISTS stock_profiles (
                symbol          TEXT PRIMARY KEY,
                total_shares    REAL,
                float_shares    REAL,
                total_market_cap  REAL,
                float_market_cap  REAL,
                industry        TEXT,
                updated_at      TEXT
            );

            CREATE TABLE IF NOT EXISTS board_stocks (
                board_name  TEXT NOT NULL,
                board_type  TEXT NOT NULL,
                symbol      TEXT NOT NULL,
                name        TEXT,
                close       REAL,
                change_pct  REAL,
                volume      INTEGER,
                turnover    REAL,
                PRIMARY KEY (board_name, board_type, symbol)
            );
            CREATE INDEX IF NOT EXISTS idx_board_stocks_symbol ON board_stocks(symbol);
            CREATE INDEX IF NOT EXISTS idx_board_stocks_board ON board_stocks(board_name, board_type);
        ''')


# ── stocks ────────────────────────────────────────────────────────────────────

def upsert_stock(symbol, name, listed_date):
    with get_conn() as conn:
        conn.execute('''
            INSERT INTO stocks (symbol, name, listed_date, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                name=excluded.name,
                listed_date=excluded.listed_date,
                updated_at=excluded.updated_at
        ''', (symbol, name, listed_date, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))


def get_stock(symbol):
    with get_conn() as conn:
        row = conn.execute('SELECT * FROM stocks WHERE symbol=?', (symbol,)).fetchone()
        return dict(row) if row else None


# ── klines ────────────────────────────────────────────────────────────────────

def upsert_klines(symbol, klines, period='daily'):
    """批量写入K线，INSERT OR REPLACE 幂等安全"""
    if not klines:
        return
    with get_conn() as conn:
        conn.executemany('''
            INSERT OR REPLACE INTO klines
                (symbol, period, date, open, close, high, low, volume, amount, change_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
            (symbol, period, k['date'], k['open'], k['close'],
             k['high'], k['low'], k['volume'], k.get('amount', 0), k.get('change_pct', 0))
            for k in klines if k.get('date')
        ])


def get_klines(symbol, period='daily', limit=1023):
    with get_conn() as conn:
        rows = conn.execute('''
            SELECT date, open, close, high, low, volume, amount, change_pct
            FROM klines WHERE symbol=? AND period=?
            ORDER BY date DESC LIMIT ?
        ''', (symbol, period, limit)).fetchall()
        return [dict(r) for r in reversed(rows)]


# ── realtime ──────────────────────────────────────────────────────────────────

def upsert_realtime(data: dict):
    """data: {symbol, name, open, close, prev_close, high, low, volume, amount, change_pct}"""
    with get_conn() as conn:
        conn.execute('''
            INSERT INTO realtime
                (symbol, name, open, close, prev_close, high, low, volume, amount, change_pct, updated_at)
            VALUES (:symbol, :name, :open, :close, :prev_close, :high, :low, :volume, :amount, :change_pct, :updated_at)
            ON CONFLICT(symbol) DO UPDATE SET
                name=excluded.name, open=excluded.open, close=excluded.close,
                prev_close=excluded.prev_close, high=excluded.high, low=excluded.low,
                volume=excluded.volume, amount=excluded.amount,
                change_pct=excluded.change_pct, updated_at=excluded.updated_at
        ''', {**data, 'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})


def get_realtime(symbol):
    with get_conn() as conn:
        row = conn.execute('SELECT * FROM realtime WHERE symbol=?', (symbol,)).fetchone()
        return dict(row) if row else None


# ── news ──────────────────────────────────────────────────────────────────────

def replace_news(symbol, news_list):
    with get_conn() as conn:
        conn.execute('DELETE FROM news WHERE symbol=?', (symbol,))
        if news_list:
            conn.executemany('''
                INSERT INTO news (symbol, type, source, title, pub_date, url, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', [
                (symbol, n.get('type', ''), n.get('source', ''),
                 n.get('title', ''), n.get('pub_date', ''), n.get('url', ''),
                 datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                for n in news_list
            ])


def get_news(symbol, limit=20):
    with get_conn() as conn:
        rows = conn.execute('''
            SELECT type, source, title, pub_date, url
            FROM news WHERE symbol=? ORDER BY pub_date DESC LIMIT ?
        ''', (symbol, limit)).fetchall()
        return [dict(r) for r in rows]


# ── boards ────────────────────────────────────────────────────────────────────

def upsert_board(name, board_type, total_stocks, strength, strength_score,
                 up_count, down_count, avg_change):
    with get_conn() as conn:
        conn.execute('''
            INSERT INTO boards
                (name, type, total_stocks, strength, strength_score,
                 up_count, down_count, avg_change, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name, type) DO UPDATE SET
                total_stocks=excluded.total_stocks,
                strength=excluded.strength,
                strength_score=excluded.strength_score,
                up_count=excluded.up_count,
                down_count=excluded.down_count,
                avg_change=excluded.avg_change,
                updated_at=excluded.updated_at
        ''', (name, board_type, total_stocks, strength, strength_score,
              up_count, down_count, avg_change,
              datetime.now().strftime('%Y-%m-%d %H:%M:%S')))


def replace_board_stocks(board_name, board_type, stocks):
    """upsert 板块成员股，不删除历史数据"""
    if not stocks:
        return
    with get_conn() as conn:
        conn.executemany('''
            INSERT INTO board_stocks
                (board_name, board_type, symbol, name, close, change_pct, volume, turnover)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(board_name, board_type, symbol) DO UPDATE SET
                name=excluded.name,
                close=excluded.close,
                change_pct=excluded.change_pct,
                volume=excluded.volume,
                turnover=excluded.turnover
        ''', [
            (board_name, board_type, s.get('symbol', ''), s.get('name', ''),
             s.get('close', 0), s.get('change_pct', 0),
             s.get('volume', 0), s.get('turnover', 0))
            for s in stocks if s.get('symbol')
        ])


def get_boards(board_type):
    """返回某类型所有板块的统计信息，按 strength_score 降序"""
    with get_conn() as conn:
        rows = conn.execute('''
            SELECT name, type, total_stocks, strength, strength_score,
                   up_count, down_count, avg_change, updated_at
            FROM boards WHERE type=?
            ORDER BY strength_score DESC
        ''', (board_type,)).fetchall()
        return [dict(r) for r in rows]


def get_board_stocks(board_name, board_type):
    """返回某板块的成员股列表"""
    with get_conn() as conn:
        rows = conn.execute('''
            SELECT symbol, name, close, change_pct, volume, turnover
            FROM board_stocks WHERE board_name=? AND board_type=?
            ORDER BY ABS(change_pct) DESC
        ''', (board_name, board_type)).fetchall()
        return [dict(r) for r in rows]


def get_symbol_boards(symbol):
    """返回某只股票所属的所有行业和概念"""
    with get_conn() as conn:
        rows = conn.execute('''
            SELECT board_name, board_type
            FROM board_stocks WHERE symbol=?
        ''', (symbol,)).fetchall()
    industries = [r['board_name'] for r in rows if r['board_type'] == 'industry']
    concepts   = [r['board_name'] for r in rows if r['board_type'] == 'concept']
    return {'industries': industries, 'concepts': concepts}


def get_all_symbols():
    """返回 board_stocks 中所有不重复的股票代码"""
    with get_conn() as conn:
        rows = conn.execute(
            'SELECT DISTINCT symbol FROM board_stocks ORDER BY symbol'
        ).fetchall()
        return [r['symbol'] for r in rows]


def get_boards_updated_at(board_type):
    """返回某类型板块的最新更新时间"""
    with get_conn() as conn:
        row = conn.execute(
            'SELECT MAX(updated_at) as t FROM boards WHERE type=?', (board_type,)
        ).fetchone()
        return row['t'] if row else None


# ── stock_profiles ────────────────────────────────────────────────────────────

def upsert_stock_profile(symbol, total_shares, float_shares,
                         total_market_cap, float_market_cap, industry):
    with get_conn() as conn:
        conn.execute('''
            INSERT INTO stock_profiles
                (symbol, total_shares, float_shares, total_market_cap,
                 float_market_cap, industry, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                total_shares=excluded.total_shares,
                float_shares=excluded.float_shares,
                total_market_cap=excluded.total_market_cap,
                float_market_cap=excluded.float_market_cap,
                industry=excluded.industry,
                updated_at=excluded.updated_at
        ''', (symbol, total_shares, float_shares, total_market_cap,
              float_market_cap, industry,
              datetime.now().strftime('%Y-%m-%d %H:%M:%S')))


def get_stock_profile(symbol):
    with get_conn() as conn:
        row = conn.execute(
            'SELECT * FROM stock_profiles WHERE symbol=?', (symbol,)
        ).fetchone()
        return dict(row) if row else None


# ── board extra info ───────────────────────────────────────────────────────────

def update_board_extra(name, board_type, fund_inflow=None, amount=None,
                       rank_in_type=None, description=None):
    with get_conn() as conn:
        conn.execute('''
            UPDATE boards SET
                fund_inflow=COALESCE(?, fund_inflow),
                amount=COALESCE(?, amount),
                rank_in_type=COALESCE(?, rank_in_type),
                description=COALESCE(?, description),
                updated_at=?
            WHERE name=? AND type=?
        ''', (fund_inflow, amount, rank_in_type, description,
              datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
              name, board_type))


init_db()

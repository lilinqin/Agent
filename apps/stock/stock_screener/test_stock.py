#!/usr/bin/python3
"""
TDD 测试：新浪财经 API + SQLite 数据库层

RED → GREEN → REFACTOR
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# 让 db 使用临时数据库，避免污染正式数据
_tmp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
_tmp_db.close()
os.environ['STOCK_DB_PATH'] = _tmp_db.name

# 重新导入以使用临时路径
import importlib
import db as _db_module
_db_module.DB_PATH = _tmp_db.name
_db_module.init_db()

import db
from data_updater import get_sina_kline, get_sina_realtime, to_sina_symbol, get_full_kline_history, get_kline_incremental


# ══════════════════════════════════════════════════════════════════════════════
# 辅助：构造新浪 K 线响应体
# ══════════════════════════════════════════════════════════════════════════════

def make_kline_response(items, with_script_prefix=True):
    """构造 quotes.sina.cn 的响应文本"""
    payload = json.dumps(items)
    body = f'var _kline=({payload});'
    if with_script_prefix:
        return f"/*<script>location.href='//sina.com';</script>*/{body}"
    return body


SAMPLE_KLINES = [
    {'day': '2026-03-25', 'open': '1410.11', 'high': '1417.87', 'low': '1401.01', 'close': '1410.27', 'volume': '2609346'},
    {'day': '2026-03-26', 'open': '1409.00', 'high': '1413.90', 'low': '1400.30', 'close': '1401.18', 'volume': '2309289'},
    {'day': '2026-03-27', 'open': '1400.00', 'high': '1426.00', 'low': '1396.66', 'close': '1416.02', 'volume': '3008711'},
]

SAMPLE_REALTIME_GBK = (
    'var hq_str_sh600519="贵州茅台,1400.000,1401.180,1416.020,1426.000,1396.660,'
    '1416.020,1416.100,3008711,4257499781.000,'
    '722,1416.020,300,1416.010,2500,1416.000,1200,1415.990,500,1415.980,'
    '100,1416.100,100,1416.340,200,1416.420,200,1416.640,100,1416.650,'
    '2026-03-27,15:00:03,00,";'
)


# ══════════════════════════════════════════════════════════════════════════════
# to_sina_symbol
# ══════════════════════════════════════════════════════════════════════════════

class TestToSinaSymbol(unittest.TestCase):

    def test_sh_prefix_for_600_stocks(self):
        self.assertEqual(to_sina_symbol('600519'), 'sh600519')

    def test_sh_prefix_for_900_stocks(self):
        self.assertEqual(to_sina_symbol('900941'), 'sh900941')

    def test_sz_prefix_for_000_stocks(self):
        self.assertEqual(to_sina_symbol('000001'), 'sz000001')

    def test_sz_prefix_for_300_stocks(self):
        self.assertEqual(to_sina_symbol('300750'), 'sz300750')

    def test_sz_prefix_for_002_stocks(self):
        self.assertEqual(to_sina_symbol('002415'), 'sz002415')


# ══════════════════════════════════════════════════════════════════════════════
# get_sina_kline - 解析
# ══════════════════════════════════════════════════════════════════════════════

class TestGetSinaKlineParsing(unittest.TestCase):

    def _mock_get(self, text, status=200):
        resp = MagicMock()
        resp.text = text
        resp.status_code = status
        resp.raise_for_status = MagicMock()
        return resp

    def test_parses_response_with_script_prefix(self):
        """带脚本前缀的响应能正确解析出K线数据"""
        text = make_kline_response(SAMPLE_KLINES, with_script_prefix=True)
        with patch('data_updater.requests.get', return_value=self._mock_get(text)):
            result = get_sina_kline('600519', scale=240, datalen=3)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['date'], '2026-03-25')
        self.assertAlmostEqual(result[2]['close'], 1416.02)

    def test_parses_response_without_script_prefix(self):
        """无脚本前缀的响应（直接返回 var）也能正确解析"""
        text = make_kline_response(SAMPLE_KLINES, with_script_prefix=False)
        with patch('data_updater.requests.get', return_value=self._mock_get(text)):
            result = get_sina_kline('600519', scale=240, datalen=3)
        self.assertEqual(len(result), 3)

    def test_returns_empty_when_only_script_redirect(self):
        """仅返回脚本重定向（无数据）时，重试后返回空列表"""
        redirect_only = "/*<script>location.href='//sina.com';</script>*/"
        with patch('data_updater.requests.get', return_value=self._mock_get(redirect_only)), \
             patch('data_updater.time.sleep'):
            result = get_sina_kline('600519', scale=240, datalen=3)
        self.assertEqual(result, [])

    def test_returns_empty_on_network_error(self):
        """网络异常时返回空列表，不抛出"""
        import requests as req
        with patch('data_updater.requests.get', side_effect=req.exceptions.ConnectionError('timeout')), \
             patch('data_updater.time.sleep'):
            result = get_sina_kline('600519', scale=240, datalen=3)
        self.assertEqual(result, [])

    def test_kline_fields_are_correct_types(self):
        """K线字段类型正确（date=str, close=float, volume=int）"""
        text = make_kline_response(SAMPLE_KLINES, with_script_prefix=True)
        with patch('data_updater.requests.get', return_value=self._mock_get(text)):
            result = get_sina_kline('600519', scale=240, datalen=3)
        k = result[0]
        self.assertIsInstance(k['date'], str)
        self.assertIsInstance(k['close'], float)
        self.assertIsInstance(k['volume'], int)
        self.assertIn('open', k)
        self.assertIn('high', k)
        self.assertIn('low', k)

    def test_retries_on_redirect_then_succeeds(self):
        """第一次返回重定向，第二次返回正常数据时，最终成功"""
        redirect = "/*<script>location.href='//sina.com';</script>*/"
        good = make_kline_response(SAMPLE_KLINES, with_script_prefix=True)
        responses = [self._mock_get(redirect), self._mock_get(good)]
        with patch('data_updater.requests.get', side_effect=responses), \
             patch('data_updater.time.sleep'):
            result = get_sina_kline('600519', scale=240, datalen=3)
        self.assertEqual(len(result), 3)

    def test_skips_items_without_day_field(self):
        """items 中没有 day 字段的条目被跳过"""
        items = SAMPLE_KLINES + [{'open': '100', 'close': '101', 'high': '102', 'low': '99', 'volume': '1000'}]
        text = make_kline_response(items, with_script_prefix=False)
        with patch('data_updater.requests.get', return_value=self._mock_get(text)):
            result = get_sina_kline('600519', scale=240, datalen=10)
        self.assertEqual(len(result), 3)   # 只有3条有 day 字段


# ══════════════════════════════════════════════════════════════════════════════
# get_sina_realtime - 解析
# ══════════════════════════════════════════════════════════════════════════════

class TestGetSinaRealtime(unittest.TestCase):

    def _mock_get(self, gbk_text):
        resp = MagicMock()
        resp.content = gbk_text.encode('gbk', errors='replace')
        resp.raise_for_status = MagicMock()
        return resp

    def test_parses_single_stock(self):
        """能正确解析单只股票行情"""
        with patch('data_updater.requests.get', return_value=self._mock_get(SAMPLE_REALTIME_GBK)):
            result = get_sina_realtime(['600519'])
        self.assertIn('600519', result)
        data = result['600519']
        self.assertEqual(data['name'], '贵州茅台')
        self.assertAlmostEqual(data['close'], 1416.02)
        self.assertAlmostEqual(data['prev_close'], 1401.18)

    def test_change_pct_calculated_correctly(self):
        """涨跌幅 = (close - prev_close) / prev_close * 100"""
        with patch('data_updater.requests.get', return_value=self._mock_get(SAMPLE_REALTIME_GBK)):
            result = get_sina_realtime(['600519'])
        data = result['600519']
        expected = round((1416.02 - 1401.18) / 1401.18 * 100, 2)
        self.assertAlmostEqual(data['change_pct'], expected, places=1)

    def test_returns_empty_on_network_error(self):
        """网络异常时返回空 dict，不抛出"""
        import requests as req
        with patch('data_updater.requests.get', side_effect=req.exceptions.ConnectionError()):
            result = get_sina_realtime(['600519'])
        self.assertEqual(result, {})

    def test_skips_malformed_lines(self):
        """字段不足的行被跳过，其他正常股票不受影响"""
        bad = 'var hq_str_sh000001="too,few,fields";'
        combined = SAMPLE_REALTIME_GBK + '\n' + bad
        with patch('data_updater.requests.get', return_value=self._mock_get(combined)):
            result = get_sina_realtime(['600519', '000001'])
        self.assertIn('600519', result)
        self.assertNotIn('000001', result)

    def test_batches_large_symbol_list(self):
        """超过200只股票时分批请求"""
        symbols = [f'{i:06d}' for i in range(1, 251)]
        call_count = []
        def fake_get(url, **kwargs):
            call_count.append(url)
            return self._mock_get(SAMPLE_REALTIME_GBK)
        with patch('data_updater.requests.get', side_effect=fake_get):
            get_sina_realtime(symbols)
        self.assertEqual(len(call_count), 2)   # 250只 → 2批


# ══════════════════════════════════════════════════════════════════════════════
# db.py - SQLite 层
# ══════════════════════════════════════════════════════════════════════════════

class TestDb(unittest.TestCase):

    def setUp(self):
        # 每个测试前清空表
        with db.get_conn() as conn:
            conn.execute('DELETE FROM klines')
            conn.execute('DELETE FROM stocks')
            conn.execute('DELETE FROM realtime')
            conn.execute('DELETE FROM news')
            conn.execute('DELETE FROM boards')
            conn.execute('DELETE FROM board_stocks')

    # ── klines ────────────────────────────────────────────────────────────────

    def test_upsert_and_get_klines(self):
        """写入K线后能正确读回，按日期升序"""
        klines = [
            {'date': '2026-03-25', 'open': 1410.0, 'close': 1410.0, 'high': 1417.0, 'low': 1401.0, 'volume': 100, 'amount': 0, 'change_pct': 0},
            {'date': '2026-03-27', 'open': 1400.0, 'close': 1416.0, 'high': 1426.0, 'low': 1396.0, 'volume': 300, 'amount': 0, 'change_pct': 0},
        ]
        db.upsert_klines('600519', klines)
        result = db.get_klines('600519', period='daily', limit=10)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['date'], '2026-03-25')
        self.assertEqual(result[1]['date'], '2026-03-27')

    def test_upsert_klines_replaces_on_conflict(self):
        """同一 (symbol, period, date) 更新时覆盖旧数据"""
        k1 = [{'date': '2026-03-27', 'open': 1400.0, 'close': 1410.0, 'high': 1420.0, 'low': 1395.0, 'volume': 100, 'amount': 0, 'change_pct': 0}]
        k2 = [{'date': '2026-03-27', 'open': 1400.0, 'close': 1416.02, 'high': 1426.0, 'low': 1396.0, 'volume': 300, 'amount': 0, 'change_pct': 0}]
        db.upsert_klines('600519', k1)
        db.upsert_klines('600519', k2)
        result = db.get_klines('600519')
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result[0]['close'], 1416.02)

    def test_get_klines_respects_limit(self):
        """limit 参数正确截断结果"""
        klines = [{'date': f'2026-03-{d:02d}', 'open': 1400.0, 'close': 1400.0, 'high': 1410.0, 'low': 1390.0, 'volume': 100, 'amount': 0, 'change_pct': 0}
                  for d in range(1, 11)]
        db.upsert_klines('600519', klines)
        result = db.get_klines('600519', limit=5)
        self.assertEqual(len(result), 5)
        # 返回最新5条
        self.assertEqual(result[-1]['date'], '2026-03-10')

    def test_daily_and_weekly_klines_stored_separately(self):
        """日K和周K独立存储，互不干扰"""
        k = [{'date': '2026-03-27', 'open': 1400.0, 'close': 1416.0, 'high': 1426.0, 'low': 1396.0, 'volume': 100, 'amount': 0, 'change_pct': 0}]
        db.upsert_klines('600519', k, period='daily')
        db.upsert_klines('600519', k, period='weekly')
        daily = db.get_klines('600519', period='daily')
        weekly = db.get_klines('600519', period='weekly')
        self.assertEqual(len(daily), 1)
        self.assertEqual(len(weekly), 1)

    def test_get_klines_returns_empty_for_unknown_symbol(self):
        result = db.get_klines('999999')
        self.assertEqual(result, [])

    # ── realtime ──────────────────────────────────────────────────────────────

    def test_upsert_and_get_realtime(self):
        """写入实时行情后能正确读回"""
        data = {'symbol': '600519', 'name': '贵州茅台', 'open': 1400.0, 'close': 1416.02,
                'prev_close': 1401.18, 'high': 1426.0, 'low': 1396.66,
                'volume': 3008711, 'amount': 4257499781.0, 'change_pct': 1.06}
        db.upsert_realtime(data)
        result = db.get_realtime('600519')
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], '贵州茅台')
        self.assertAlmostEqual(result['close'], 1416.02)
        self.assertIn('updated_at', result)

    def test_upsert_realtime_updates_existing(self):
        """同一 symbol 再次写入时更新数据"""
        db.upsert_realtime({'symbol': '600519', 'name': '贵州茅台', 'open': 1400.0,
                            'close': 1400.0, 'prev_close': 1401.18, 'high': 1410.0,
                            'low': 1390.0, 'volume': 100, 'amount': 0, 'change_pct': -0.08})
        db.upsert_realtime({'symbol': '600519', 'name': '贵州茅台', 'open': 1400.0,
                            'close': 1416.02, 'prev_close': 1401.18, 'high': 1426.0,
                            'low': 1396.66, 'volume': 3008711, 'amount': 4257499781.0, 'change_pct': 1.06})
        result = db.get_realtime('600519')
        self.assertAlmostEqual(result['close'], 1416.02)

    def test_get_realtime_returns_none_for_unknown_symbol(self):
        result = db.get_realtime('999999')
        self.assertIsNone(result)

    # ── stocks ────────────────────────────────────────────────────────────────

    def test_upsert_and_get_stock(self):
        """写入股票信息后能正确读回"""
        db.upsert_stock('600519', '贵州茅台', '2001-08-27')
        result = db.get_stock('600519')
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], '贵州茅台')
        self.assertEqual(result['listed_date'], '2001-08-27')

    def test_upsert_board_and_get_boards(self):
        """写入板块后能按 type 读回"""
        db.upsert_board('白酒', 'industry', 20, '强势', 85, 15, 5, 2.5)
        db.upsert_board('AI概念', 'concept', 50, '偏强', 65, 30, 18, 0.8)
        industries = db.get_boards('industry')
        concepts   = db.get_boards('concept')
        self.assertEqual(len(industries), 1)
        self.assertEqual(industries[0]['name'], '白酒')
        self.assertEqual(len(concepts), 1)

    def test_replace_board_stocks_and_get(self):
        """写入板块成员后能读回，再次写入完全替换"""
        stocks1 = [{'symbol': '600519', 'name': '贵州茅台', 'close': 1416.0,
                    'change_pct': 1.0, 'volume': 100, 'turnover': 0.5}]
        stocks2 = [{'symbol': '000858', 'name': '五粮液', 'close': 150.0,
                    'change_pct': 0.5, 'volume': 200, 'turnover': 0.3}]
        db.upsert_board('白酒', 'industry', 2, '强势', 85, 2, 0, 0.75)
        db.replace_board_stocks('白酒', 'industry', stocks1)
        db.replace_board_stocks('白酒', 'industry', stocks2)
        result = db.get_board_stocks('白酒', 'industry')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['symbol'], '000858')

    def test_get_symbol_boards(self):
        """能通过股票代码反查所属行业和概念"""
        db.upsert_board('白酒', 'industry', 5, '强势', 85, 4, 1, 1.5)
        db.upsert_board('消费白马', 'concept', 10, '偏强', 65, 7, 3, 0.6)
        db.replace_board_stocks('白酒', 'industry', [
            {'symbol': '600519', 'name': '贵州茅台', 'close': 1416.0, 'change_pct': 1.0, 'volume': 100, 'turnover': 0.5}
        ])
        db.replace_board_stocks('消费白马', 'concept', [
            {'symbol': '600519', 'name': '贵州茅台', 'close': 1416.0, 'change_pct': 1.0, 'volume': 100, 'turnover': 0.5}
        ])
        boards = db.get_symbol_boards('600519')
        self.assertIn('白酒', boards['industries'])
        self.assertIn('消费白马', boards['concepts'])

    def test_get_all_symbols(self):
        """get_all_symbols 返回 board_stocks 中所有不重复代码"""
        db.upsert_board('白酒', 'industry', 2, '强势', 85, 2, 0, 1.0)
        db.replace_board_stocks('白酒', 'industry', [
            {'symbol': '600519', 'name': '贵州茅台', 'close': 1416.0, 'change_pct': 1.0, 'volume': 100, 'turnover': 0.5},
            {'symbol': '000858', 'name': '五粮液',   'close': 150.0,  'change_pct': 0.5, 'volume': 200, 'turnover': 0.3},
        ])
        symbols = db.get_all_symbols()
        self.assertIn('600519', symbols)
        self.assertIn('000858', symbols)

    def test_get_stock_returns_none_for_unknown(self):
        result = db.get_stock('999999')
        self.assertIsNone(result)

    # ── news ──────────────────────────────────────────────────────────────────

    def test_replace_news_clears_old_entries(self):
        """replace_news 先删后插，不会积累重复新闻"""
        news1 = [{'type': 'stock', 'source': '', 'title': '旧新闻', 'pub_date': '2026-03-26', 'url': ''}]
        news2 = [{'type': 'stock', 'source': '', 'title': '新新闻', 'pub_date': '2026-03-27', 'url': ''}]
        db.replace_news('600519', news1)
        db.replace_news('600519', news2)
        result = db.get_news('600519')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['title'], '新新闻')

    def test_get_news_respects_limit(self):
        """limit 参数正确截断新闻条数"""
        news = [{'type': 'stock', 'source': '', 'title': f'新闻{i}', 'pub_date': f'2026-03-{i:02d}', 'url': ''}
                for i in range(1, 11)]
        db.replace_news('600519', news)
        result = db.get_news('600519', limit=5)
        self.assertEqual(len(result), 5)

    def test_get_news_returns_empty_for_unknown(self):
        result = db.get_news('999999')
        self.assertEqual(result, [])


# ══════════════════════════════════════════════════════════════════════════════
# get_full_kline_history - AKShare全量历史（含重试）
# ══════════════════════════════════════════════════════════════════════════════

SAMPLE_AKSHARE_DF_ROWS = [
    {'日期': '2001-08-27', '开盘': 35.55, '收盘': 36.86, '最高': 37.50, '最低': 35.22, '成交量': 1234567, '成交额': 45000000.0, '涨跌幅': 3.68},
    {'日期': '2001-08-28', '开盘': 36.86, '收盘': 37.20, '最高': 38.00, '最低': 36.50, '成交量': 987654,  '成交额': 36000000.0, '涨跌幅': 0.92},
]

def _make_ak_df(rows=None):
    import pandas as pd
    return pd.DataFrame(rows or SAMPLE_AKSHARE_DF_ROWS)


class TestGetFullKlineHistory(unittest.TestCase):

    def test_returns_klines_from_listed_date(self):
        """能拿到从上市日期开始的所有K线"""
        with patch('data_updater.ak.stock_zh_a_hist', return_value=_make_ak_df()):
            result = get_full_kline_history('600519', listed_date='2001-08-27')
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['date'], '2001-08-27')

    def test_kline_fields_complete(self):
        """返回字段包含 date/open/close/high/low/volume/amount/change_pct"""
        with patch('data_updater.ak.stock_zh_a_hist', return_value=_make_ak_df()):
            result = get_full_kline_history('600519', listed_date='2001-08-27')
        k = result[0]
        for field in ('date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'change_pct'):
            self.assertIn(field, k, f'缺少字段: {field}')

    def test_retries_on_akshare_exception(self):
        """AKShare 抛异常时重试，第二次成功则返回数据"""
        call_count = [0]
        def flaky(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception('eastmoney timeout')
            return _make_ak_df()
        with patch('data_updater.ak.stock_zh_a_hist', side_effect=flaky), \
             patch('data_updater.time.sleep'):
            result = get_full_kline_history('600519', listed_date='2001-08-27')
        self.assertEqual(len(result), 2)
        self.assertEqual(call_count[0], 2)

    def test_returns_empty_after_max_retries(self):
        """重试耗尽后返回空列表，不抛出"""
        with patch('data_updater.ak.stock_zh_a_hist', side_effect=Exception('persistent error')), \
             patch('data_updater.time.sleep'):
            result = get_full_kline_history('600519', listed_date='2001-08-27')
        self.assertEqual(result, [])

    def test_returns_empty_when_df_is_none(self):
        """AKShare 返回 None 时返回空列表"""
        with patch('data_updater.ak.stock_zh_a_hist', return_value=None):
            result = get_full_kline_history('600519', listed_date='2001-08-27')
        self.assertEqual(result, [])


# ══════════════════════════════════════════════════════════════════════════════
# get_kline_incremental - 增量逻辑
# ══════════════════════════════════════════════════════════════════════════════

class TestGetKlineIncremental(unittest.TestCase):

    def setUp(self):
        with db.get_conn() as conn:
            conn.execute('DELETE FROM klines')
            conn.execute('DELETE FROM stocks')
            conn.execute('DELETE FROM boards')
            conn.execute('DELETE FROM board_stocks')

    def _sina_mock(self, items):
        resp = MagicMock()
        resp.text = make_kline_response(items, with_script_prefix=False)
        resp.raise_for_status = MagicMock()
        return resp

    def test_fetches_sina_1023_bars_when_db_empty(self):
        """DB 没有该股票K线时，用新浪拉取1023条（约4年）并写入"""
        sina_items = [
            {'day': '2022-03-01', 'open': '35.0', 'high': '37.0', 'low': '34.0', 'close': '36.0', 'volume': '100'},
            {'day': '2026-03-26', 'open': '1400.0', 'high': '1410.0', 'low': '1390.0', 'close': '1401.0', 'volume': '200'},
        ]
        captured_urls = []
        def fake_get(url, **kwargs):
            captured_urls.append(url)
            return self._sina_mock(sina_items)
        with patch('data_updater.requests.get', side_effect=fake_get):
            get_kline_incremental('600519', listed_date='2001-08-27')
        stored = db.get_klines('600519', limit=9999)
        self.assertEqual(len(stored), 2)
        self.assertEqual(stored[0]['date'], '2022-03-01')
        # 首次应请求 datalen=1023
        import re
        m = re.search(r'datalen=(\d+)', captured_urls[0])
        self.assertEqual(int(m.group(1)), 1023)

    def test_appends_only_new_bars_when_history_exists(self):
        """DB 已有历史数据时，只追加新浪返回的新K线"""
        old = [{'date': '2026-03-25', 'open': 1410.0, 'close': 1410.0,
                'high': 1417.0, 'low': 1401.0, 'volume': 100, 'amount': 0, 'change_pct': 0}]
        db.upsert_klines('600519', old, period='daily')

        sina_items = [
            {'day': '2026-03-25', 'open': '1410.11', 'high': '1417.87', 'low': '1401.01', 'close': '1410.27', 'volume': '2609346'},
            {'day': '2026-03-26', 'open': '1409.00', 'high': '1413.90', 'low': '1400.30', 'close': '1401.18', 'volume': '2309289'},
            {'day': '2026-03-27', 'open': '1400.00', 'high': '1426.00', 'low': '1396.66', 'close': '1416.02', 'volume': '3008711'},
        ]
        with patch('data_updater.requests.get', return_value=self._sina_mock(sina_items)):
            get_kline_incremental('600519', listed_date='2001-08-27')

        stored = db.get_klines('600519', limit=9999)
        self.assertEqual(len(stored), 3)
        self.assertEqual(stored[-1]['date'], '2026-03-27')

    def test_no_full_fetch_when_history_exists(self):
        """DB 已有历史时不再调用 AKShare 全量接口"""
        old = [{'date': '2026-03-25', 'open': 1410.0, 'close': 1410.0,
                'high': 1417.0, 'low': 1401.0, 'volume': 100, 'amount': 0, 'change_pct': 0}]
        db.upsert_klines('600519', old, period='daily')

        sina_items = [{'day': '2026-03-27', 'open': '1400.00', 'high': '1426.00',
                       'low': '1396.66', 'close': '1416.02', 'volume': '3008711'}]
        with patch('data_updater.requests.get', return_value=self._sina_mock(sina_items)), \
             patch('data_updater.ak.stock_zh_a_hist') as mock_ak:
            get_kline_incremental('600519', listed_date='2001-08-27')
        mock_ak.assert_not_called()

    def test_incremental_fetches_only_days_since_last(self):
        """增量时 datalen 根据距上次日期天数动态计算，不拉1023条"""
        from unittest.mock import call
        import datetime
        # 昨天的数据
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        old = [{'date': yesterday, 'open': 1410.0, 'close': 1410.0,
                'high': 1417.0, 'low': 1401.0, 'volume': 100, 'amount': 0, 'change_pct': 0}]
        db.upsert_klines('600519', old, period='daily')

        sina_items = [{'day': yesterday, 'open': '1410.0', 'high': '1417.0',
                       'low': '1401.0', 'close': '1410.0', 'volume': '100'}]
        captured_urls = []
        def fake_get(url, **kwargs):
            captured_urls.append(url)
            return self._sina_mock(sina_items)

        with patch('data_updater.requests.get', side_effect=fake_get):
            get_kline_incremental('600519', listed_date='2001-08-27')

        # datalen 应该很小（约 1+5=6），不是1023
        self.assertTrue(captured_urls, '应发出请求')
        url = captured_urls[0]
        import re
        m = re.search(r'datalen=(\d+)', url)
        self.assertIsNotNone(m)
        self.assertLess(int(m.group(1)), 30, f'增量 datalen 应远小于1023，实际={m.group(1)}')


# ══════════════════════════════════════════════════════════════════════════════
# daily_update.py - 每日更新覆盖率验证
# ══════════════════════════════════════════════════════════════════════════════

from daily_update import update_klines, update_news
from init_all import init_klines


class TestDailyUpdateCoverage(unittest.TestCase):

    def setUp(self):
        with db.get_conn() as conn:
            conn.execute('DELETE FROM klines')
            conn.execute('DELETE FROM stocks')
            conn.execute('DELETE FROM boards')
            conn.execute('DELETE FROM board_stocks')

    def test_update_klines_calls_incremental_for_every_symbol(self):
        """update_klines 对列表中每只股票都调用增量更新，一只不落"""
        symbols = ['600519', '000001', '300750']
        called = []

        def fake_incremental(symbol, listed_date=''):
            called.append(symbol)
            return []

        with patch('daily_update.get_kline_incremental', side_effect=fake_incremental), \
             patch('daily_update.time.sleep'):
            update_klines(symbols)

        self.assertEqual(sorted(called), sorted(symbols),
                         f'漏处理股票: {set(symbols) - set(called)}')

    def test_update_klines_no_symbol_skipped_even_if_klines_exist(self):
        """即使股票已有K线，update_klines 仍执行增量更新（不像 init_klines 会跳过）"""
        symbols = ['600519', '000001']
        for sym in symbols:
            db.upsert_klines(sym, [
                {'date': '2026-03-01', 'open': 10.0, 'close': 10.0,
                 'high': 11.0, 'low': 9.0, 'volume': 100, 'amount': 0, 'change_pct': 0}
            ], period='daily')

        call_count = [0]

        def fake_incremental(symbol, listed_date=''):
            call_count[0] += 1
            return []

        with patch('daily_update.get_kline_incremental', side_effect=fake_incremental), \
             patch('daily_update.time.sleep'):
            update_klines(symbols)

        self.assertEqual(call_count[0], len(symbols),
                         f'应调 {len(symbols)} 次，实际 {call_count[0]} 次')

    def test_update_news_calls_get_stock_news_for_every_symbol(self):
        """update_news 对每只股票都获取新闻，一只不落"""
        symbols = ['600519', '000001', '300750', '002415', '000858']
        called = []

        with patch('daily_update.get_stock_news', side_effect=lambda s: called.append(s) or []), \
             patch('daily_update.time.sleep'):
            update_news(symbols)

        self.assertEqual(sorted(called), sorted(symbols),
                         f'漏获取新闻: {set(symbols) - set(called)}')


class TestInitAllCoverage(unittest.TestCase):

    def setUp(self):
        with db.get_conn() as conn:
            conn.execute('DELETE FROM klines')
            conn.execute('DELETE FROM stocks')
            conn.execute('DELETE FROM boards')
            conn.execute('DELETE FROM board_stocks')

    def _fake_klines(self):
        return [{'date': '2001-08-27', 'open': 35.0, 'close': 36.0,
                 'high': 37.0, 'low': 34.0, 'volume': 100, 'amount': 0.0, 'change_pct': 0.0}]

    def test_init_klines_skips_symbols_with_existing_data(self):
        """init_klines 对已有K线的股票跳过（支持断点续传）"""
        db.upsert_klines('600519', self._fake_klines(), period='daily')

        call_count = [0]

        def fake_history(symbol, listed_date='', period='daily'):
            call_count[0] += 1
            return self._fake_klines()

        with patch('init_all.get_full_kline_history', side_effect=fake_history), \
             patch('init_all.get_listed_date', return_value='2001-08-27'), \
             patch('init_all.time.sleep'), \
             patch('init_all.get_stock_news', return_value=[]):
            init_klines(['600519', '000001'], with_news=False)

        self.assertEqual(call_count[0], 1, '已有K线的股票应被跳过，只处理新股票')

    def test_init_klines_news_fetched_for_every_new_kline_stock(self):
        """init_klines 对每只成功写入K线的股票都应获取新闻，而不是每10只才获取一次"""
        # 5只股票，都没有现有K线
        symbols = ['600519', '000001', '000002', '000003', '000004']
        news_called = []

        with patch('init_all.get_full_kline_history', return_value=self._fake_klines()), \
             patch('init_all.get_listed_date', return_value='2001-08-27'), \
             patch('init_all.time.sleep'), \
             patch('init_all.get_stock_news',
                   side_effect=lambda s: news_called.append(s) or []):
            init_klines(symbols, with_news=True)

        self.assertEqual(sorted(news_called), sorted(symbols),
                         f'应为每只股票获取新闻，实际只获取了: {sorted(news_called)}')


# ══════════════════════════════════════════════════════════════════════════════

def teardown_module():
    os.unlink(_tmp_db.name)


if __name__ == '__main__':
    unittest.main(verbosity=2)

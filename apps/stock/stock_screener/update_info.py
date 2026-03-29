#!/usr/bin/python3
"""
补充信息更新脚本（不常用，按需手动运行）

功能：
  1. stock_profiles  — 从东财拉取每只股票基本面（市值、股本、行业）
  2. board_extra     — 从同花顺拉取概念板块额外信息（资金净流入、成交额、排名）

用法：
  python update_info.py                  # 更新全部
  python update_info.py --profiles-only  # 只更新股票基本面
  python update_info.py --boards-only    # 只更新板块额外信息
  python update_info.py --stock 600519   # 只更新单只股票基本面
"""

import akshare as ak
import time
import argparse
from datetime import datetime
from tqdm import tqdm

import db

SLEEP = 0.5  # 每次请求间隔


# ── 股票基本面 ─────────────────────────────────────────────────────────────────

def _parse_profile(symbol: str) -> dict | None:
    try:
        df = ak.stock_individual_info_em(symbol=symbol)
        if df is None or df.empty:
            return None
        info = {row['item']: row['value'] for _, row in df.iterrows()}
        return {
            'total_shares':     float(info.get('总股本', 0) or 0),
            'float_shares':     float(info.get('流通股', 0) or 0),
            'total_market_cap': float(info.get('总市值', 0) or 0),
            'float_market_cap': float(info.get('流通市值', 0) or 0),
            'industry':         str(info.get('行业', '') or ''),
        }
    except Exception:
        return None


def update_stock_profiles(symbols: list):
    print(f"\n📊 更新股票基本面（{len(symbols)} 只）...")
    ok, skip, fail = 0, 0, 0

    for symbol in tqdm(symbols, desc="  stock_profiles"):
        # 已有且7天内更新过则跳过
        existing = db.get_stock_profile(symbol)
        if existing and existing.get('updated_at'):
            try:
                updated = datetime.strptime(existing['updated_at'], '%Y-%m-%d %H:%M:%S')
                if (datetime.now() - updated).days < 7:
                    skip += 1
                    continue
            except Exception:
                pass

        profile = _parse_profile(symbol)
        if profile:
            db.upsert_stock_profile(symbol, **profile)
            # 同步更新 stocks 表的上市日期和名称
            ok += 1
        else:
            fail += 1

        time.sleep(SLEEP)

    print(f"✅ 基本面更新：成功 {ok}，跳过 {skip}，失败 {fail}")


# ── 概念板块额外信息 ───────────────────────────────────────────────────────────

def _parse_board_extra(concept_name: str) -> dict | None:
    try:
        df = ak.stock_board_concept_info_ths(symbol=concept_name)
        if df is None or df.empty:
            return None
        info = {str(row['项目']): str(row['值']) for _, row in df.iterrows()}

        def _num(key):
            try:
                return float(str(info.get(key, '') or '').replace('%', '').replace(',', ''))
            except Exception:
                return None

        return {
            'fund_inflow':  _num('资金净流入(亿)'),
            'amount':       _num('成交额(亿)'),
            'rank_in_type': info.get('涨幅排名', None),
        }
    except Exception:
        return None


def update_board_extras():
    concepts = db.get_boards('concept')
    print(f"\n🏷  更新概念板块额外信息（{len(concepts)} 个）...")
    ok, fail = 0, 0

    for board in tqdm(concepts, desc="  board_extra"):
        extra = _parse_board_extra(board['name'])
        if extra:
            db.update_board_extra(board['name'], 'concept', **extra)
            ok += 1
        else:
            fail += 1
        time.sleep(SLEEP)

    print(f"✅ 板块额外信息：成功 {ok}，失败 {fail}")


# ── 入口 ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='补充信息更新')
    parser.add_argument('--profiles-only', action='store_true', help='只更新股票基本面')
    parser.add_argument('--boards-only',   action='store_true', help='只更新板块额外信息')
    parser.add_argument('--stock',         type=str,            help='只更新单只股票')
    args = parser.parse_args()

    start = datetime.now()
    print(f"🚀 开始: {start.strftime('%Y-%m-%d %H:%M:%S')}")

    if args.stock:
        profile = _parse_profile(args.stock)
        if profile:
            db.upsert_stock_profile(args.stock, **profile)
            print(f"✅ {args.stock}: {profile}")
        else:
            print(f"❌ {args.stock}: 获取失败")
    elif args.profiles_only:
        update_stock_profiles(db.get_all_symbols())
    elif args.boards_only:
        update_board_extras()
    else:
        update_stock_profiles(db.get_all_symbols())
        update_board_extras()

    print(f"⏱  耗时: {datetime.now() - start}")

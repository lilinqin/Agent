#!/usr/bin/python3
"""
A股完整数据采集器 v2.0
- 每只股票独立存储，包含行业、概念、K线、新闻
- 板块文件只存储股票代码列表
- 支持增量更新

用法：
  python stock_scraper_full.py --output-dir ../stock-analyzer/data
  python stock_scraper_full.py --mode full          # 全量采集
  python stock_scraper_full.py --mode update        # 增量更新
  python stock_scraper_full.py --mode stocks-only   # 只更新股票详情
"""

import akshare as ak
import pandas as pd
import time
import json
import os
import argparse
from datetime import datetime, timedelta
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================
# 配置
# ============================================================
SLEEP_BETWEEN = 0.15
TODAY = datetime.now().strftime('%Y-%m-%d')
DATA_DIR = '../stock-analyzer/data'

# ============================================================
# 获取单只股票完整信息
# ============================================================
def get_stock_profile(symbol, name):
    """获取股票完整信息：基本信息、行业、概念"""
    try:
        # 获取个股信息（包含行业、概念）
        df = ak.stock_individual_info_em(symbol=symbol)
        if df is None or df.empty:
            return None
        
        info = {
            'symbol': symbol,
            'name': name,
            'industry': '',
            'concepts': [],
            'listed_date': '',
            'total_shares': 0,
            'market_cap': 0,
        }
        
        for _, row in df.iterrows():
            item = str(row.get('item', ''))
            value = row.get('value', '')
            
            if '行业' in item:
                info['industry'] = str(value)
            elif '概念' in item:
                info['concepts'] = [c.strip() for c in str(value).split(',') if c.strip()]
            elif '上市时间' in item:
                info['listed_date'] = str(value)
            elif '总股本' in item:
                info['total_shares'] = float(value) if value else 0
            elif '总市值' in item:
                info['market_cap'] = float(value) if value else 0
        
        return info
    except Exception:
        return None


def get_stock_realtime(symbol):
    """获取股票实时行情"""
    try:
        df = ak.stock_zh_a_spot_em()
        if df is None:
            return None
        
        stock = df[df['代码'] == symbol]
        if stock.empty:
            return None
        
        row = stock.iloc[0]
        return {
            'close': float(row.get('最新价', 0)) or 0,
            'change_pct': float(row.get('涨跌幅', 0)) or 0,
            'change_amount': float(row.get('涨跌额', 0)) or 0,
            'volume': int(row.get('成交量', 0)) or 0,
            'turnover': float(row.get('换手率', 0)) or 0,
            'pe': float(row.get('市盈率-动态', 0)) or 0,
            'pb': float(row.get('市净率', 0)) or 0,
            'market_cap': float(row.get('总市值', 0)) or 0,
            'high': float(row.get('最高', 0)) or 0,
            'low': float(row.get('最低', 0)) or 0,
            'open': float(row.get('今开', 0)) or 0,
            'prev_close': float(row.get('昨收', 0)) or 0,
        }
    except Exception:
        return None


def get_stock_kline(symbol, days=None, listed_date=None):
    """获取股票K线数据（日K）
    - 如果指定了listed_date，从上市日期开始
    - 否则使用days参数（默认365天）
    """
    try:
        end_date = datetime.now().strftime('%Y%m%d')
        
        if listed_date:
            ld = str(listed_date)
            if len(ld) >= 8:
                start_date = ld[:4] + ld[4:6] + ld[6:8]
            elif len(ld) >= 10:
                start_date = ld[:10].replace('-', '')
            else:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        elif days:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        else:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        
        if df is None or df.empty:
            return []
        
        klines = []
        for _, row in df.iterrows():
            klines.append({
                'date': str(row.get('日期', '')),
                'open': float(row.get('开盘', 0)),
                'close': float(row.get('收盘', 0)),
                'high': float(row.get('最高', 0)),
                'low': float(row.get('最低', 0)),
                'volume': int(row.get('成交量', 0)),
                'amount': float(row.get('成交额', 0)),
                'change_pct': float(row.get('涨跌幅', 0)),
            })
        
        return klines
    except Exception:
        return []


def get_stock_news(symbol):
    """获取股票近期新闻/公告"""
    try:
        # 获取公司新闻
        df = ak.stock_news_em(symbol=symbol)
        if df is None or df.empty:
            return []
        
        news_list = []
        for _, row in df.head(20).iterrows():  # 最近20条
            news_list.append({
                'title': str(row.get('新闻标题', '')),
                'time': str(row.get('发布时间', '')),
                'content': str(row.get('新闻内容', ''))[:500],  # 截取前500字
                'source': str(row.get('新闻来源', '')),
                'url': str(row.get('新闻链接', '')),
            })
        
        return news_list
    except Exception:
        return []


def build_stock_data(symbol, name):
    """构建单只股票的完整数据"""
    print(f"  📊 采集 {symbol} {name}...")
    
    # 1. 获取基本信息和行业概念
    profile = get_stock_profile(symbol, name)
    time.sleep(SLEEP_BETWEEN * 2)
    
    # 2. 获取实时行情
    realtime = get_stock_realtime(symbol)
    time.sleep(SLEEP_BETWEEN)
    
    # 3. 获取K线数据
    klines = get_stock_kline(symbol, days=365)
    time.sleep(SLEEP_BETWEEN * 2)
    
    # 4. 获取新闻
    news = get_stock_news(symbol)
    time.sleep(SLEEP_BETWEEN)
    
    # 合并数据
    stock_data = {
        'symbol': symbol,
        'name': name,
        'industry': profile.get('industry', '') if profile else '',
        'concepts': profile.get('concepts', []) if profile else [],
        'listed_date': profile.get('listed_date', '') if profile else '',
        'total_shares': profile.get('total_shares', 0) if profile else 0,
        'realtime': realtime or {},
        'klines': klines,
        'news': news,
        'updated_at': TODAY,
    }
    
    return stock_data


# ============================================================
# 板块数据采集（优化版）
# ============================================================
def scrape_board_optimized(board_name, board_type='industry'):
    """获取板块成分股（只返回代码和名称）"""
    try:
        if board_type == 'industry':
            df = ak.stock_board_industry_cons_em(symbol=board_name)
        else:
            df = ak.stock_board_concept_cons_em(symbol=board_name)
        
        if df is None or df.empty:
            return []
        
        stocks = []
        for _, row in df.iterrows():
            stocks.append({
                'symbol': str(row.get('代码', '')).zfill(6),
                'name': str(row.get('名称', '')),
            })
        
        return stocks
    except Exception as e:
        print(f"    ❌ {board_name}: {e}")
        return []


def calculate_board_strength_by_codes(board_name, board_type='industry', stock_data_map=None):
    """根据股票代码列表计算板块强弱"""
    try:
        if board_type == 'industry':
            df = ak.stock_board_industry_cons_em(symbol=board_name)
        else:
            df = ak.stock_board_concept_cons_em(symbol=board_name)
        
        if df is None or df.empty:
            return '中性', 50, 0, 0, 0.0, []
        
        stocks = []
        for _, row in df.iterrows():
            stock = {
                'symbol': str(row.get('代码', '')).zfill(6),
                'name': str(row.get('名称', '')),
                'close': float(row.get('最新价', 0)) if pd.notna(row.get('最新价')) else 0,
                'change_pct': float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else 0,
                'volume': int(row.get('成交量', 0)) if pd.notna(row.get('成交量')) else 0,
                'turnover': float(row.get('换手率', 0)) if pd.notna(row.get('换手率')) else 0,
            }
            stocks.append(stock)
        
        if not stocks:
            return '中性', 50, 0, 0, 0.0, []
        
        total = len(stocks)
        up_count = sum(1 for s in stocks if s.get('change_pct', 0) > 0)
        down_count = sum(1 for s in stocks if s.get('change_pct', 0) < 0)
        avg_change = sum(s.get('change_pct', 0) for s in stocks) / total
        up_ratio = up_count / total
        
        if avg_change > 2 and up_ratio > 0.7:
            strength, score = '强势', 85
        elif avg_change > 0.5 and up_ratio > 0.55:
            strength, score = '偏强', 65
        elif avg_change < -2 and up_ratio < 0.3:
            strength, score = '弱势', 20
        elif avg_change < -0.5 and up_ratio < 0.45:
            strength, score = '偏弱', 35
        else:
            strength, score = '中性', 50
        
        return strength, score, up_count, down_count, avg_change, stocks
    except Exception:
        return '中性', 50, 0, 0, 0.0, []


# ============================================================
# 主流程
# ============================================================
def main(output_dir, mode='full'):
    print("=" * 60)
    print("  A股数据采集器 v2.0 - 完整版")
    print("  每只股票独立存储，包含行业/概念/K线/新闻")
    print("=" * 60)
    
    # 创建目录结构
    stocks_dir = os.path.join(output_dir, 'stocks')
    industries_dir = os.path.join(output_dir, 'industries')
    concepts_dir = os.path.join(output_dir, 'concepts')
    os.makedirs(stocks_dir, exist_ok=True)
    os.makedirs(industries_dir, exist_ok=True)
    os.makedirs(concepts_dir, exist_ok=True)
    
    # ============================================================
    # 第一步：获取所有板块和股票列表
    # ============================================================
    print("\n📋 第一步：获取板块列表...")
    
    industry_names = []
    concept_names = []
    
    if mode in ('full', 'boards'):
        try:
            industry_df = ak.stock_board_industry_name_em()
            industry_names = industry_df['板块名称'].tolist() if industry_df is not None else []
            print(f"  ✅ {len(industry_names)} 个行业板块")
        except Exception as e:
            print(f"  ❌ 行业板块获取失败: {e}")
        
        try:
            concept_df = ak.stock_board_concept_name_em()
            concept_names = concept_df['板块名称'].tolist() if concept_df is not None else []
            print(f"  ✅ {len(concept_names)} 个概念板块")
        except Exception as e:
            print(f"  ❌ 概念板块获取失败: {e}")
    
    # ============================================================
    # 第二步：采集板块数据，建立股票→行业/概念映射
    # ============================================================
    print("\n📋 第二步：采集板块成分股，建立股票映射...")
    
    all_stock_symbols = {}  # symbol -> {name, industries: [], concepts: []}
    
    if mode in ('full', 'boards'):
        # 采集行业板块（只建立映射，不保存板块文件）
        print("\n  🏭 行业板块...")
        for name in tqdm(industry_names, desc="    行业"):
            stocks = scrape_board_optimized(name, 'industry')
            time.sleep(SLEEP_BETWEEN)
            
            # 记录股票的行业归属
            for s in stocks:
                sym = s['symbol']
                if sym not in all_stock_symbols:
                    all_stock_symbols[sym] = {'name': s['name'], 'industries': [], 'concepts': []}
                if name not in all_stock_symbols[sym]['industries']:
                    all_stock_symbols[sym]['industries'].append(name)
        
        # 采集概念板块
        print("\n  💡 概念板块...")
        for name in tqdm(concept_names, desc="    概念"):
            stocks = scrape_board_optimized(name, 'concept')
            time.sleep(SLEEP_BETWEEN)
            
            for s in stocks:
                sym = s['symbol']
                if sym not in all_stock_symbols:
                    all_stock_symbols[sym] = {'name': s['name'], 'industries': [], 'concepts': []}
                if name not in all_stock_symbols[sym]['concepts']:
                    all_stock_symbols[sym]['concepts'].append(name)
    
    print(f"\n  📊 共发现 {len(all_stock_symbols)} 只独立股票")
    
    # ============================================================
    # 第三步：采集每只股票的详细信息
    # ============================================================
    if mode in ('full', 'stocks'):
        print(f"\n📋 第三步：采集 {len(all_stock_symbols)} 只股票详情...")
        print("  （包含K线、新闻，预计需要较长时间）")
        
        # 检查已采集的股票
        existing_stocks = set()
        if os.path.exists(stocks_dir):
            existing_stocks = set(f.replace('.json', '') for f in os.listdir(stocks_dir) if f.endswith('.json'))
        
        stock_symbols = list(all_stock_symbols.keys())
        stocks_to_fetch = [s for s in stock_symbols if s not in existing_stocks] if mode == 'update' else stock_symbols
        
        print(f"  📁 已有 {len(existing_stocks)} 只，需采集 {len(stocks_to_fetch)} 只")
        
        for i, symbol in enumerate(tqdm(stocks_to_fetch, desc="  股票详情")):
            info = all_stock_symbols.get(symbol, {})
            name = info.get('name', symbol)
            
            # 构建股票数据
            stock_data = {
                'symbol': symbol,
                'name': name,
                'industries': info.get('industries', []),
                'concepts': info.get('concepts', []),
            }
            
            # 获取实时行情和基本信息
            profile = get_stock_profile(symbol, name)
            if profile and profile.get('listed_date'):
                stock_data['listed_date'] = profile['listed_date']
                listed_date = profile['listed_date']
            else:
                listed_date = None
            
            realtime = get_stock_realtime(symbol)
            if realtime:
                stock_data['realtime'] = realtime
            time.sleep(SLEEP_BETWEEN)
            
            # 获取K线（从上市日期到现在）
            klines = get_stock_kline(symbol, listed_date=listed_date)
            stock_data['klines'] = klines
            time.sleep(SLEEP_BETWEEN * 2)
            
            # 获取新闻
            news = get_stock_news(symbol)
            stock_data['news'] = news[:10]  # 只保留最近10条
            time.sleep(SLEEP_BETWEEN)
            
            stock_data['updated_at'] = TODAY
            
            # 保存单只股票文件
            safe_name = symbol.replace('/', '_').replace('\\', '_')
            filepath = os.path.join(stocks_dir, f"{safe_name}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(stock_data, f, ensure_ascii=False, indent=2)
            
            # 每10只股票打印进度
            if (i + 1) % 10 == 0:
                print(f"    ✓ 已完成 {i + 1}/{len(stocks_to_fetch)}")
    
    # ============================================================
    # 第四步：生成索引文件（按行业/概念分组）
    # ============================================================
    print("\n📋 第四步：生成索引文件...")
    
    # 按行业分组
    industry_map = {}  # industry_name -> [{symbol, name}, ...]
    for sym, info in all_stock_symbols.items():
        for ind in info.get('industries', []):
            if ind not in industry_map:
                industry_map[ind] = []
            industry_map[ind].append({'symbol': sym, 'name': info.get('name', '')})
    
    # 按概念分组
    concept_map = {}  # concept_name -> [{symbol, name}, ...]
    for sym, info in all_stock_symbols.items():
        for con in info.get('concepts', []):
            if con not in concept_map:
                concept_map[con] = []
            concept_map[con].append({'symbol': sym, 'name': info.get('name', '')})
    
    # 保存统一索引（包含行业、概念、股票统计）
    index_data = {
        'updated_at': TODAY,
        'total_stocks': len(all_stock_symbols),
        'industries': [],
        'concepts': [],
    }
    
    for name, stocks in sorted(industry_map.items()):
        index_data['industries'].append({
            'name': name,
            'count': len(stocks),
            'stocks': sorted(stocks, key=lambda x: x['symbol'])
        })
    
    for name, stocks in sorted(concept_map.items()):
        index_data['concepts'].append({
            'name': name,
            'count': len(stocks),
            'stocks': sorted(stocks, key=lambda x: x['symbol'])
        })
    
    with open(os.path.join(output_dir, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    # 保存 industries/ 目录（向后兼容）
    for name, stocks in industry_map.items():
        safe_name = name.replace('/', '_').replace('\\', '_')
        filepath = os.path.join(industries_dir, f"{safe_name}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'name': name,
                'type': 'industry',
                'stocks': sorted(stocks, key=lambda x: x['symbol'])
            }, f, ensure_ascii=False, indent=2)
    
    # 保存 concepts/ 目录（向后兼容）
    for name, stocks in concept_map.items():
        safe_name = name.replace('/', '_').replace('\\', '_')
        filepath = os.path.join(concepts_dir, f"{safe_name}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'name': name,
                'type': 'concept',
                'stocks': sorted(stocks, key=lambda x: x['symbol'])
            }, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("  采集完成！")
    print(f"  - 行业板块: {len(industry_map)} 个")
    print(f"  - 概念板块: {len(concept_map)} 个")
    print(f"  - 股票详情: {len(all_stock_symbols)} 只")
    print("=" * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', default=DATA_DIR)
    parser.add_argument('--mode', choices=['full', 'boards', 'stocks', 'update'], default='full',
                        help='full=全部, boards=仅板块, stocks=仅股票, update=增量更新')
    args = parser.parse_args()
    main(args.output_dir, args.mode)

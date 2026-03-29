#!/usr/bin/python3
"""
A股数据采集脚本 - 分批保存每个股票的行业和概念信息
每个股票保存为独立JSON文件，最后汇总生成行业和概念板块数据

用法：
  python stock_scraper_batch.py --batch-size 100 --output-dir ../stock-analyzer/data/stocks
"""

import akshare as ak
import pandas as pd
import time
import sys
import json
import os
import argparse
from datetime import datetime, timedelta
from tqdm import tqdm

# ============================================================
# 参数配置
# ============================================================
BATCH_SIZE = 100
SLEEP_BETWEEN = 0.1
HISTORY_DAYS = 400

# ============================================================
# 获取单只股票的行业和概念信息
# ============================================================
def get_stock_tags(symbol):
    """获取股票的行业和概念标签"""
    try:
        # 获取个股信息（包含行业、概念）
        df = ak.stock_individual_info_em(symbol=symbol)
        if df is None or len(df) == 0:
            return None
        
        info = {}
        for _, row in df.iterrows():
            item = row.get('item', '')
            value = row.get('value', '')
            if '行业' in str(item):
                info['industry'] = str(value)
            elif '概念' in str(item):
                info['concepts'] = [c.strip() for c in str(value).split(',') if c.strip()]
        
        return info
    except Exception:
        return None

# ============================================================
# 获取板块成分股
# ============================================================
def get_board_stocks(board_type='industry'):
    """获取行业或概念板块列表"""
    try:
        if board_type == 'industry':
            df = ak.stock_board_industry_name_em()
        else:
            df = ak.stock_board_concept_name_em()
        return df['板块名称'].tolist() if df is not None else []
    except Exception as e:
        print(f"  ❌ 获取板块列表失败: {e}")
        return []

def get_board_members(board_name, board_type='industry'):
    """获取板块成分股"""
    try:
        if board_type == 'industry':
            df = ak.stock_board_industry_cons_em(symbol=board_name)
        else:
            df = ak.stock_board_concept_cons_em(symbol=board_name)
        
        if df is not None and '代码' in df.columns:
            return df['代码'].tolist()
        return []
    except Exception:
        return []

# ============================================================
# 构建股票到板块的映射
# ============================================================
def build_stock_mapping():
    """构建股票代码 -> {industry, concepts} 的映射"""
    print("\n📋 构建股票板块映射...")
    
    stock_map = {}  # code -> {industry: str, concepts: list}
    
    # 1. 获取行业板块
    print("  获取行业板块...")
    industry_boards = get_board_stocks('industry')
    print(f"  ✅ {len(industry_boards)} 个行业板块")
    
    for board_name in tqdm(industry_boards, desc="  行业板块"):
        members = get_board_members(board_name, 'industry')
        for code in members:
            code = str(code).zfill(6)
            if code not in stock_map:
                stock_map[code] = {'industry': '', 'concepts': []}
            stock_map[code]['industry'] = board_name
        time.sleep(SLEEP_BETWEEN)
    
    # 2. 获取概念板块
    print("\n  获取概念板块...")
    concept_boards = get_board_stocks('concept')
    print(f"  ✅ {len(concept_boards)} 个概念板块")
    
    for board_name in tqdm(concept_boards, desc="  概念板块"):
        members = get_board_members(board_name, 'concept')
        for code in members:
            code = str(code).zfill(6)
            if code not in stock_map:
                stock_map[code] = {'industry': '', 'concepts': []}
            if board_name not in stock_map[code]['concepts']:
                stock_map[code]['concepts'].append(board_name)
        time.sleep(SLEEP_BETWEEN)
    
    return stock_map

# ============================================================
# 主函数
# ============================================================
def main(output_dir, batch_size=BATCH_SIZE):
    print("=" * 60)
    print("  A股数据采集器 - 分批保存股票信息")
    print("=" * 60)
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    stocks_dir = os.path.join(output_dir, 'stocks')
    os.makedirs(stocks_dir, exist_ok=True)
    
    # 1. 构建映射
    stock_map = build_stock_mapping()
    print(f"\n📊 共 {len(stock_map)} 只股票")
    
    # 2. 保存映射文件
    mapping_file = os.path.join(output_dir, 'stock_mapping.json')
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(stock_map, f, ensure_ascii=False, indent=2)
    print(f"✅ 映射文件已保存: {mapping_file}")
    
    # 3. 分批处理并保存每个股票的JSON
    stock_codes = list(stock_map.keys())
    total_batches = (len(stock_codes) + batch_size - 1) // batch_size
    
    print(f"\n📦 分批处理: {len(stock_codes)} 只股票, 每批 {batch_size} 只, 共 {total_batches} 批")
    
    for batch_idx in range(total_batches):
        start = batch_idx * batch_size
        end = min(start + batch_size, len(stock_codes))
        batch_codes = stock_codes[start:end]
        
        print(f"\n批次 {batch_idx + 1}/{total_batches}: {len(batch_codes)} 只股票")
        
        for code in tqdm(batch_codes, desc=f"  保存股票"):
            stock_data = {
                'symbol': code,
                'industry': stock_map[code]['industry'],
                'concepts': stock_map[code]['concepts'],
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 保存单个股票的JSON
            stock_file = os.path.join(stocks_dir, f'{code}.json')
            with open(stock_file, 'w', encoding='utf-8') as f:
                json.dump(stock_data, f, ensure_ascii=False, indent=2)
    
    # 4. 生成行业板块汇总
    print("\n📊 生成行业板块汇总...")
    industry_summary = {}
    for code, data in stock_map.items():
        industry = data.get('industry', '')
        if industry:
            if industry not in industry_summary:
                industry_summary[industry] = {'stocks': [], 'count': 0}
            industry_summary[industry]['stocks'].append(code)
            industry_summary[industry]['count'] += 1
    
    # 保存行业汇总
    industry_file = os.path.join(output_dir, 'industry_summary.json')
    with open(industry_file, 'w', encoding='utf-8') as f:
        json.dump(industry_summary, f, ensure_ascii=False, indent=2)
    print(f"✅ 行业汇总已保存: {industry_file} ({len(industry_summary)} 个行业)")
    
    # 5. 生成概念板块汇总
    print("\n📊 生成概念板块汇总...")
    concept_summary = {}
    for code, data in stock_map.items():
        for concept in data.get('concepts', []):
            if concept not in concept_summary:
                concept_summary[concept] = {'stocks': [], 'count': 0}
            concept_summary[concept]['stocks'].append(code)
            concept_summary[concept]['count'] += 1
    
    # 保存概念汇总
    concept_file = os.path.join(output_dir, 'concept_summary.json')
    with open(concept_file, 'w', encoding='utf-8') as f:
        json.dump(concept_summary, f, ensure_ascii=False, indent=2)
    print(f"✅ 概念汇总已保存: {concept_file} ({len(concept_summary)} 个概念)")
    
    print("\n" + "=" * 60)
    print("  采集完成！")
    print(f"  - 股票数据目录: {stocks_dir}")
    print(f"  - 行业汇总: {industry_file}")
    print(f"  - 概念汇总: {concept_file}")
    print("=" * 60)

# ============================================================
# 命令行入口
# ============================================================
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A股数据采集器')
    parser.add_argument('--output-dir', default='../stock-analyzer/data', help='输出目录')
    parser.add_argument('--batch-size', type=int, default=100, help='每批处理股票数')
    args = parser.parse_args()
    
    main(args.output_dir, args.batch_size)

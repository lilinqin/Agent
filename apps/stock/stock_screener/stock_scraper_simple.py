#!/usr/bin/python3
"""
A股数据采集脚本 - 按板块分批保存
每个行业/概念板块单独一个JSON文件，前端按需加载

用法：
  python stock_scraper_simple.py --output-dir ../stock-analyzer/data
"""

import akshare as ak
import pandas as pd
import time
import json
import os
import argparse
from datetime import datetime
from tqdm import tqdm

SLEEP_BETWEEN = 0.2
TODAY = datetime.now().strftime('%Y-%m-%d')

def get_stock_data(symbol, name):
    """获取单只股票的基本数据"""
    try:
        # 获取实时行情
        df = ak.stock_zh_a_spot_em()
        if df is None:
            return None
        
        stock = df[df['代码'] == symbol]
        if stock.empty:
            return None
        
        row = stock.iloc[0]
        return {
            'symbol': symbol,
            'name': name,
            'close': float(row.get('最新价', 0)),
            'change_pct': float(row.get('涨跌幅', 0)),
            'volume': int(row.get('成交量', 0)),
            'turnover': float(row.get('换手率', 0)),
        }
    except Exception:
        return None

def scrape_board(board_name, board_type='industry'):
    """获取板块所有成分股数据"""
    try:
        if board_type == 'industry':
            df = ak.stock_board_industry_cons_em(symbol=board_name)
        else:
            df = ak.stock_board_concept_cons_em(symbol=board_name)
        
        if df is None or df.empty:
            return []
        
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
        
        return stocks
    except Exception as e:
        print(f"    ❌ {board_name}: {e}")
        return []

def calculate_strength(stocks):
    """计算板块强弱"""
    if not stocks:
        return '中性', 50, 0, 0, 0.0
    
    total = len(stocks)
    up_count = sum(1 for s in stocks if s.get('change_pct', 0) > 0)
    down_count = sum(1 for s in stocks if s.get('change_pct', 0) < 0)
    avg_change = sum(s.get('change_pct', 0) for s in stocks) / total if total > 0 else 0
    up_ratio = up_count / total if total > 0 else 0
    
    if avg_change > 2 and up_ratio > 0.7:
        return '强势', 85, up_count, down_count, avg_change
    elif avg_change > 0.5 and up_ratio > 0.55:
        return '偏强', 65, up_count, down_count, avg_change
    elif avg_change < -2 and up_ratio < 0.3:
        return '弱势', 20, up_count, down_count, avg_change
    elif avg_change < -0.5 and up_ratio < 0.45:
        return '偏弱', 35, up_count, down_count, avg_change
    else:
        return '中性', 50, up_count, down_count, avg_change

def main(output_dir):
    print("=" * 60)
    print("  A股数据采集器 - 按板块分批保存")
    print("=" * 60)
    
    # 创建目录
    industries_dir = os.path.join(output_dir, 'industries')
    concepts_dir = os.path.join(output_dir, 'concepts')
    os.makedirs(industries_dir, exist_ok=True)
    os.makedirs(concepts_dir, exist_ok=True)
    
    # 1. 获取行业板块列表
    print("\n📋 获取行业板块列表...")
    try:
        industry_df = ak.stock_board_industry_name_em()
        industry_names = industry_df['板块名称'].tolist() if industry_df is not None else []
    except Exception as e:
        print(f"❌ 失败: {e}")
        return
    print(f"✅ {len(industry_names)} 个行业板块")
    
    # 2. 逐个采集行业板块
    print("\n🏭 采集行业板块数据...")
    industry_index = []
    
    for i, name in enumerate(tqdm(industry_names, desc="  行业板块")):
        stocks = scrape_board(name, 'industry')
        time.sleep(SLEEP_BETWEEN)
        
        if not stocks:
            continue
        
        strength, strength_score, up, down, avg_chg = calculate_strength(stocks)
        
        # 板块数据
        board_data = {
            'name': name,
            'type': 'industry',
            'total_stocks': len(stocks),
            'stocks': sorted(stocks, key=lambda x: abs(x.get('change_pct', 0)), reverse=True),
            'strength': strength,
            'strength_score': strength_score,
            'up_count': up,
            'down_count': down,
            'avg_change': round(avg_chg, 2),
            'updated_at': TODAY
        }
        
        # 保存单个板块文件（替换特殊字符）
        safe_name = name.replace('/', '_').replace('\\', '_').replace(':', '_')
        filename = f"{safe_name}.json"
        filepath = os.path.join(industries_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(board_data, f, ensure_ascii=False, indent=2)
        
        # 添加到索引
        industry_index.append({
            'name': name,
            'total_stocks': len(stocks),
            'strength': strength,
            'strength_score': strength_score,
            'avg_change': round(avg_chg, 2),
            'up_count': up,
            'down_count': down,
            'file': f"industries/{filename}"
        })
    
    # 保存行业索引
    index_file = os.path.join(output_dir, 'industries_index.json')
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump({
            'type': 'industry',
            'count': len(industry_index),
            'updated_at': TODAY,
            'items': sorted(industry_index, key=lambda x: x['strength_score'], reverse=True)
        }, f, ensure_ascii=False, indent=2)
    print(f"✅ 行业索引已保存: {index_file}")
    
    # 3. 获取概念板块列表
    print("\n📋 获取概念板块列表...")
    try:
        concept_df = ak.stock_board_concept_name_em()
        concept_names = concept_df['板块名称'].tolist() if concept_df is not None else []
    except Exception as e:
        print(f"❌ 失败: {e}")
        concept_names = []
    print(f"✅ {len(concept_names)} 个概念板块")
    
    # 4. 逐个采集概念板块
    print("\n💡 采集概念板块数据...")
    concept_index = []
    
    for i, name in enumerate(tqdm(concept_names, desc="  概念板块")):
        stocks = scrape_board(name, 'concept')
        time.sleep(SLEEP_BETWEEN)
        
        if not stocks:
            continue
        
        strength, strength_score, up, down, avg_chg = calculate_strength(stocks)
        
        board_data = {
            'name': name,
            'type': 'concept',
            'total_stocks': len(stocks),
            'stocks': sorted(stocks, key=lambda x: abs(x.get('change_pct', 0)), reverse=True),
            'strength': strength,
            'strength_score': strength_score,
            'up_count': up,
            'down_count': down,
            'avg_change': round(avg_chg, 2),
            'updated_at': TODAY
        }
        
        safe_name = name.replace('/', '_').replace('\\', '_').replace(':', '_')
        filename = f"{safe_name}.json"
        filepath = os.path.join(concepts_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(board_data, f, ensure_ascii=False, indent=2)
        
        concept_index.append({
            'name': name,
            'total_stocks': len(stocks),
            'strength': strength,
            'strength_score': strength_score,
            'avg_change': round(avg_chg, 2),
            'up_count': up,
            'down_count': down,
            'file': f"concepts/{filename}"
        })
    
    # 保存概念索引
    index_file = os.path.join(output_dir, 'concepts_index.json')
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump({
            'type': 'concept',
            'count': len(concept_index),
            'updated_at': TODAY,
            'items': sorted(concept_index, key=lambda x: x['strength_score'], reverse=True)
        }, f, ensure_ascii=False, indent=2)
    print(f"✅ 概念索引已保存: {index_file}")
    
    print("\n" + "=" * 60)
    print("  采集完成！")
    print(f"  - 行业板块: {len(industry_index)} 个")
    print(f"  - 概念板块: {len(concept_index)} 个")
    print("=" * 60)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', default='../stock-analyzer/data')
    args = parser.parse_args()
    main(args.output_dir)

#!/usr/bin/python3
"""
A股选股脚本 - 基于 AKShare（升级版）
筛选条件：
  1. 当前价格接近年线（MA250），偏离在 ±5% 以内
  2. KDJ 的 J 值 < 13（超卖信号）

来源：
  - 行业板块（东财，共 ~496 个）
  - 概念板块（东财，共 ~483 个，含液冷、可控核聚变等）

用法：
  python stock_screener.py
  python stock_screener.py --output /path/to/result.json
  python stock_screener.py --mode industry   # 仅行业
  python stock_screener.py --mode concept    # 仅概念
  python stock_screener.py --mode all        # 行业+概念（默认）
"""

import akshare as ak
import pandas as pd
import time
import sys
import json
import argparse
from datetime import datetime, timedelta
from tqdm import tqdm

# ============================================================
# 参数配置
# ============================================================
MA_PERIOD      = 250     # 年线周期（交易日）
MA_THRESHOLD   = 0.05    # 接近年线的偏离阈值 ±5%
KDJ_J_MAX      = 13      # J 值上限（超卖信号）
KDJ_PERIOD     = 9
HISTORY_DAYS   = 400     # 拉取历史 K 线天数
SLEEP_BETWEEN  = 0.3     # 请求间隔（秒）
OUTPUT_CSV     = "result.csv"
OUTPUT_JSON    = "result.json"

# ============================================================
# KDJ 计算
# ============================================================
def calc_kdj(df, period=9):
    low_min  = df['最低'].rolling(window=period).min()
    high_max = df['最高'].rolling(window=period).max()
    rsv = (df['收盘'] - low_min) / (high_max - low_min + 1e-10) * 100
    k = rsv.ewm(com=2, adjust=False).mean()
    d = k.ewm(com=2, adjust=False).mean()
    j = 3 * k - 2 * d
    df = df.copy()
    df['K'] = k
    df['D'] = d
    df['J'] = j
    return df


# ============================================================
# 单只股票指标
# ============================================================
def get_stock_indicators(symbol, name):
    try:
        start = (datetime.today() - timedelta(days=HISTORY_DAYS + 50)).strftime('%Y%m%d')
        end   = datetime.today().strftime('%Y%m%d')
        df = ak.stock_zh_a_hist(
            symbol=symbol, period="daily",
            start_date=start, end_date=end, adjust="qfq"
        )
        if df is None or len(df) < MA_PERIOD:
            return None

        df = df.sort_values('日期').reset_index(drop=True)
        df['MA250'] = df['收盘'].rolling(window=MA_PERIOD).mean()
        df = calc_kdj(df, period=KDJ_PERIOD)

        latest   = df.iloc[-1]
        prev     = df.iloc[-2] if len(df) >= 2 else latest
        close    = latest['收盘']
        ma250    = latest['MA250']
        j_val    = latest['J']

        if pd.isna(ma250) or pd.isna(j_val):
            return None

        deviation  = (close - ma250) / ma250
        change_pct = (close - prev['收盘']) / prev['收盘'] * 100 if prev['收盘'] else 0

        # 近5日量能趋势
        vol5     = df['成交量'].iloc[-5:].mean() if len(df) >= 5 else 0
        vol10    = df['成交量'].iloc[-10:].mean() if len(df) >= 10 else 0
        vol_trend = "放量" if vol5 > vol10 * 1.2 else ("缩量" if vol5 < vol10 * 0.8 else "平量")

        # 信号强度评分 (0-100)
        j_score  = max(0, (KDJ_J_MAX - j_val) / KDJ_J_MAX * 50)   # J越低分越高
        dev_score = (1 - abs(deviation) / MA_THRESHOLD) * 50        # 越接近年线分越高
        signal_score = round(j_score + dev_score)

        return {
            'symbol':       symbol,
            'name':         name,
            'close':        round(close, 2),
            'ma250':        round(ma250, 2),
            'deviation':    round(deviation * 100, 2),
            'change_pct':   round(change_pct, 2),
            'K':            round(latest['K'], 2),
            'D':            round(latest['D'], 2),
            'J':            round(j_val, 2),
            'vol_trend':    vol_trend,
            'signal_score': signal_score,
        }
    except Exception:
        return None


# ============================================================
# 板块分析（行业 & 概念通用）
# ============================================================
def analyze_board(board_name, stocks_in_board, all_cons_df, source='industry'):
    analysis = {
        'name':           board_name,
        'source':         source,       # 'industry' | 'concept'
        'total_stocks':   len(all_cons_df) if all_cons_df is not None else 0,
        'hit_stocks':     len(stocks_in_board),
        'hit_rate':       0.0,
        'avg_change':     0.0,
        'up_count':       0,
        'down_count':     0,
        'strength':       '中性',
        'strength_score': 50,
        'fund_flow':      '未知',
        'summary':        '',
    }

    if all_cons_df is not None and len(all_cons_df) > 0:
        analysis['total_stocks'] = len(all_cons_df)
        analysis['hit_rate'] = round(len(stocks_in_board) / len(all_cons_df) * 100, 1)

        change_col = None
        for col in ['涨跌幅', '今日涨跌幅', 'change_pct']:
            if col in all_cons_df.columns:
                change_col = col
                break

        if change_col:
            avg_change = all_cons_df[change_col].mean()
            analysis['avg_change'] = round(float(avg_change), 2)
            analysis['up_count']   = int((all_cons_df[change_col] > 0).sum())
            analysis['down_count'] = int((all_cons_df[change_col] < 0).sum())

            up_ratio = analysis['up_count'] / max(analysis['total_stocks'], 1)
            if avg_change > 2 and up_ratio > 0.7:
                analysis['strength'] = '强势';  analysis['strength_score'] = 85
            elif avg_change > 0.5 and up_ratio > 0.55:
                analysis['strength'] = '偏强';  analysis['strength_score'] = 65
            elif avg_change < -2 and up_ratio < 0.3:
                analysis['strength'] = '弱势';  analysis['strength_score'] = 20
            elif avg_change < -0.5 and up_ratio < 0.45:
                analysis['strength'] = '偏弱';  analysis['strength_score'] = 35
            else:
                analysis['strength'] = '中性';  analysis['strength_score'] = 50

    hit    = analysis['hit_stocks']
    total  = analysis['total_stocks']
    strength = analysis['strength']
    avg_chg  = analysis['avg_change']
    sign     = '↑' if avg_chg >= 0 else '↓'
    src_label = '行业' if source == 'industry' else '概念'

    if hit > 0:
        analysis['summary'] = (
            f"{board_name}{src_label}今日{strength}，平均涨跌幅{sign}{abs(avg_chg):.2f}%，"
            f"共{total}只成分股中有{hit}只接近年线且KDJ超卖，"
            f"{'具备较好的布局窗口' if strength in ['偏弱','弱势'] else '需关注趋势变化'}。"
        )
    else:
        analysis['summary'] = (
            f"{board_name}{src_label}今日{strength}，平均涨跌幅{sign}{abs(avg_chg):.2f}%，"
            f"当前无成分股同时满足年线+KDJ超卖条件。"
        )

    return analysis


# ============================================================
# 扫描一批板块（行业 or 概念），返回命中股票和板块分析
# ============================================================
def scan_boards(board_df, fetch_cons_fn, source_label, seen_symbols):
    """
    board_df      : 板块列表 DataFrame（含 '板块名称' 列）
    fetch_cons_fn : 获取板块成分股的函数，接受 symbol=板块名 参数
    source_label  : 'industry' | 'concept'
    seen_symbols  : 已处理的股票 set（跨板块去重用）
    返回 (board_stocks_map, hit_map)
    """
    board_stocks = {}   # board_name -> [symbol, ...]
    local_seen   = set()

    print(f"\n  获取板块成分股...")
    for _, row in tqdm(board_df.iterrows(), total=len(board_df), desc=f"  {'行业' if source_label=='industry' else '概念'}扫描"):
        board_name = row.get('板块名称', row.iloc[0])
        try:
            cons = fetch_cons_fn(symbol=board_name)
            time.sleep(SLEEP_BETWEEN)
        except Exception:
            continue
        if cons is None or len(cons) == 0:
            continue

        board_stocks[board_name] = []
        for _, s in cons.iterrows():
            code = str(s.get('代码', s.iloc[0])).zfill(6)
            name = s.get('名称', s.iloc[1])
            local_seen.add((code, name, board_name))
            board_stocks[board_name].append(code)

    # 去重：已在其他板块处理过的股票跳过
    to_check = {}   # symbol -> (name, board_name)
    for board_name, codes in board_stocks.items():
        for code in codes:
            # 找到 name
            name = code   # fallback
            for (c, n, b) in local_seen:
                if c == code and b == board_name:
                    name = n
                    break
            if code not in seen_symbols and code not in to_check:
                to_check[code] = (name, board_name)

    print(f"  ✅ {len(board_stocks)} 个板块，{len(to_check)} 只新股票待分析")

    # 计算指标
    print(f"  计算指标...")
    hit_map = {}   # symbol -> data
    for symbol, (name, board_name) in tqdm(to_check.items(), desc="  计算指标"):
        data = get_stock_indicators(symbol, name)
        time.sleep(SLEEP_BETWEEN)
        if data is None:
            continue
        if abs(data['deviation']) <= MA_THRESHOLD * 100 and data['J'] < KDJ_J_MAX:
            data['board'] = board_name
            data['source'] = source_label
            hit_map[symbol] = data
        seen_symbols.add(symbol)

    print(f"  ✅ 命中 {len(hit_map)} 只股票")
    return board_stocks, hit_map


# ============================================================
# 主流程
# ============================================================
def main(output_json=None, mode='all'):
    print("=" * 60)
    print("  A股选股器  |  年线附近 + KDJ 超卖")
    print(f"  条件：年线偏离 ±{MA_THRESHOLD*100:.0f}%  且  J值 < {KDJ_J_MAX}")
    print(f"  模式：{mode} (all=行业+概念, industry=仅行业, concept=仅概念)")
    print("=" * 60)

    run_industry = mode in ('all', 'industry')
    run_concept  = mode in ('all', 'concept')

    seen_symbols = set()   # 全局去重
    all_hit_map  = {}      # symbol -> data (合并行业+概念)

    # ================================================================
    # Part A: 行业板块
    # ================================================================
    industry_boards_out = []
    if run_industry:
        print("\n[行业] 获取行业板块列表...")
        try:
            industry_df = ak.stock_board_industry_name_em()
        except Exception as e:
            print(f"  ❌ 失败：{e}"); sys.exit(1)
        print(f"  ✅ {len(industry_df)} 个行业板块")

        ind_board_stocks, ind_hit_map = scan_boards(
            industry_df,
            ak.stock_board_industry_cons_em,
            'industry',
            seen_symbols
        )
        all_hit_map.update(ind_hit_map)

        # 聚合行业分析
        by_board = {}
        for sym, data in ind_hit_map.items():
            by_board.setdefault(data['board'], []).append(data)

        for board_name, stocks in sorted(by_board.items(), key=lambda x: -len(x[1])):
            cons_df = None
            try:
                cons_df = ak.stock_board_industry_cons_em(symbol=board_name)
                time.sleep(SLEEP_BETWEEN)
            except Exception:
                pass
            analysis = analyze_board(board_name, stocks, cons_df, source='industry')
            analysis['stocks'] = sorted(stocks, key=lambda x: -x['signal_score'])
            industry_boards_out.append(analysis)

        print(f"\n  [行业] 完成：命中 {len(ind_hit_map)} 只 / {len(industry_boards_out)} 个行业")

    # ================================================================
    # Part B: 概念板块
    # ================================================================
    concept_boards_out = []
    if run_concept:
        print("\n[概念] 获取概念板块列表...")
        try:
            concept_df = ak.stock_board_concept_name_em()
        except Exception as e:
            print(f"  ❌ 失败：{e}"); sys.exit(1)
        print(f"  ✅ {len(concept_df)} 个概念板块")

        con_board_stocks, con_hit_map = scan_boards(
            concept_df,
            ak.stock_board_concept_cons_em,
            'concept',
            seen_symbols
        )
        all_hit_map.update(con_hit_map)

        # 聚合概念分析
        by_board = {}
        for sym, data in con_hit_map.items():
            by_board.setdefault(data['board'], []).append(data)

        for board_name, stocks in sorted(by_board.items(), key=lambda x: -len(x[1])):
            cons_df = None
            try:
                cons_df = ak.stock_board_concept_cons_em(symbol=board_name)
                time.sleep(SLEEP_BETWEEN)
            except Exception:
                pass
            analysis = analyze_board(board_name, stocks, cons_df, source='concept')
            analysis['stocks'] = sorted(stocks, key=lambda x: -x['signal_score'])
            concept_boards_out.append(analysis)

        print(f"\n  [概念] 完成：命中 {len(con_hit_map)} 只 / {len(concept_boards_out)} 个概念板块")

    # ================================================================
    # 输出
    # ================================================================
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    result = {
        'status':      'ok',
        'updated_at':  now,
        'total_hit':   len(all_hit_map),
        'industry_hit': len([v for v in all_hit_map.values() if v.get('source') == 'industry']),
        'concept_hit':  len([v for v in all_hit_map.values() if v.get('source') == 'concept']),
        'industries':  industry_boards_out,
        'concepts':    concept_boards_out,
        'params': {
            'ma_threshold_pct': MA_THRESHOLD * 100,
            'kdj_j_max':        KDJ_J_MAX,
            'ma_period':        MA_PERIOD,
            'mode':             mode,
        }
    }

    json_path = output_json or OUTPUT_JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n📁 JSON 已保存：{json_path}")

    # CSV
    rows = []
    for ind_data in industry_boards_out + concept_boards_out:
        for s in ind_data.get('stocks', []):
            rows.append(s)
    if rows:
        pd.DataFrame(rows).to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
        print(f"📁 CSV  已保存：{OUTPUT_CSV}")

    # 控制台摘要
    print(f"\n{'='*60}")
    print(f"  完成！{now}")
    print(f"  总命中：{len(all_hit_map)} 只")
    if run_industry:
        print(f"  行业板块：{len([v for v in all_hit_map.values() if v.get('source')=='industry'])} 只 / {len(industry_boards_out)} 个行业")
    if run_concept:
        print(f"  概念板块：{len([v for v in all_hit_map.values() if v.get('source')=='concept'])} 只 / {len(concept_boards_out)} 个概念")
    print(f"{'='*60}\n")

    if run_industry and industry_boards_out:
        print("── 行业板块命中 ──")
        for ind in industry_boards_out:
            print(f"【{ind['name']}】{ind['hit_stocks']}只  {ind['strength']}  {ind['avg_change']:+.2f}%")
            for s in ind['stocks']:
                print(f"    {s['symbol']} {s['name']:<8} 现价{s['close']:.2f}  "
                      f"年线{s['ma250']:.2f}  偏离{s['deviation']:+.2f}%  "
                      f"J={s['J']:.1f}  信号{s['signal_score']}")
            print()

    if run_concept and concept_boards_out:
        print("── 概念板块命中 ──")
        for con in concept_boards_out:
            print(f"【{con['name']}】{con['hit_stocks']}只  {con['strength']}  {con['avg_change']:+.2f}%")
            for s in con['stocks']:
                print(f"    {s['symbol']} {s['name']:<8} 现价{s['close']:.2f}  "
                      f"年线{s['ma250']:.2f}  偏离{s['deviation']:+.2f}%  "
                      f"J={s['J']:.1f}  信号{s['signal_score']}")
            print()

    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=str, default=None, help='JSON输出路径')
    parser.add_argument('--mode',   type=str, default='all',
                        choices=['all', 'industry', 'concept'],
                        help='扫描模式：all=行业+概念(默认), industry=仅行业, concept=仅概念')
    args = parser.parse_args()
    main(output_json=args.output, mode=args.mode)

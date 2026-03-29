#!/bin/bash
# A股板块数据自动更新脚本
# 每个工作日运行一次，更新行业和概念板块数据

LOG_FILE="/tmp/stock_auto_update.log"
OUTPUT_DIR="/Users/mobvoi/Documents/projects/opencode/agent/apps/stock/stock-analyzer/data"

echo "========================================" >> "$LOG_FILE"
echo "开始更新: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"

cd /Users/mobvoi/Documents/projects/opencode/agent/apps/stock/stock_screener

# 运行采集脚本
python3 stock_scraper_simple.py --output-dir "$OUTPUT_DIR" >> "$LOG_FILE" 2>&1

echo "更新完成: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

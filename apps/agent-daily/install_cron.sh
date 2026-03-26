#!/bin/bash
# 安装 crontab 定时任务：每天 06:00 自动运行

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="/usr/bin/python3"
LOG="$SCRIPT_DIR/output/cron.log"

CRON_JOB="0 6 * * * cd $SCRIPT_DIR && $PYTHON main.py >> $LOG 2>&1"

# 检查是否已安装
if crontab -l 2>/dev/null | grep -q "agent-daily"; then
    echo "crontab 任务已存在，跳过"
else
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ crontab 已安装：每天 06:00 自动运行"
fi

echo "当前 crontab："
crontab -l

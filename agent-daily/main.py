"""
Agent 每日情报系统 - 主入口
用法：
  python main.py          # 运行采集+摘要+渲染
  python main.py --serve  # 只启动 HTTP server
  python main.py --fetch-only  # 只采集，不生成摘要（调试用）
"""
import argparse
import logging
import sys
import yaml
from datetime import datetime, timedelta, timezone
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import zoneinfo

from models import Article
from summarizer import summarize_articles
from renderer import render_daily

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def load_config(path: str = "config.yaml") -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_fetch(config: dict) -> list[Article]:
    """执行所有数据源采集，返回合并后的文章列表"""
    articles: dict[str, Article] = {}
    keywords = config.get("keywords", [])

    # 1. RSS（官方博客 + 技术媒体 + 国内媒体）
    if config.get("sources", {}).get("rss_feeds", {}).get("enabled"):
        log.info("📰 抓取 RSS feeds...")
        from fetchers.rss_fetcher import fetch_rss
        cfg = config["sources"]["rss_feeds"]
        items = fetch_rss(cfg["feeds"], keywords, keyword_filter=True)
        log.info(f"  RSS: {len(items)} 条")
        for a in items:
            articles[a.id] = a

    # 2. GitHub Trending
    if config.get("sources", {}).get("github_trending", {}).get("enabled"):
        log.info("💻 抓取 GitHub Trending...")
        from fetchers.github_fetcher import fetch_github_trending
        cfg = config["sources"]["github_trending"]
        items = fetch_github_trending(cfg["languages"], cfg["period"], keywords)
        log.info(f"  GitHub: {len(items)} 条")
        for a in items:
            articles[a.id] = a

    # 3. Hacker News
    if config.get("sources", {}).get("hackernews", {}).get("enabled"):
        log.info("🔥 抓取 Hacker News...")
        from fetchers.hackernews_fetcher import fetch_hackernews
        cfg = config["sources"]["hackernews"]
        items = fetch_hackernews(cfg["min_score"], cfg["max_items"], keywords)
        log.info(f"  HN: {len(items)} 条")
        for a in items:
            articles[a.id] = a

    # 4. 官网爬取
    if config.get("sources", {}).get("websites", {}).get("enabled", True):
        log.info("🌐 爬取官网...")
        from fetchers.website_fetcher import fetch_websites
        window = config.get("time_window_days", 3)
        items = fetch_websites(keywords, time_window_days=window)
        log.info(f"  官网: {len(items)} 条")
        for a in items:
            articles[a.id] = a

    # 5. 微信公众号（已移除）

    result = list(articles.values())
    log.info(f"✅ 总计采集 {len(result)} 条（去重后）")
    return result


def filter_by_window(articles: list[Article], config: dict) -> list[Article]:
    """
    只保留「昨天」（北京时间）发布的文章。
    GitHub Trending 没有具体时间，直接保留。
    published_at 为 None 的也保留（网站爬取通常无时间戳）。
    time_window_days 作为向前容差（默认 1），但上限严格截止到昨天。
    """
    CST = zoneinfo.ZoneInfo("Asia/Shanghai")
    days = config.get("time_window_days", 1)
    now_cst = datetime.now(CST)
    yesterday = (now_cst - timedelta(days=1)).date()   # 上限：昨天（含）
    cutoff    = (now_cst - timedelta(days=days)).date() # 下限：N天前

    kept, skipped = [], 0
    for a in articles:
        if a.category == "github":
            kept.append(a)
            continue
        if a.published_at is None:
            kept.append(a)
            continue
        pub_date = a.published_at.astimezone(CST).date()
        if cutoff <= pub_date <= yesterday:   # ← 加上上限，今天的不要
            kept.append(a)
        else:
            skipped += 1

    log.info(f"📅 时间过滤：保留 {len(kept)} 条（{cutoff} ~ {yesterday}），过滤掉 {skipped} 条")
    return kept


def run_summarize(articles: list[Article], config: dict) -> list[Article]:
    """AI 摘要"""
    aws_config = config.get("aws", {})
    log.info(f"🤖 开始 AI 摘要（共 {len(articles)} 条）...")
    return summarize_articles(articles, aws_config)


def run_render(articles: list[Article], config: dict) -> str:
    """生成 HTML 日报（数据归属昨天）"""
    output_dir = config.get("output", {}).get("dir", "./output")
    CST = zoneinfo.ZoneInfo("Asia/Shanghai")
    yesterday = datetime.now(CST) - timedelta(days=1)
    filepath = render_daily(articles, output_dir, yesterday)
    log.info(f"📄 日报生成完成：{filepath}")
    return filepath


def serve(config: dict):
    """启动 HTTP server"""
    output_dir = Path(config.get("output", {}).get("dir", "./output")).resolve()
    port = config.get("output", {}).get("port", 8888)

    os.chdir(output_dir)
    handler = SimpleHTTPRequestHandler
    server = HTTPServer(("0.0.0.0", port), handler)
    log.info(f"🌐 HTTP Server 启动：http://0.0.0.0:{port}")
    log.info(f"   日报地址：http://localhost:{port}/index.html")
    server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description="Agent 每日情报系统")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--serve", action="store_true", help="只启动 HTTP server")
    parser.add_argument("--fetch-only", action="store_true", help="只采集，不生成摘要")
    args = parser.parse_args()

    config = load_config(args.config)

    if args.serve:
        serve(config)
        return

    # 完整流程：采集 → 摘要 → 渲染
    articles = run_fetch(config)

    if not articles:
        log.warning("⚠️  昨天没有相关文章，退出")
        sys.exit(0)

    # 时间窗口过滤
    articles = filter_by_window(articles, config)

    if not articles:
        log.warning("⚠️  昨天没有相关文章，退出")
        sys.exit(0)

    if not args.fetch_only:
        articles = run_summarize(articles, config)
    else:
        log.info("--fetch-only 模式，跳过 AI 摘要")
        for a in articles:
            a.zh_title = a.title
            a.zh_summary = a.content[:300] if a.content else ""
            a.importance = 3

    run_render(articles, config)
    log.info("🎉 完成！")


if __name__ == "__main__":
    main()

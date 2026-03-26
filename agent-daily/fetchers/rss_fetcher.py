"""
通用 RSS 采集器（量子位、机器之心、新智元、OpenAI Blog 等）
"""
import feedparser
import httpx
from typing import Optional

from models import Article
from utils import make_id, is_agent_related, clean_html, truncate, parse_date


def fetch_rss(feeds: list[dict], keywords: list[str], keyword_filter: bool = True) -> list[Article]:
    """
    批量抓取 RSS feeds，返回合并后的 Article 列表。
    feeds: [{"name": "量子位", "url": "...", "category": "cn_media", "language": "zh"}, ...]
    """
    articles: dict[str, Article] = {}

    for feed_cfg in feeds:
        name = feed_cfg.get("name", "Unknown")
        url = feed_cfg.get("url", "")
        category = feed_cfg.get("category", "rss")
        language = feed_cfg.get("language", "en")

        try:
            items = _fetch_single_feed(name, url, category, language, keywords, keyword_filter)
            for item in items:
                if item.id not in articles:
                    articles[item.id] = item
            print(f"[RSS] {name}: 获取 {len(items)} 条")
        except Exception as e:
            print(f"[RSS] {name} 抓取失败: {e}")

    return list(articles.values())


def _fetch_single_feed(
    name: str, url: str, category: str, language: str,
    keywords: list[str], keyword_filter: bool
) -> list[Article]:
    """抓取单个 RSS feed"""
    # feedparser 支持直接传 URL 或已获取的文本
    try:
        # 先用 httpx 获取，设置合理 timeout 和 headers
        resp = httpx.get(url, timeout=20, headers={
            "User-Agent": "Mozilla/5.0 (compatible; AgentDaily/1.0)"
        }, follow_redirects=True)
        feed = feedparser.parse(resp.text)
    except Exception:
        # fallback: feedparser 直接解析
        feed = feedparser.parse(url)

    articles = []
    for entry in feed.entries:
        title = getattr(entry, "title", "").strip()
        link = getattr(entry, "link", "").strip()
        if not title or not link:
            continue

        # 提取正文内容
        content = ""
        if hasattr(entry, "content") and entry.content:
            content = clean_html(entry.content[0].get("value", ""))
        elif hasattr(entry, "summary"):
            content = clean_html(entry.summary or "")
        elif hasattr(entry, "description"):
            content = clean_html(entry.description or "")

        # 关键词过滤（可选）
        if keyword_filter and not is_agent_related(title + " " + content, keywords):
            continue

        published = parse_date(
            getattr(entry, "published", None) or
            getattr(entry, "updated", None)
        )

        articles.append(Article(
            id=make_id(link),
            title=title,
            url=link,
            content=truncate(content, 1500),
            source=name,
            category=category,
            language=language,
            published_at=published,
            score=0.7,
        ))

    return articles

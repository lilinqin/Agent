"""
微信公众号采集器（对接 we-mp-rss 自部署实例）
we-mp-rss: https://github.com/rachelos/we-mp-rss
"""
import httpx
from datetime import datetime, timezone

from models import Article
from utils import make_id, is_agent_related, clean_html, truncate, parse_date


def fetch_wechat(api_base: str, accounts: list[dict], keywords: list[str]) -> list[Article]:
    """
    通过 we-mp-rss API 获取微信公众号最新文章。
    api_base: "http://localhost:8085"
    accounts: [{"name": "量子位", "id": "QbitAI"}, ...]
    """
    articles: dict[str, Article] = {}

    for account in accounts:
        name = account.get("name", "Unknown")
        acc_id = account.get("id", "")
        try:
            items = _fetch_account(api_base, name, acc_id, keywords)
            for item in items:
                if item.id not in articles:
                    articles[item.id] = item
            print(f"[WeChat] {name}: {len(items)} 条")
        except Exception as e:
            print(f"[WeChat] {name} 抓取失败: {e}")

    return list(articles.values())


def _fetch_account(api_base: str, name: str, account_id: str, keywords: list[str]) -> list[Article]:
    """获取单个公众号的最新文章（通过 we-mp-rss RSS 接口）"""
    # we-mp-rss 提供 RSS 接口：GET /rss/{account_id}
    rss_url = f"{api_base}/rss/{account_id}"

    import feedparser
    try:
        resp = httpx.get(rss_url, timeout=15)
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)
    except Exception as e:
        raise RuntimeError(f"we-mp-rss 请求失败: {e}")

    articles = []
    for entry in feed.entries:
        title = getattr(entry, "title", "").strip()
        link = getattr(entry, "link", "").strip()
        if not title or not link:
            continue

        content = ""
        if hasattr(entry, "summary"):
            content = clean_html(entry.summary or "")

        if not is_agent_related(title + " " + content, keywords):
            continue

        published = parse_date(getattr(entry, "published", None))

        articles.append(Article(
            id=make_id(link),
            title=title,
            url=link,
            content=truncate(content, 1500),
            source=f"微信·{name}",
            category="wechat",
            language="zh",
            published_at=published,
            score=0.75,
        ))

    return articles

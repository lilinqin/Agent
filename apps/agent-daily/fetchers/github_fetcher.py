"""
GitHub Trending 采集器
参考 CloudFlare-AI-Insight-Daily 的 github-trending.js
爬取 https://github.com/trending/{language}?since=daily
"""
import httpx
import re
from bs4 import BeautifulSoup
from datetime import datetime, timezone

from models import Article
from utils import make_id, is_agent_related, truncate


GITHUB_TRENDING_URL = "https://github.com/trending/{language}?since={period}"


def fetch_github_trending(
    languages: list[str],
    period: str,
    keywords: list[str],
) -> list[Article]:
    """
    抓取 GitHub Trending，过滤 AI/Agent 相关仓库。
    languages: ["python", "typescript", ""] 空字符串表示所有语言
    """
    articles: dict[str, Article] = {}

    for lang in languages:
        try:
            items = _fetch_trending_page(lang, period, keywords)
            for item in items:
                if item.id not in articles:
                    articles[item.id] = item
            print(f"[GitHub] lang={lang or 'all'}: {len(items)} 条")
        except Exception as e:
            print(f"[GitHub] lang={lang} 抓取失败: {e}")

    return list(articles.values())


def _fetch_trending_page(language: str, period: str, keywords: list[str]) -> list[Article]:
    """抓取单个语言的 Trending 页面"""
    url = GITHUB_TRENDING_URL.format(language=language, period=period)
    resp = httpx.get(url, timeout=20, headers={
        "User-Agent": "Mozilla/5.0 (compatible; AgentDaily/1.0)",
        "Accept-Language": "en-US,en;q=0.9",
    }, follow_redirects=True)
    resp.raise_for_status()

    return _parse_trending_html(resp.text, keywords)


def _parse_trending_html(html: str, keywords: list[str]) -> list[Article]:
    """解析 GitHub Trending HTML"""
    soup = BeautifulSoup(html, "lxml")
    articles = []

    for repo in soup.select("article.Box-row"):
        # 仓库名
        h2 = repo.select_one("h2.h3 a")
        if not h2:
            continue
        repo_path = h2.get("href", "").strip("/")  # owner/repo
        if not repo_path:
            continue

        repo_url = f"https://github.com/{repo_path}"
        repo_name = repo_path.replace("/", " / ")

        # 描述
        desc_el = repo.select_one("p.col-9")
        description = desc_el.get_text(strip=True) if desc_el else ""

        # 关键词过滤
        if not is_agent_related(repo_name + " " + description, keywords):
            continue

        # Stars today
        stars_today_el = repo.select_one("span.d-inline-block.float-sm-right")
        stars_today = stars_today_el.get_text(strip=True) if stars_today_el else ""

        # 语言
        lang_el = repo.select_one("[itemprop='programmingLanguage']")
        lang = lang_el.get_text(strip=True) if lang_el else ""

        content = description
        if stars_today:
            content += f"\n今日新增 Star：{stars_today}"
        if lang:
            content += f"\n主要语言：{lang}"

        articles.append(Article(
            id=make_id(repo_url),
            title=repo_name,
            url=repo_url,
            content=content,
            source="GitHub Trending",
            category="github",
            language="en",
            published_at=datetime.now(timezone.utc),
            score=0.8,
        ))

    return articles

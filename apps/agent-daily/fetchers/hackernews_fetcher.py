"""
Hacker News 采集器（双模式）
1. Top Stories：抓热门帖子，关键词过滤
2. Algolia 搜索：按关键词直接搜索，精准捕捉 agent 相关话题
"""
import httpx
import json
from datetime import datetime, timezone, timedelta
from typing import Optional

from models import Article
from utils import make_id, is_agent_related, truncate


HN_API = "https://hacker-news.firebaseio.com/v0"
HN_ALGOLIA = "https://hn.algolia.com/api/v1/search_by_date"

# Agent 热门话题搜索词 —— 与 Algolia 精准匹配
SEARCH_QUERIES = [
    # 2026 热点
    "harness engineering",
    "context engineering",
    "CLAUDE.md agent",
    "SKILL.md",
    "agent skills anthropic",
    # 经典
    "llm agent",
    "agentic AI",
    "MCP model context protocol",
    "multi-agent system",
    "tool calling LLM",
    # Claude Code 生态
    "claude code",
    "coding agent workflow",
]


def fetch_hackernews(min_score: int, max_items: int, keywords: list[str]) -> list[Article]:
    """双模式抓取：Top Stories 过滤 + Algolia 关键词搜索"""
    articles: dict[str, Article] = {}

    # 模式1：Top Stories
    for a in _fetch_top_stories(min_score, max_items, keywords):
        articles[a.id] = a

    # 模式2：Algolia 关键词搜索（最近 3 天）
    for a in _fetch_algolia_search(keywords):
        if a.id not in articles:
            articles[a.id] = a

    result = list(articles.values())
    # 按优先级排序
    now_ts = datetime.now(timezone.utc).timestamp()
    for a in result:
        a.score = _priority_score(a, now_ts)
    result.sort(key=lambda a: a.score, reverse=True)
    return result


def _fetch_top_stories(min_score: int, max_items: int, keywords: list[str]) -> list[Article]:
    try:
        resp = httpx.get(f"{HN_API}/topstories.json", timeout=15)
        resp.raise_for_status()
        story_ids: list[int] = resp.json()[:100]
    except Exception as e:
        print(f"[HN] Top stories 获取失败: {e}")
        return []

    articles = []
    for story_id in story_ids:
        if len(articles) >= max_items:
            break
        try:
            item = _fetch_story(story_id)
            if item and item.score >= min_score:
                articles.append(item)
        except Exception:
            continue

    return [a for a in articles if is_agent_related(a.title + " " + a.content, keywords)]


def _fetch_algolia_search(keywords: list[str]) -> list[Article]:
    """用 Algolia API 按关键词搜索最近 3 天的帖子"""
    articles: dict[str, Article] = {}
    cutoff_ts = int((datetime.now(timezone.utc) - timedelta(days=3)).timestamp())

    for query in SEARCH_QUERIES:
        try:
            resp = httpx.get(HN_ALGOLIA, params={
                "query": query,
                "tags": "story",
                "hitsPerPage": 15,
                "numericFilters": f"created_at_i>{cutoff_ts},points>10",
            }, timeout=10)
            resp.raise_for_status()
            hits = resp.json().get("hits", [])

            for hit in hits:
                url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                title = hit.get("title", "").strip()
                if not title:
                    continue
                article = Article(
                    id=make_id(url),
                    title=title,
                    url=url,
                    content=truncate(hit.get("story_text") or "", 500),
                    source="Hacker News",
                    category="hackernews",
                    language="en",
                    published_at=datetime.fromtimestamp(hit.get("created_at_i", 0), tz=timezone.utc),
                    score=float(hit.get("points", 0)),
                    tags=[f"{hit.get('num_comments', 0)} comments"],
                )
                if article.id not in articles:
                    articles[article.id] = article
        except Exception as e:
            print(f"[HN Algolia] query={query!r} 失败: {e}")

    return list(articles.values())


def _fetch_story(story_id: int) -> Optional[Article]:
    resp = httpx.get(f"{HN_API}/item/{story_id}.json", timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if not data or data.get("type") != "story":
        return None

    title = data.get("title", "").strip()
    url = data.get("url", f"https://news.ycombinator.com/item?id={story_id}")
    score = data.get("score", 0)
    timestamp = data.get("time", 0)
    text = data.get("text", "") or ""
    comments = data.get("descendants", 0)

    return Article(
        id=make_id(url),
        title=title,
        url=url,
        content=truncate(text, 500),
        source="Hacker News",
        category="hackernews",
        language="en",
        published_at=datetime.fromtimestamp(timestamp, tz=timezone.utc) if timestamp else None,
        score=float(score),
        tags=[f"{comments} comments"],
    )


def _priority_score(article: Article, now_ts: float) -> float:
    if article.published_at:
        age_hours = (now_ts - article.published_at.timestamp()) / 3600
        recency = max(0.0, 1.0 - age_hours / 72)  # 3天内线性衰减
    else:
        recency = 0.5
    engagement = min(1.0, float(article.score) / 300)
    return recency * engagement

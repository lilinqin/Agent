"""
arXiv 论文采集器
参考：arXiv 官方 Atom API
"""
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional

from models import Article
from utils import make_id, is_agent_related, truncate, parse_date


ARXIV_API = "http://export.arxiv.org/api/query"
ARXIV_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def fetch_arxiv(queries: list[str], max_results: int, keywords: list[str]) -> list[Article]:
    """
    从 arXiv API 抓取 Agent 相关论文。
    每个 query 单独请求，结果合并去重。
    """
    articles: dict[str, Article] = {}

    for query in queries:
        params = {
            "search_query": query,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        try:
            resp = httpx.get(ARXIV_API, params=params, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            items = _parse_arxiv_xml(resp.text, keywords)
            for item in items:
                if item.id not in articles:
                    articles[item.id] = item
        except Exception as e:
            print(f"[arXiv] 抓取失败 query={query!r}: {e}")

    return list(articles.values())


def _parse_arxiv_xml(xml_text: str, keywords: list[str]) -> list[Article]:
    """解析 arXiv Atom XML，返回 Article 列表"""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    articles = []
    for entry in root.findall("atom:entry", ARXIV_NS):
        title_el = entry.find("atom:title", ARXIV_NS)
        summary_el = entry.find("atom:summary", ARXIV_NS)
        id_el = entry.find("atom:id", ARXIV_NS)
        published_el = entry.find("atom:published", ARXIV_NS)

        if title_el is None or id_el is None:
            continue

        title = (title_el.text or "").strip().replace("\n", " ")
        summary = (summary_el.text or "").strip().replace("\n", " ") if summary_el is not None else ""
        url = (id_el.text or "").strip()
        published = parse_date(published_el.text if published_el is not None else None)

        # 关键词过滤
        if not is_agent_related(title + " " + summary, keywords):
            continue

        authors = [
            (a.find("atom:name", ARXIV_NS).text or "").strip()
            for a in entry.findall("atom:author", ARXIV_NS)
            if a.find("atom:name", ARXIV_NS) is not None
        ]

        articles.append(Article(
            id=make_id(url),
            title=title,
            url=url,
            content=truncate(summary, 1500),
            source="arXiv",
            category="arxiv",
            language="en",
            published_at=published,
            authors=authors,
            score=0.9,
        ))

    return articles

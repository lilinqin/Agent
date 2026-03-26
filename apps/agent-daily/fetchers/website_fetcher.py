"""
官网直接爬取器
针对没有可用 RSS 的来源，通过静态 HTML / JSON API / Playwright 获取文章列表
"""
import httpx
import re
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from typing import Optional

from models import Article
from utils import make_id, is_agent_related, truncate

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# ── 来源配置 ──────────────────────────────────────────────────
WEBSITE_SOURCES = [
    # ── 官方博客 · 国内 ──────────────────────────────────────
    {
        "name": "智源研究院",
        "url": "https://www.baai.ac.cn/news",
        "base_url": "",
        "category": "official_blog/cn",
        "language": "zh",
        "parser": "baai",
    },
    {
        "name": "MiniMax",
        "url": "https://www.minimaxi.com/news",
        "base_url": "https://www.minimaxi.com",
        "category": "official_blog/cn",
        "language": "zh",
        "parser": "minimax",
    },
    {
        "name": "百度飞桨",
        "url": "https://www.paddlepaddle.org.cn/support/news",
        "base_url": "https://www.paddlepaddle.org.cn",
        "category": "official_blog/cn",
        "language": "zh",
        "parser": "paddlepaddle",
    },
    # ── 官方博客 · 国际（RSS 挂了，改爬网页）────────────────
    {
        "name": "Anthropic Blog",
        "url": "https://www.anthropic.com/news",
        "base_url": "https://www.anthropic.com",
        "category": "official_blog/intl",
        "language": "en",
        "parser": "anthropic",
    },
    # ── 国内媒体 ─────────────────────────────────────────────
    {
        "name": "腾讯云AI资讯",
        "url": "https://cloud.tencent.com/developer/news",
        "base_url": "https://cloud.tencent.com",
        "category": "cn_media",
        "language": "zh",
        "parser": "tencent_cloud",
    },
    {
        "name": "腾讯云开发者",
        "url": "https://cloud.tencent.com/developer/column/search?type=article&q=agent",
        "base_url": "https://cloud.tencent.com",
        "category": "cn_media",
        "language": "zh",
        "parser": "tencent_cloud_article",
    },
]

# ── Playwright 来源（需要 JS 渲染）────────────────────────────
PLAYWRIGHT_SOURCES = [
    {
        "name": "Meta AI Blog",
        "url": "https://ai.meta.com/blog/",
        "base_url": "https://ai.meta.com",
        "category": "official_blog/intl",
        "language": "en",
        "parser": "meta_ai",
    },
]

# ── JSON API 来源 ─────────────────────────────────────────────
API_SOURCES = [
    {
        "name": "机器之心",
        "url": "https://www.jiqizhixin.com/api/article_library/articles.json?page=1&per=30",
        "base_url": "https://www.jiqizhixin.com",
        "category": "cn_media",
        "language": "zh",
        "parser": "jiqizhixin",
        "referer": "https://www.jiqizhixin.com/articles",
    },
    {
        "name": "新智元",
        "url": "https://www.aiera.com.cn/wp-json/wp/v2/posts?per_page=20&_fields=id,title,link,date,excerpt",
        "base_url": "https://www.aiera.com.cn",
        "category": "cn_media",
        "language": "zh",
        "parser": "wordpress",
        "referer": "",
    },
]


def fetch_websites(keywords: list[str], time_window_days: int = 3) -> list[Article]:
    """爬取所有配置的官网（静态 + API + Playwright）"""
    articles = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=time_window_days)

    # 静态 HTML 爬取
    for source in WEBSITE_SOURCES:
        try:
            fetched = _fetch_static(source, keywords, cutoff)
            print(f"[Website] {source['name']}: 获取 {len(fetched)} 条")
            articles.extend(fetched)
        except Exception as e:
            print(f"[Website] {source['name']} 失败: {e}")

    # JSON API 爬取
    for source in API_SOURCES:
        try:
            fetched = _fetch_api(source, keywords, cutoff)
            print(f"[Website] {source['name']}: 获取 {len(fetched)} 条")
            articles.extend(fetched)
        except Exception as e:
            print(f"[Website] {source['name']} 失败: {e}")

    # Playwright 爬取
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            for source in PLAYWRIGHT_SOURCES:
                try:
                    fetched = _fetch_playwright(pw, source, keywords, cutoff)
                    print(f"[Website] {source['name']}: 获取 {len(fetched)} 条")
                    articles.extend(fetched)
                except Exception as e:
                    print(f"[Website] {source['name']} 失败: {e}")
    except ImportError:
        print("[Website] Playwright 未安装，跳过需要 JS 渲染的来源")

    return articles


# ── 静态 HTML 爬取 ────────────────────────────────────────────

def _fetch_static(source: dict, keywords: list[str], cutoff: datetime) -> list[Article]:
    parser_fn = _STATIC_PARSERS.get(source["parser"])
    if not parser_fn:
        return []
    resp = httpx.get(source["url"], headers=HEADERS, timeout=15, follow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    return _to_articles(parser_fn(soup, source), source, keywords, cutoff)


# ── JSON API 爬取 ─────────────────────────────────────────────

def _fetch_api(source: dict, keywords: list[str], cutoff: datetime) -> list[Article]:
    parser_fn = _API_PARSERS.get(source["parser"])
    if not parser_fn:
        return []
    hdrs = {**HEADERS}
    if source.get("referer"):
        hdrs["Referer"] = source["referer"]
    resp = httpx.get(source["url"], headers=hdrs, timeout=15, follow_redirects=True)
    resp.raise_for_status()
    data = resp.json()
    return _to_articles(parser_fn(data, source), source, keywords, cutoff)


# ── Playwright 爬取 ───────────────────────────────────────────

_PW_ARGS = ["--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled"]
_PW_UA   = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def _fetch_playwright(pw, source: dict, keywords: list[str], cutoff: datetime) -> list[Article]:
    parser_fn = _PW_PARSERS.get(source["parser"])
    if not parser_fn:
        return []
    browser = pw.chromium.launch(headless=True, args=_PW_ARGS)
    ctx = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent=_PW_UA,
        locale="en-US",
    )
    ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
    page = ctx.new_page()
    try:
        page.goto(source["url"], timeout=20000, wait_until="networkidle")
        html = page.content()
    finally:
        page.close()
        ctx.close()
        browser.close()
    soup = BeautifulSoup(html, "lxml")
    return _to_articles(parser_fn(soup, source), source, keywords, cutoff)


# ── 统一转换为 Article ────────────────────────────────────────

def _to_articles(raw_items: list[dict], source: dict, keywords: list[str], cutoff: datetime) -> list[Article]:
    articles = []
    for item in raw_items:
        title = item.get("title", "").strip()
        url   = item.get("url", "").strip()
        if not title or not url:
            continue
        if not is_agent_related(title + " " + item.get("summary", ""), keywords):
            continue
        pub = item.get("published_at")
        if pub and isinstance(pub, datetime) and pub.tzinfo and pub < cutoff:
            continue
        articles.append(Article(
            id=make_id(url),
            title=title,
            url=url,
            content=truncate(item.get("summary", ""), 500),
            source=source["name"],
            category=source["category"],
            language=source["language"],
            published_at=pub,
            score=0.0,
            tags=[],
        ))
    return articles


# ── 静态 HTML 解析器 ──────────────────────────────────────────

def _parse_baai(soup: BeautifulSoup, source: dict) -> list[dict]:
    """智源研究院"""
    items = []
    for a in soup.find_all("a", href=True):
        title = re.sub(r'\s+', ' ', a.get_text(separator=" ", strip=True)).strip()[:60]
        href  = a["href"]
        if not (("mp.weixin.qq.com" in href) or ("/news/" in href and "baai.ac.cn" in href)):
            continue
        if len(title) < 10:
            continue
        items.append({"title": title, "url": href, "summary": "", "published_at": None})
    return _dedup(items)


def _parse_minimax(soup: BeautifulSoup, source: dict) -> list[dict]:
    """MiniMax 新闻页"""
    items = []
    base = source["base_url"]
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(separator=" ", strip=True)
        if "/news/" not in href or len(text) < 10:
            continue
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
        pub = None
        if date_match:
            try:
                pub = datetime.strptime(date_match.group(1), "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except Exception:
                pass
        title = re.sub(r'文章\d{4}-\d{2}-\d{2}|阅读更多', '', text).strip()
        title = re.sub(r'\s+', ' ', title)[:60].strip()
        if len(title) < 8:
            continue
        full_url = base + href if href.startswith("/") else href
        items.append({"title": title, "url": full_url, "summary": "", "published_at": pub})
    return _dedup(items)


def _parse_paddlepaddle(soup: BeautifulSoup, source: dict) -> list[dict]:
    """百度飞桨"""
    items = []
    for a in soup.find_all("a", href=True):
        href  = a["href"]
        title = re.sub(r'\s+', ' ', a.get_text(separator=" ", strip=True)).strip()[:60]
        if not (("mp.weixin.qq.com" in href) or ("/support/news" in href)):
            continue
        if len(title) < 10:
            continue
        items.append({"title": title, "url": href, "summary": "", "published_at": None})
    return _dedup(items)


def _parse_tencent_cloud(soup: BeautifulSoup, source: dict) -> list[dict]:
    """腾讯云开发者新闻"""
    items = []
    base = source["base_url"]
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/developer/news/" not in href:
            continue
        title_raw = a.get_text(separator=" ", strip=True)
        title = re.sub(r'📷|[\U00010000-\U0010ffff]', '', title_raw)
        title = re.split(r'[。！？\n]', re.sub(r'\s+', ' ', title))[0][:60].strip()
        if len(title) < 8:
            continue
        full_url = base + href if href.startswith("/") else href
        items.append({"title": title, "url": full_url, "summary": "", "published_at": None})
    return _dedup(items)[:30]


def _parse_tencent_cloud_article(soup: BeautifulSoup, source: dict) -> list[dict]:
    """腾讯云开发者社区文章（技术深度文章，包含 Harness/Skill 等内容）"""
    items = []
    base = source["base_url"]
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # 匹配 /developer/article/ 路径
        if "/developer/article/" not in href:
            continue
        title_raw = a.get_text(separator=" ", strip=True)
        title = re.sub(r'[\U00010000-\U0010ffff]', '', title_raw)
        title = re.sub(r'\s+', ' ', title).strip()[:80]
        if len(title) < 10:
            continue
        full_url = base + href if href.startswith("/") else href
        items.append({"title": title, "url": full_url, "summary": "", "published_at": None})
    return _dedup(items)[:20]


def _parse_anthropic(soup: BeautifulSoup, source: dict) -> list[dict]:
    """Anthropic /news — 链接是 /news/slug 相对路径，标题含日期/分类前缀需清理"""
    from datetime import timezone
    import calendar

    items = []
    base = source["base_url"]
    seen_slugs = set()
    date_pat = re.compile(
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),\s+(\d{4})', re.I)
    month_map = {m.lower(): i for i, m in enumerate(calendar.month_abbr) if m}

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith("/news/") or href == "/news/":
            continue
        slug = href.rstrip("/").split("/")[-1]
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        raw = a.get_text(separator=" ", strip=True)

        # 标题格式: "ProductFeb 17, 2026Introducing Claude Sonnet 4.6Some desc..."
        # 1. 先提取日期
        published_at = None
        m = date_pat.search(raw)
        if m:
            try:
                mon = month_map[m.group(1).lower()]
                day = int(m.group(2))
                year = int(m.group(3))
                from datetime import datetime as _dt
                published_at = _dt(year, mon, day, tzinfo=timezone.utc)
            except Exception:
                pass

        # 2. 去掉分类词 + 日期
        clean = re.sub(
            r'^(Products?|Announcements?|Research|Policy|News|Updates?|Blog)\s*', '', raw, flags=re.I)
        clean = date_pat.sub('', clean).strip()
        # 再次去掉可能残留的分类词（某些文本分类词在日期之后）
        clean = re.sub(
            r'^(Products?|Announcements?|Research|Policy|News|Updates?|Blog)\s*', '', clean, flags=re.I).strip()

        # 3. 取第一句作为标题
        title = re.split(r'\s{2,}', clean)[0].strip()[:100]
        if len(title) < 8:
            continue
        full_url = base + href
        items.append({"title": title, "url": full_url, "summary": "", "published_at": published_at})
    return items


def _parse_the_batch(soup: BeautifulSoup, source: dict) -> list[dict]:
    """The Batch — 从首页找最新期链接，取 issue 页内的文章标题"""
    base = source["base_url"]
    items = []
    # 找最新几期的 issue 链接（如 /the-batch/issue-345/）
    issue_links = list({
        a["href"] for a in soup.find_all("a", href=True)
        if re.search(r'/the-batch/issue-\d+', a.get("href", ""))
    })[:3]  # 取最新3期
    all_hrefs = issue_links or ["/the-batch/"]

    seen = set()
    for issue_path in all_hrefs:
        url = base + issue_path if issue_path.startswith("/") else issue_path
        try:
            r = httpx.get(url, headers=HEADERS, timeout=10, follow_redirects=True)
            isoup = BeautifulSoup(r.text, "lxml")
            for a in isoup.find_all("a", href=True):
                href = a["href"]
                if not re.search(r'/the-batch/(issue-\d+|[a-z0-9-]{10,})', href):
                    continue
                title = re.sub(r'\s+', ' ', a.get_text(strip=True)).strip()[:100]
                if len(title) < 12 or href in seen:
                    continue
                seen.add(href)
                full_url = base + href if href.startswith("/") else href
                items.append({"title": title, "url": full_url, "summary": "", "published_at": None})
        except Exception:
            pass
    return items


_STATIC_PARSERS = {
    "baai":                  _parse_baai,
    "minimax":               _parse_minimax,
    "paddlepaddle":          _parse_paddlepaddle,
    "tencent_cloud":         _parse_tencent_cloud,
    "tencent_cloud_article": _parse_tencent_cloud_article,
    "anthropic":             _parse_anthropic,
    "the_batch":             _parse_the_batch,
}


# ── JSON API 解析器 ───────────────────────────────────────────

def _parse_jiqizhixin(data: dict, source: dict) -> list[dict]:
    """机器之心内部 API articles.json"""
    base = source["base_url"]
    articles_raw = data.get("articles", [])
    items = []
    for a in articles_raw:
        slug = a.get("slug", "")
        title = a.get("title", "").strip()
        if not slug or not title:
            continue
        url = f"{base}/articles/{slug}"
        # 解析时间
        pub = None
        pub_str = a.get("publishedAt", "") or a.get("published_at", "")
        if pub_str:
            try:
                pub = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
            except Exception:
                pass
        # 摘要
        summary = ""
        content = a.get("content", "") or ""
        if content:
            text = re.sub(r'<[^>]+>', '', content)
            summary = text[:300].strip()
        items.append({"title": title, "url": url, "summary": summary, "published_at": pub})
    return items


def _parse_wordpress(data, source: dict) -> list[dict]:
    """通用 WordPress REST API（新智元等）"""
    if not isinstance(data, list):
        return []
    items = []
    for post in data:
        title_raw = post.get("title", {})
        title = (title_raw.get("rendered", "") if isinstance(title_raw, dict) else str(title_raw))
        title = re.sub(r'<[^>]+>', '', title).strip()
        url   = post.get("link", "")
        if not title or not url:
            continue
        # 摘要
        exc = post.get("excerpt", {})
        summary_html = exc.get("rendered", "") if isinstance(exc, dict) else ""
        summary = re.sub(r'<[^>]+>', '', summary_html).strip()[:300]
        # 时间
        pub = None
        date_str = post.get("date", "") or post.get("date_gmt", "")
        if date_str:
            try:
                pub = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
            except Exception:
                pass
        items.append({"title": title, "url": url, "summary": summary, "published_at": pub})
    return items


_API_PARSERS = {
    "jiqizhixin": _parse_jiqizhixin,
    "wordpress":  _parse_wordpress,
}


# ── Playwright 解析器 ─────────────────────────────────────────

def _parse_meta_ai(soup: BeautifulSoup, source: dict) -> list[dict]:
    """Meta AI /blog/ — Playwright 渲染后解析"""
    base = source["base_url"]
    items = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/blog/" not in href or href.rstrip("/") == base + "/blog":
            continue
        title = re.sub(r'\s+', ' ', a.get_text(strip=True)).strip()[:100]
        if len(title) < 10 or href in seen:
            continue
        seen.add(href)
        full_url = base + href if href.startswith("/") else href
        items.append({"title": title, "url": full_url, "summary": "", "published_at": None})
    return items


_PW_PARSERS = {
    "meta_ai": _parse_meta_ai,
}


# ── 工具函数 ──────────────────────────────────────────────────

def _dedup(items: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for it in items:
        if it["url"] not in seen:
            seen.add(it["url"])
            unique.append(it)
    return unique

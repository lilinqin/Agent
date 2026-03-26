"""
工具函数：关键词过滤、文本清理、ID生成
"""
import hashlib
import re
from datetime import datetime, timezone
from typing import Optional


def make_id(url: str) -> str:
    """根据 URL 生成唯一 ID"""
    return hashlib.md5(url.encode()).hexdigest()[:12]


def is_agent_related(text: str, keywords: list[str]) -> bool:
    """判断文本是否与 Agent 相关（大小写不敏感）"""
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def clean_html(html: str) -> str:
    """去除 HTML 标签，返回纯文本"""
    # 去除 script/style
    html = re.sub(r'<(script|style)[^>]*>.*?</(script|style)>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # 去除所有标签
    text = re.sub(r'<[^>]+>', ' ', html)
    # 合并空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def truncate(text: str, max_chars: int = 2000) -> str:
    """截断文本，避免超出 LLM 上下文"""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """尝试解析各种日期格式"""
    if not date_str:
        return None
    try:
        from dateutil import parser as dateparser
        dt = dateparser.parse(date_str)
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def now_utc() -> datetime:
    return datetime.now(timezone.utc)

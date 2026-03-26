"""
共用数据模型和工具函数
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Article:
    """统一的文章数据模型"""
    id: str                          # 唯一标识（url hash 或原始 id）
    title: str                       # 原始标题
    url: str                         # 原文链接
    content: str                     # 正文摘要或全文（用于 AI 处理）
    source: str                      # 来源名称，如 "arXiv", "量子位"
    category: str                    # 分类：arxiv / github / hackernews / rss / wechat
    language: str                    # 语言：zh / en
    published_at: Optional[datetime] = None
    authors: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    score: float = 0.0               # 相关性评分（0-1）
    # AI 生成内容（Phase 3 填充）
    zh_title: str = ""               # 中文标题
    zh_summary: str = ""             # 中文详细摘要
    importance: int = 0              # 重要程度 1-5

"""
工具函数测试（TDD - RED 阶段先写好，确保逻辑正确）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from utils import make_id, is_agent_related, clean_html, truncate, parse_date


def test_make_id_returns_12_char_string():
    result = make_id("https://arxiv.org/abs/2501.00001")
    assert isinstance(result, str)
    assert len(result) == 12


def test_make_id_same_url_same_id():
    url = "https://example.com/paper"
    assert make_id(url) == make_id(url)


def test_make_id_different_urls_different_ids():
    assert make_id("https://example.com/a") != make_id("https://example.com/b")


def test_is_agent_related_matches_keyword():
    keywords = ["agent", "智能体", "MCP"]
    assert is_agent_related("Building an AI agent system", keywords) is True


def test_is_agent_related_case_insensitive():
    keywords = ["agent"]
    assert is_agent_related("Multi-Agent Framework", keywords) is True
    assert is_agent_related("AGENT LOOP", keywords) is True


def test_is_agent_related_no_match():
    keywords = ["agent", "智能体"]
    assert is_agent_related("How to bake a cake", keywords) is False


def test_is_agent_related_chinese():
    keywords = ["智能体", "agent"]
    assert is_agent_related("大模型智能体的最新进展", keywords) is True


def test_clean_html_removes_tags():
    html = "<p>Hello <b>World</b></p>"
    assert clean_html(html) == "Hello World"


def test_clean_html_removes_script():
    html = "<p>Content</p><script>alert('xss')</script>"
    result = clean_html(html)
    assert "alert" not in result
    assert "Content" in result


def test_clean_html_collapses_whitespace():
    html = "<p>  Hello   World  </p>"
    result = clean_html(html)
    assert "  " not in result


def test_truncate_short_text_unchanged():
    text = "short text"
    assert truncate(text, max_chars=100) == text


def test_truncate_long_text_cut():
    text = "a" * 3000
    result = truncate(text, max_chars=2000)
    assert len(result) <= 2004  # 2000 + "..."
    assert result.endswith("...")


def test_parse_date_iso_format():
    result = parse_date("2026-03-24T10:00:00Z")
    assert result is not None
    assert result.year == 2026
    assert result.month == 3
    assert result.day == 24


def test_parse_date_none_returns_none():
    assert parse_date(None) is None


def test_parse_date_invalid_returns_none():
    assert parse_date("not-a-date") is None

"""
快速验证 AI 摘要是否能正常调用 AWS Bedrock
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import Article
from summarizer import summarize_articles
from datetime import datetime, timezone

def test_summarize_single_article():
    """测试对单篇文章生成摘要（真实调用 Bedrock）"""
    article = Article(
        id="test001",
        title="ReAct: Synergizing Reasoning and Acting in Language Models",
        url="https://arxiv.org/abs/2210.03629",
        content="We explore the use of LLMs to generate both reasoning traces and task-specific actions in an interleaved manner, allowing for greater synergy between the two. ReAct prompts LLMs to generate verbal reasoning traces and actions pertaining to a task in an interleaved manner.",
        source="arXiv",
        category="arxiv",
        language="en",
        published_at=datetime(2026, 3, 24, tzinfo=timezone.utc),
    )

    aws_config = {
        "access_key_id": os.environ.get("AWS_ACCESS_KEY_ID", "YOUR_AWS_ACCESS_KEY_ID"),
        "secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY", "YOUR_AWS_SECRET_ACCESS_KEY"),
        "region": os.environ.get("AWS_REGION", "us-east-1"),
        "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
    }

    result = summarize_articles([article], aws_config)

    assert len(result) == 1
    a = result[0]
    assert a.zh_title, "zh_title 不应为空"
    assert a.zh_summary, "zh_summary 不应为空"
    assert 1 <= a.importance <= 5, f"importance 应在 1-5 之间，实际：{a.importance}"
    assert len(a.zh_summary) > 50, "摘要太短"

    print(f"\n✅ 摘要测试通过:")
    print(f"  zh_title: {a.zh_title}")
    print(f"  importance: {a.importance}")
    print(f"  zh_summary: {a.zh_summary[:100]}...")

if __name__ == "__main__":
    test_summarize_single_article()
    print("PASS")

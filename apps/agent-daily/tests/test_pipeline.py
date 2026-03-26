"""
快速验证完整流程（少量文章）
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import yaml
from datetime import datetime, timezone
from main import run_fetch, run_summarize, run_render

def test_full_pipeline_small():
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    # 只测试 arXiv（最快最稳定）
    config["sources"]["rss_feeds"]["enabled"] = False
    config["sources"]["github_trending"]["enabled"] = False
    config["sources"]["hackernews"]["enabled"] = False
    config["sources"]["huggingface_papers"]["enabled"] = False

    articles = run_fetch(config)
    print(f"\n采集到 {len(articles)} 篇论文")
    assert len(articles) > 0, "应该至少采集到 1 篇论文"

    # 只摘要前 3 篇
    sample = articles[:3]
    summarized = run_summarize(sample, config)
    assert all(a.zh_title for a in summarized), "所有文章应有中文标题"
    assert all(a.zh_summary for a in summarized), "所有文章应有中文摘要"

    path = run_render(summarized, config)
    from pathlib import Path
    assert Path(path).exists(), "HTML 文件应存在"
    content = Path(path).read_text()
    assert "Agent" in content or "agent" in content.lower()
    print(f"✅ 完整流程测试通过，HTML 文件: {path}")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(__file__)))
    test_full_pipeline_small()

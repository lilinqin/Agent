"""
AI 摘要层 - AWS Bedrock Claude Sonnet 4
批量翻译（每批 5 篇），批次失败自动逐篇重试
"""
import json
import boto3

from models import Article


BATCH_PROMPT = """你是一个专注于 AI Agent 领域的资深技术分析师，对以下背景有深刻理解：

【当前最重要的概念演进脉络】
- Prompt Engineering（2022-2024）→ Context Engineering（2025）→ Harness Engineering（2026年2月爆发）
- Harness = Context Engineering + 架构约束 + 熵管理/垃圾回收，是让 Agent 持续稳定工作的完整工作环境
- Agent Skills / SKILL.md：Anthropic 2025年下半年推出的跨平台技能标准，Claude Code/Cursor/Gemini CLI 均支持
- CLAUDE.md：Claude Code 的项目级配置文件，定义 Agent 行为约束
- OpenClaw：2026年爆火的主动式 Agent 产品，将 Skills 推向大众基础设施
- Mitchell Hashimoto（HashiCorp创始人）定义了 "Engineer the Harness" 第五阶段

【重要性评分指南（1-5分）】
- 5分（重大突破）：新模型发布、重大能力突破、行业范式转变的第一手信息
- 4分（重要进展）：Harness/Skill/Context Engineering 实践案例、重要框架更新、头部公司 Agent 落地
- 3分（值得关注）：技术深度分析、开源工具发布、行业调研报告
- 2分（一般资讯）：公司动态、产品小更新、活动资讯
- 1分（参考信息）：泛泛而谈的 AI 文章、无实质内容的新闻稿

请对以下 {n} 篇文章逐一分析，全部用中文输出。

{articles}

请以 JSON 数组格式返回，数组长度必须为 {n}，顺序与输入一致（不要有任何其他文字）：
[
  {{
    "zh_title": "简洁的中文标题（25字以内）",
    "zh_summary": "中文摘要，说明核心内容、技术价值、与 Harness/Skill/Context Engineering 等当前趋势的关联（100-200字）",
    "importance": 1到5的整数
  }},
  ...
]"""

SINGLE_PROMPT = """你是一个专注于 AI Agent 领域的资深技术分析师，深度了解 Harness Engineering、Agent Skills、Context Engineering、CLAUDE.md、SKILL.md 等 2025-2026 年核心概念。

请分析以下文章，用中文输出（不要有任何其他文字）：

来源：{source}
标题：{title}
内容：{content}

请以 JSON 格式返回：
{{
  "zh_title": "简洁的中文标题（25字以内）",
  "zh_summary": "中文摘要，说明核心内容、技术价值、与当前 Agent 领域趋势的关联（100-200字）",
  "importance": 1到5的整数，5=重大突破，4=重要进展，3=值得关注，2=一般资讯，1=参考信息
}}"""

BATCH_SIZE = 5


def summarize_articles(articles: list[Article], aws_config: dict) -> list[Article]:
    """批量调用 Claude，批次失败时自动降级为逐篇重试。"""
    client = _make_bedrock_client(aws_config)
    model_id = aws_config.get("model_id", "us.anthropic.claude-sonnet-4-20250514-v1:0")

    total = len(articles)
    total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_start in range(0, total, BATCH_SIZE):
        batch = articles[batch_start: batch_start + BATCH_SIZE]
        batch_num = batch_start // BATCH_SIZE + 1
        print(f"[Summarizer] 批次 {batch_num}/{total_batches}（{len(batch)} 篇）...")

        try:
            results = _summarize_batch(client, model_id, batch)
            for i, article in enumerate(batch):
                r = results[i] if i < len(results) else {}
                _apply(article, r)
                print(f"  ✓ {article.source}: {article.zh_title[:35]}")
        except Exception as e:
            print(f"[Summarizer] 批次失败（{e}），逐篇重试...")
            for article in batch:
                try:
                    r = _summarize_single(client, model_id, article)
                    _apply(article, r)
                    print(f"  ✓ {article.source}: {article.zh_title[:35]}")
                except Exception as e2:
                    print(f"  ✗ 失败 {article.title[:30]}: {e2}")
                    _fallback(article)

    return articles


def _apply(article: Article, r: dict):
    article.zh_title   = r.get("zh_title", "").strip() or article.title
    article.zh_summary = r.get("zh_summary", "").strip() or article.content[:300]
    article.importance = int(r.get("importance", 3))


def _fallback(article: Article):
    article.zh_title   = article.title
    article.zh_summary = article.content[:300] if article.content else ""
    article.importance = 2


def _summarize_batch(client, model_id: str, batch: list[Article]) -> list[dict]:
    articles_text = ""
    for i, a in enumerate(batch, 1):
        articles_text += f"\n【{i}】来源：{a.source}\n标题：{a.title}\n内容：{(a.content or '')[:600]}\n---"

    prompt = BATCH_PROMPT.format(n=len(batch), articles=articles_text)
    text = _call_claude(client, model_id, prompt, max_tokens=3000)
    text = _extract_json(text)

    # 修复截断的 JSON 数组
    if not text.rstrip().endswith("]"):
        last = text.rfind("}")
        if last != -1:
            text = text[:last + 1] + "\n]"

    results = json.loads(text)
    if not isinstance(results, list):
        raise ValueError(f"期望列表，得到 {type(results)}")
    return results


def _summarize_single(client, model_id: str, article: Article) -> dict:
    prompt = SINGLE_PROMPT.format(
        source=article.source,
        title=article.title,
        content=(article.content or "")[:800],
    )
    text = _call_claude(client, model_id, prompt, max_tokens=600)
    text = _extract_json(text)
    return json.loads(text)


def _call_claude(client, model_id: str, prompt: str, max_tokens: int) -> str:
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": prompt}],
    })
    resp = client.invoke_model(modelId=model_id, body=body)
    resp_body = json.loads(resp["body"].read())
    return resp_body["content"][0]["text"].strip()


def _extract_json(text: str) -> str:
    """从可能带 ```json 包裹的文本中提取 JSON"""
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            p = part.strip()
            if p.startswith("json"):
                p = p[4:].strip()
            if p.startswith("{") or p.startswith("["):
                return p
    return text


def _make_bedrock_client(aws_config: dict):
    return boto3.client(
        service_name="bedrock-runtime",
        region_name=aws_config.get("region", "us-east-1"),
        aws_access_key_id=aws_config.get("access_key_id"),
        aws_secret_access_key=aws_config.get("secret_access_key"),
    )

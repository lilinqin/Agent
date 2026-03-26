# Agent 每日情报系统 - 任务计划

## 目标
构建一个每日自动聚合 Agent 领域最新动态的系统，多源采集 → AI 摘要 → 静态网页展示。
每天凌晨自动运行，早上打开浏览器即可看到昨日 Agent 领域全貌。

## 技术栈
- Python 3.11
- 采集：httpx + feedparser + beautifulsoup4
- AI 摘要：boto3（AWS Bedrock Claude Sonnet 4）
- 网页：单文件 HTML + Tailwind CDN
- 调度：crontab
- 托管：Python http.server

## 信息源（借鉴开源项目）
### 国际
- arXiv cs.AI/cs.MA（官方 API）
- HuggingFace Papers（RSS）
- GitHub Trending AI（爬虫，参考 CloudFlare-AI-Insight-Daily）
- Hacker News（官方 API，参考 openclaw-agents）
- Twitter/X AI 大V（RSSHub 路由）
- OpenAI/Anthropic/DeepMind/Google 官博（RSS）
### 国内
- 量子位（RSS，参考 CloudFlare-AI-Insight-Daily qbit.js）
- 机器之心（RSS，参考 jiqizhixin.js）
- 新智元（RSS，参考 xinzhiyuan.js）
- aibase.com（参考 aibase.js）
- 微信公众号（we-mp-rss API，后续配置）

## 项目结构
```
agent-daily/
├── config.yaml           # 信息源、关键词、AWS 配置
├── fetchers/
│   ├── __init__.py
│   ├── arxiv_fetcher.py
│   ├── github_fetcher.py
│   ├── hackernews_fetcher.py
│   ├── rss_fetcher.py    # 通用 RSS（博客/量子位/机器之心等）
│   └── wechat_fetcher.py # we-mp-rss API 对接
├── summarizer.py         # Claude Bedrock 摘要
├── renderer.py           # 生成 HTML 日报
├── main.py               # 主入口
├── tests/
│   ├── test_fetchers.py
│   ├── test_summarizer.py
│   └── test_renderer.py
└── output/               # 生成的 HTML（gitignore）
    ├── index.html
    └── 2026-03-24.html
```

## 实现阶段

### Phase 1: 项目骨架与配置 [status: pending]
- 创建目录结构
- 写 config.yaml（信息源、关键词、AWS 配置）
- 写 requirements.txt
- 写 README.md

### Phase 2: 数据采集层 [status: pending]
- arxiv_fetcher.py（arXiv 官方 API，关键词过滤 agent）
- rss_fetcher.py（通用 RSS：量子位/机器之心/新智元/HuggingFace/官博等）
- github_fetcher.py（GitHub Trending AI 方向）
- hackernews_fetcher.py（HN Top Stories，关键词过滤）
- wechat_fetcher.py（we-mp-rss API 对接，可选）

### Phase 3: AI 摘要层 [status: pending]
- summarizer.py（boto3 调用 AWS Bedrock Claude Sonnet 4）
- 每条内容生成：标题（中文）+ 详细摘要（3-5句）+ 重要程度评分

### Phase 4: 渲染层 [status: pending]
- renderer.py（生成单文件 HTML 日报）
- 支持分类 Tab：论文 / GitHub / 社区 / 国内媒体
- 每条显示：标题 + 摘要 + 来源标签 + 原文链接

### Phase 5: 主流程与调度 [status: pending]
- main.py（串联所有模块，错误处理，日志）
- 启动 HTTP server
- 配置 crontab 定时任务（每天 06:00）

### Phase 6: 测试与验证 [status: pending]
- 运行完整流程，验证输出
- 检查各信息源是否正常抓取

## 决策记录
- 使用 Python（vs Node.js）：更熟悉的数据处理生态，feedparser/httpx 成熟稳定
- 静态 HTML（vs 数据库）：零依赖，浏览器直接打开，够用
- 借鉴 CloudFlare-AI-Insight-Daily 的数据源模块逻辑
- 借鉴 openclaw-agents 的 HN 优先级评分算法
- 借鉴 BestBlogs 的 Twitter RSS 列表（RSSHub 路由）

## 错误记录
（待填写）

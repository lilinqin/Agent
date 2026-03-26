# 研究发现

## 可借鉴的开源项目

### CloudFlare-AI-Insight-Daily（justlovemaki）
- 数据源模块：aibase.js / github-trending.js / huggingface-papers.js / jiqizhixin.js / papers.js / qbit.js / reddit.js / twitter.js / xiaohu.js / xinzhiyuan.js / newsAggregator.js
- 架构：每个数据源独立 fetch + transform 方法，统一数据格式（id/url/title/content_html）
- 扩展方式：在 src/dataSources/ 新建文件即可
- 用 Gemini 做摘要，我们改成 Claude Bedrock

### openclaw-agents/ai-news-agent（leochen-ailab）
- 信息源：HN + arXiv + Twitter
- 亮点：有优先级评分算法（total = recency × engagement × relevance），Node.js 实现
- 推送：飞书，改成 HTML 文件

### BestBlogs（ginobefun）
- 400 个 RSS 订阅源（170 文章 + 160 Twitter + 30 播客 + 40 视频）
- Twitter 覆盖：OpenAI/Sam Altman/Karpathy/Yann LeCun/Anthropic/Google AI 等 100+ 大V
- 国内媒体：量子位/新智元/AI前线/腾讯技术工程/百度Geek说等
- 提供 BestBlogs_RSS_Twitters.opml 可直接用

### we-mp-rss（rachelos）
- MIT License，Docker 自部署
- 提供 RSS API + Web UI
- 用于订阅微信公众号

## arXiv API
- 官方 API：http://export.arxiv.org/api/query
- 关键词搜索：search_query=ti:agent+OR+abs:agent
- 分类过滤：cat:cs.AI OR cat:cs.MA
- 每次最多返回 100 条，支持分页

## HuggingFace Papers
- RSS：https://huggingface.co/papers.rss（需验证是否可用）
- 或爬取 https://huggingface.co/papers

## GitHub Trending
- 无官方 API，需爬取 https://github.com/trending/python?since=daily&spoken_language_code=
- 或用 RSSHub 路由：/github/trending/daily/{language}

## RSSHub 常用路由（Twitter/X）
- /twitter/user/:id（需配置 Twitter API 或 Cookie）
- 公共实例：https://rsshub.app/twitter/user/sama

## 国内媒体 RSS
- 量子位：https://www.qbitai.com/feed
- 机器之心：https://www.jiqizhixin.com/rss
- 新智元：待验证
- AI前线：待验证

## AWS Bedrock 配置
- Region: us-east-1
- Model: us.anthropic.claude-sonnet-4-20250514-v1:0
- 认证：AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY
- boto3 调用方式：bedrock-runtime invoke_model

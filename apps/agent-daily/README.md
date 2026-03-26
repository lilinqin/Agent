# 🤖 Agent 每日情报系统

每天自动聚合 Agent 领域最新动态，生成中文日报网页。

## 在线访问

🌐 **https://agent-daily.codebanana.app/**

> 可直接在浏览器或 App WebView 中访问，无需登录，无账号体系。

### 隐私说明

| 第三方资源 | 用途 | 是否收集用户信息 |
|-----------|------|----------------|
| Tailwind CSS CDN | 样式 | 仅记录请求 IP（CDN 标准行为） |
| Alpine.js CDN | 交互逻辑 | 同上 |
| Google Fonts | 字体加载 | 仅记录请求 IP（国内可能加载失败，自动 fallback） |
| counterapi.dev | 访问计数展示 | 仅 +1 计数，不收集任何用户信息 |

- ❌ 无 Analytics / 统计追踪
- ❌ 无广告 SDK
- ❌ 无 Cookie、无用户登录
- ✅ 适合在 App WebView 中内嵌

## 信息来源

| 来源 | 类型 | 说明 |
|------|------|------|
| arXiv cs.AI/cs.MA | 学术论文 | Agent 相关最新论文，中文摘要 |
| GitHub Trending | 开源项目 | AI/Agent 方向热门仓库 |
| Hacker News | 技术社区 | AI Agent 相关热帖 |
| 量子位 | 国内媒体 | RSS |
| 机器之心 | 国内媒体 | RSS |
| 新智元 | 国内媒体 | RSS |
| OpenAI Blog | 官方博客 | RSS |
| Anthropic Blog | 官方博客 | RSS |
| Google DeepMind | 官方博客 | RSS |
| HuggingFace Blog | 技术媒体 | RSS |
| LangChain Blog | 技术媒体 | RSS |
| 微信公众号 | 国内平台 | 需自部署 we-mp-rss（可选）|

## 快速开始

```bash
# 1. 安装依赖
/usr/bin/python3 -m pip install -r requirements.txt

# 2. 运行一次（fetch-only 模式，不消耗 AI 额度）
/usr/bin/python3 main.py --fetch-only

# 3. 完整运行（含 AI 摘要）
/usr/bin/python3 main.py

# 4. 启动网页服务
/usr/bin/python3 main.py --serve

# 5. 安装每日定时任务（每天 06:00 自动运行）
bash install_cron.sh
```

## 项目结构

```
agent-daily/
├── config.yaml           # 配置（信息源、关键词、AWS）
├── main.py               # 主入口
├── models.py             # 数据模型
├── utils.py              # 工具函数
├── summarizer.py         # AI 摘要（AWS Bedrock）
├── renderer.py           # HTML 渲染
├── fetchers/
│   ├── arxiv_fetcher.py  # arXiv 论文
│   ├── rss_fetcher.py    # 通用 RSS
│   ├── github_fetcher.py # GitHub Trending
│   ├── hackernews_fetcher.py # Hacker News
│   └── wechat_fetcher.py # 微信公众号（需 we-mp-rss）
├── tests/
│   ├── test_utils.py
│   ├── test_summarizer.py
│   └── test_pipeline.py
└── output/               # 生成的 HTML 日报
    ├── index.html        # 最新一天
    └── 2026-03-24.html
```

## 配置微信公众号（可选）

需要自部署 [we-mp-rss](https://github.com/rachelos/we-mp-rss)：

```bash
git clone https://github.com/rachelos/we-mp-rss
cd we-mp-rss
docker compose up -d
```

部署后在 Web UI 添加公众号，然后在 `config.yaml` 中开启：
```yaml
wechat:
  enabled: true
  api_base: "http://localhost:8085"
```

## 参考项目

- [CloudFlare-AI-Insight-Daily](https://github.com/justlovemaki/CloudFlare-AI-Insight-Daily) — 数据源模块设计
- [openclaw-agents](https://github.com/leochen-ailab/openclaw-agents) — HN 优先级评分算法
- [BestBlogs](https://github.com/ginobefun/BestBlogs) — RSS 订阅源列表
- [we-mp-rss](https://github.com/rachelos/we-mp-rss) — 微信公众号订阅

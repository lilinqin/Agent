# 🤖 Agent 每日情报系统

每天自动聚合 Agent 领域最新动态，通过 AI 生成中文摘要，并渲染成可浏览的 HTML 日报网页。

---

## ✨ 功能特性

- 📰 **多源聚合**：同时抓取论文、开源项目、技术社区、官方博客、国内媒体
- 🤖 **AI 摘要**：调用 AWS Bedrock（Claude）自动生成中文摘要和重要性评分
- 🌐 **网页展示**：生成精美 HTML 日报，支持本地 HTTP 服务浏览
- ⏰ **定时运行**：支持 cron 每天自动执行，无需人工干预
- 🔍 **关键词过滤**：只保留 Agent 相关内容，信噪比高

---

## 📡 信息来源

| 来源 | 类型 | 获取方式 |
|------|------|------|
| GitHub Trending | 开源项目 | HTML 爬取 |
| Hacker News | 技术社区 | API + Algolia 搜索 |
| OpenAI Blog | 官方博客 | RSS |
| Anthropic Blog | 官方博客 | HTML 爬取 |
| Google DeepMind Blog | 官方博客 | RSS |
| Meta AI Blog | 官方博客 | Playwright JS 渲染 |
| Microsoft Research | 官方博客 | RSS |
| AWS Machine Learning | 官方博客 | RSS |
| LangChain Blog | 框架博客 | RSS |
| HuggingFace Blog | 框架博客 | RSS |
| Latent Space | 技术媒体 | RSS |
| The AI Edge | 技术媒体 | RSS |
| Interconnects.ai | 技术媒体 | RSS |
| Mitchell Hashimoto Blog | 技术博客 | RSS |
| Simon Willison's Weblog | 技术博客 | RSS |
| Hamel Husain Blog | 技术博客 | RSS |
| Qwen Blog | 官方博客 | RSS |
| 量子位 | 国内媒体 | RSS |
| InfoQ 中文 | 国内媒体 | RSS |
| 机器之心 | 国内媒体 | JSON API |
| 新智元 | 国内媒体 | WordPress API |
| 智源研究院 | 国内机构 | HTML 爬取 |
| MiniMax | 国内厂商 | HTML 爬取 |
| 百度飞桨 | 国内厂商 | HTML 爬取 |
| 腾讯云 AI 资讯 | 国内媒体 | HTML 爬取 |
| 微信公众号 | 国内平台 | 需自部署 we-mp-rss（可选）|

---

## 🚀 快速开始

### 1. 配置 AWS Bedrock

编辑 `config.yaml`，填入你的 AWS 密钥：

```yaml
aws:
  access_key_id: "YOUR_AWS_ACCESS_KEY_ID"
  secret_access_key: "YOUR_AWS_SECRET_ACCESS_KEY"
  region: "us-east-1"
  model_id: "us.anthropic.claude-sonnet-4-20250514-v1:0"
```

> AWS Bedrock 需要在对应 Region 开通 Claude 模型访问权限。
> IAM 用户需要 `bedrock:InvokeModel` 权限。

### 2. 安装依赖

```bash
cd agent-daily
/usr/bin/python3 -m pip install -r requirements.txt
```

### 3. 运行

```bash
# 仅采集，不调用 AI（调试用，不消耗 AWS 额度）
/usr/bin/python3 main.py --fetch-only

# 完整运行：采集 + AI 摘要 + 生成 HTML 日报
/usr/bin/python3 main.py

# 只启动网页服务（浏览已生成的日报）
/usr/bin/python3 main.py --serve
```

### 4. 浏览日报

启动服务后，打开浏览器访问：

```
http://localhost:8008/index.html
```

---

## ⏰ 定时任务（每天自动运行）

```bash
bash install_cron.sh
```

默认每天 **06:00** 自动运行，生成前一天的情报日报。

查看定时任务：
```bash
crontab -l
```

取消定时任务：
```bash
crontab -e  # 删除对应行
```

---

## 📁 项目结构

```
agent-daily/
├── config.yaml               # 配置文件（信息源、关键词、AWS 凭证）
├── main.py                   # 主入口
├── models.py                 # 数据模型（Article）
├── utils.py                  # 工具函数（关键词过滤等）
├── summarizer.py             # AI 摘要模块（调用 AWS Bedrock）
├── renderer.py               # HTML 渲染模块
├── requirements.txt          # Python 依赖
├── install_cron.sh           # 定时任务安装脚本
├── fetchers/
│   ├── arxiv_fetcher.py      # arXiv 论文抓取
│   ├── rss_fetcher.py        # 通用 RSS 订阅抓取
│   ├── github_fetcher.py     # GitHub Trending 抓取
│   ├── hackernews_fetcher.py # Hacker News 抓取
│   └── wechat_fetcher.py     # 微信公众号（需 we-mp-rss）
├── tests/
│   ├── test_utils.py
│   ├── test_summarizer.py
│   └── test_pipeline.py
└── output/                   # 生成的 HTML 日报目录
    ├── index.html            # 最新日报（每次覆盖）
    └── YYYY-MM-DD.html       # 历史日报归档
```

---

## ⚙️ 配置说明

### 关键词过滤

`config.yaml` 中的 `keywords` 字段控制内容过滤，只有包含这些关键词的文章才会被收录。可按需增减：

```yaml
keywords:
  - agent
  - MCP
  - 智能体
  # ... 更多关键词
```

### 时间窗口

```yaml
time_window_days: 1  # 只收录昨天的内容，增大此值可扩大时间范围
```

### 输出配置

```yaml
output:
  dir: "./output"   # HTML 输出目录
  port: 8008        # 本地服务端口
```

### 开关各数据源

```yaml
sources:
  github_trending:
    enabled: true   # 改为 false 可禁用
  hackernews:
    enabled: true
  rss_feeds:
    enabled: true
```

---

## 🔧 配置微信公众号（可选）

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
  accounts:
    - name: "量子位"
      id: "YOUR_ACCOUNT_ID"
```

---

## 📦 依赖环境

- Python 3.10+
- AWS 账号，开通 Bedrock Claude 模型权限
- 网络可访问 GitHub、arXiv、HackerNews 等境外服务

---

## 参考项目

- [CloudFlare-AI-Insight-Daily](https://github.com/justlovemaki/CloudFlare-AI-Insight-Daily) — 数据源模块设计参考
- [openclaw-agents](https://github.com/leochen-ailab/openclaw-agents) — HN 优先级评分算法参考
- [BestBlogs](https://github.com/ginobefun/BestBlogs) — RSS 订阅源列表参考
- [we-mp-rss](https://github.com/rachelos/we-mp-rss) — 微信公众号订阅方案

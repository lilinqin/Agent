# Agent

> Agent 开发相关项目集合：Web 应用、Skill、学习资料等

## 目录结构

```
Agent/
├── apps/                  # 可运行的 Agent 应用 / 工具产品
│   ├── agent-daily/       # 每日 Agent 情报系统
│   └── stock/             # 股票分析工具集
│       ├── stock-analyzer/
│       └── stock_screener/
├── skills/                # 可复用的 Agent Skill 模块
│   └── open-source/       # 开源 Skill 收录
├── learning/              # 学习资料（渐进式Disclosure）
│   └── architecture/      # 架构原理
│       ├── llm-fundamentals/    # L0: LLM 基础
│       ├── what-is-agent/      # L1: Agent 本质
│       └── agent-paradigms/    # L2: Agent 范式
└── docs/                  # 开发计划与进度
    ├── plan.md            # 开发规划
    └── progress.md        # 进度日志
```

## 项目列表

### 🚀 apps — Web 应用

| 项目 | 描述 | 技术栈 |
|------|------|--------|
| [agent-daily](./apps/agent-daily/README.md) | 每日 Agent 情报系统，聚合 GitHub Trending / HackerNews / RSS，AI 摘要生成 HTML 日报 · [🌐 在线访问](https://agent-daily.codebanana.app/) | Python · AWS Bedrock · Claude |
| [stock-analyzer](./apps/stock/stock-analyzer/) | 股票概念分析工具，支持概念板块、产业链分析 | Next.js · TypeScript |
| [stock_screener](./apps/stock/stock_screener/) | 股票筛选器 | - |

### 🧩 skills — Skill 模块

详见 [skills/open-source/README.md](./skills/open-source/README.md)。

### 📚 learning — 学习资料

渐进式Disclosure学习路径，详见 [learning/README.md](./learning/README.md)。

| 层级 | 内容 | 文件 |
|------|------|------|
| L0 | LLM 基础 | [llm-basics.md](./learning/architecture/llm-fundamentals/llm-basics.md) |
| L1 | Agent 本质 | [agent-intro.md](./learning/architecture/what-is-agent/agent-intro.md) |
| L2 | Agent 范式 | [agent-patterns.md](./learning/architecture/agent-paradigms/agent-patterns.md) |

## 开发计划

详见 [docs/plan.md](./docs/plan.md)，进度记录见 [docs/progress.md](./docs/progress.md)。

## License

MIT

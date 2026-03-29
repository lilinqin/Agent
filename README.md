# Agent

> Agent 开发相关项目集合：Web 应用、Skill、学习资料等

## 目录结构

```
Agent/
├── apps/                  # 可运行的 Agent 应用 / 工具产品
│   ├── agent-daily/       # 每日 Agent 情报系统
│   └── stock/             # 股票分析工具集
├── skills/                # 可复用的 Agent Skill 模块
│   └── open-source/       # 开源 Skill 收录
├── learning/              # 学习资料
│   └── architecture/      # 架构原理
└── docs/                  # 开发计划与进度
```

## 项目列表

### 🚀 apps — Web 应用

| 项目 | 描述 | 技术栈 |
|------|------|--------|
| [agent-daily](./apps/agent-daily/README.md) | 每日 Agent 情报系统，聚合 GitHub Trending / HackerHub / RSS，AI 摘要生成 HTML 日报 · [🌐 在线访问](https://agent-daily.codebanana.app/) | Python · AWS Bedrock · Claude |
| [stock](./apps/stock/README.md) | 股票分析工具集（概念分析、筛选器） | Next.js · Python · TypeScript |

### 🧩 skills — Skill 模块

详见 [skills/open-source/README.md](./skills/open-source/README.md)。

### 📚 learning — 学习资料

详见 [learning/README.md](./learning/README.md)。

| 层级 | 内容 | 文件 |
|------|------|------|
| L0 | LLM 基础 | [llm-basics.md](./learning/architecture/llm-fundamentals/llm-basics.md) |
| L1 | Agent 本质 | [agent-intro.md](./learning/architecture/what-is-agent/agent-intro.md) |
| L2 | Agent 范式 | [agent-patterns.md](./learning/architecture/agent-paradigms/agent-patterns.md) |

## 开发计划

详见 [docs/plan.md](./docs/plan.md)，进度记录见 [docs/progress.md](./docs/progress.md)。

## License

MIT

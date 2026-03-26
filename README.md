# Agent

> Agent 开发相关项目集合：Web 应用、Skill、学习资料等

## 目录结构

```
Agent/
├── apps/                  # 可运行的 Agent 应用 / 工具产品
│   └── agent-daily/       # 每日 Agent 情报系统
├── skills/                # 可复用的 Agent Skill 模块
├── learning/              # 学习资料、笔记、资源整理
└── docs/                  # 开发计划与进度
    ├── plan.md            # 开发规划
    └── progress.md        # 进度日志
```

## 项目列表

### 🚀 apps — Web 应用

| 项目 | 描述 | 技术栈 |
|------|------|--------|
| [agent-daily](./apps/agent-daily/README.md) | 每日 Agent 情报系统，聚合 GitHub Trending / HackerNews / RSS，AI 摘要生成 HTML 日报 · [🌐 在线访问](https://agent-daily.codebanana.app/) | Python · AWS Bedrock · Claude |

### 🧩 skills — Skill 模块

收录常用开源 Agent Skill，详见 [skills/open-source/README.md](./skills/open-source/README.md)。

| Skill | 说明 |
|-------|------|
| planning-with-files | Manus 风格文件化规划，防止上下文丢失 |
| test-driven-development | TDD 流程强制约束 |
| brainstorming | 实现前先对齐需求与设计 |
| ui-ux-pro-max | UI/UX 设计全流程辅助 |
| remotion | 用 React 代码程序化制作视频 |

### 📚 learning — 学习资料

持续整理中，详见 [learning/README.md](./learning/README.md)。

| 目录 | 内容 |
|------|------|
| [architecture/what-is-agent](./learning/architecture/what-is-agent/) | Agent 本质理解：ReAct 循环、Agent vs Workflow、局限分析 |
| [resources/LINKS.md](./learning/resources/LINKS.md) | 优质文档、论文链接收录 |

## 开发计划

详见 [docs/plan.md](./docs/plan.md)，进度记录见 [docs/progress.md](./docs/progress.md)。

## License

MIT

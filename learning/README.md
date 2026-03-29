# Learning

Agent 开发学习资料库。

## 学习路径（推荐顺序）

```
1. llm-fundamentals/    → 大语言模型基础（前置知识）
2. what-is-agent/       → Agent 本质理解
3. agent-paradigms/     → 智能体经典范式
```

---

## 目录结构

```
learning/
├── courses/          # 📚 完整课程仓库（本地下载，不进 git）
│   ├── README.md     # 本地已下载列表
│   └── COURSES.md    # 课程链接收录（进 git）
│
├── architecture/     # 🏗️ Agent 架构原理
│   ├── llm-fundamentals/    # LLM 基础（先学）
│   ├── what-is-agent/       # Agent 概念（再学）
│   └── agent-paradigms/     # 经典范式（后学）
│
├── components/       # 🔧 功能模块（待建设）
│   ├── tools/        # Tool Use / Function Calling
│   ├── memory/       # 短期 / 长期记忆实现
│   ├── planning/     # 任务规划
│   ├── perception/   # 感知（多模态）
│   └── rag/          # RAG / 知识检索
│
└── resources/        # 🔗 优秀文档 / 链接收录
    └── LINKS.md
```

## 快速导航

| 层级 | 内容 | 文件 |
|------|------|------|
| L0 | LLM 基础 | [llm-basics.md](./architecture/llm-fundamentals/llm-basics.md) |
| L1 | Agent 本质 | [agent-intro.md](./architecture/what-is-agent/agent-intro.md) |
| L2 | Agent 范式 | [agent-patterns.md](./architecture/agent-paradigms/agent-patterns.md) |

| 我想了解… | 去哪里 |
|-----------|--------|
| 系统学习 Agent 开发 | [courses/COURSES.md](./courses/COURSES.md) |
| Tool Use / RAG 实现 | [components/](./components/) |
| 优质博客 / 文档链接 | [resources/LINKS.md](./resources/LINKS.md) |

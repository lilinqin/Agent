# 开发计划

> 本文件记录整个 Agent 项目集合的开发规划，按模块分类追踪。

## 总体目标

构建一个以 Agent 开发为核心的项目集合，涵盖：
- **apps/** — 可运行的 Agent Web 应用 / 工具产品
- **skills/** — 可复用的 Agent Skill 模块
- **learning/** — 学习资料、笔记、资源整理

---

## apps/ — Web 应用

| 项目 | 描述 | 状态 |
|------|------|------|
| [agent-daily](../apps/agent-daily/README.md) | Agent 每日情报系统，聚合 GitHub/HN/RSS，AI 摘要并生成日报 | ✅ 完成 v1 |

**待规划：**
- Agent 监控面板（可视化多个 Agent 运行状态）
- 基于 MCP 的 Web 工具集

---

## skills/ — Skill 开发

| Skill | 描述 | 状态 |
|-------|------|------|
| (待开发) | | |

**待规划：**
- 信息检索 Skill
- 代码审查 Skill
- 定时任务 Skill

---

## learning/ — 学习资料

> 渐进式Disclosure：LLM基础 → Agent概念 → 工程范式

| 主题 | 文件 | 状态 |
|------|------|------|
| LLM 基础 | `llm-fundamentals/llm-basics.md` | ✅ 完成 |
| Agent 本质 | `what-is-agent/agent-intro.md` | ✅ 完成 |
| Agent 范式 | `agent-paradigms/agent-patterns.md` | ✅ 完成 |

**待建设：**
- [ ] components/tools/ — Tool Use / Function Calling
- [ ] components/memory/ — 记忆系统
- [ ] components/planning/ — 任务规划
- [ ] components/perception/ — 多模态感知
- [ ] components/rag/ — RAG 实现

**待规划：**
- MCP 协议学习记录
- Context Engineering 资料整理

---

## 里程碑

| 时间 | 目标 |
|------|------|
| 2026 Q1 | agent-daily v1 上线，仓库结构初始化 ✅ |
| 2026 Q2 | 第一个 Skill 开发完成；learning 模块开始积累 |
| 2026 Q3 | apps/ 新增第二个项目；skills/ 达到 3 个可用 Skill |

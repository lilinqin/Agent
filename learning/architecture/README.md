# Agent 架构知识体系

> 从 CTO/技术总监视角整理的技术体系，适合技术战略分享、技术选型、团队培训

---

## 当前进度

| 模块 | 状态 | 说明 |
|------|------|------|
| agent-intro | ✅ 完成 | Agent 本质、ReAct 循环、与 Workflow 的区别 |
| core/reasoning | ✅ 完成 | ReAct、Plan-and-Solve、Reflection 三种范式 |
| core/tool | ✅ 完成 | 工具定义、Function Calling vs ReAct、MCP |
| core/memory | ✅ 完成 | 工作记忆、会话记忆、长期记忆分层 |
| core/sandbox | ✅ 完成 | 权限控制、资源限制、Guardrails、Heartbeat |
| patterns | ⚠️ 部分 | 单智能体完成，多智能体待完善 |
| evaluation | 🔲 待完成 | Agent 评测方法论 |
| skill | ✅ 完成 | 常用 Skill + 参考论文 |
| frameworks | ✅ 完成 | AutoGen、AgentScope、CAMEL、LangGraph 对比 |

---

## 核心要点

### Agent 是什么

> Agent = LLM + 工具调用 + 循环反馈。核心是"感知→决策→行动→观察"的闭环，能把模糊目标转化为可执行行动序列。

### 三大范式

- **ReAct**：动态决策，走一步看一步。适合需要外部工具的开放式任务。
- **Plan-and-Solve**：先规划再执行，稳定但缺乏调整能力。适合结构化任务。
- **Reflection**：执行→反思→优化→重复。用额外调用换准确率。

### 记忆分层

- **工作记忆**：当前任务上下文
- **会话记忆**：多轮对话历史
- **长期记忆**：跨会话知识（向量库）

### 选型决策

- 快速原型 → AutoGen
- 生产级分布式 → AgentScope
- 复杂工作流 → LangGraph

---

## 后续完善方向

1. **evaluation/**: Agent 评测体系（Benchmark、Harness）
2. **patterns/multi-agent/**: 多智能体协作模式
3. **案例补充**: 实际项目中的应用示例

---

## 格式规范

每个模块的文档遵循统一格式：
- 从 CTO/技术总监视角陈述
- "我们"的视角——"我们怎么做"、"我们为什么投入"
- 技术战略思考——每个模块回答"为什么投入"
- 具体例子和踩过的坑
- 参考论文链接
- 一句话总结

详见 [FORMAT.md](./FORMAT.md)

# Agent 架构知识体系

> 一份文档，两种用途：既能应对面试细节考察，又能给 CTO 做技术战略汇报

---

## 当前进度

| 模块 | 状态 | 说明 |
|------|------|------|
| agent-intro | ✅ 完成 | Agent 本质、ReAct 循环 |
| core/reasoning | ✅ 完成 | ReAct、Plan-and-Solve、Reflection |
| core/tool | ✅ 完成 | 工具系统、Function Calling、MCP |
| core/memory | ✅ 完成 | 三层记忆架构 |
| core/sandbox | ✅ 完成 | 安全沙箱、Heartbeat、Guardrails |
| patterns | ⚠️ 部分 | 单智能体完成，多智能体待完善 |
| evaluation | 🔲 待完成 | Agent 评测 |
| frameworks | ✅ 完成 | AutoGen、AgentScope、LangGraph |

---

## 核心要点

### Agent 是什么
> Agent = LLM + 工具调用 + 循环反馈。核心是"感知→决策→行动→观察"的闭环。

### 三大范式
- **ReAct**：动态决策，适合开放式任务
- **Plan-and-Solve**：先规划后执行，适合结构化任务
- **Reflection**：迭代优化，适合高准确率场景

### 记忆分层
- 工作记忆 → 会话记忆 → 长期记忆

### 选型
- 快速原型 → AutoGen
- 生产级 → AgentScope
- 复杂工作流 → LangGraph

---

## 后续完善

1. **evaluation/**: Agent 评测体系
2. **patterns/multi-agent/**: 多智能体协作
3. **案例补充**: 实际项目示例

---

## 格式规范

每份文档包含：

1. **第一性原理**：追本溯源，回答"为什么会出现"、"最根本的限制是什么"
2. **核心概念**：一句话定义
3. **具体解释**：精髓、本质、对比
4. **工程实践**：踩坑、解决方案
5. **当前发展现状**（CTO 视角）
6. **未来展望**（CTO 视角）
7. **面试常见问题**
8. **参考论文**

核心：**不是简单描述是什么，而是回答"为什么"**。追问到最根本的原因。

详见 [FORMAT.md](./FORMAT.md)

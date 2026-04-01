# Agent 架构知识体系

> 一份文档，两种用途：既能应对面试细节考察，又能给 CTO 做技术战略汇报

---

## 当前进度

| 模块 | 状态 | 说明 |
|------|------|------|
| agent-intro | ✅ 完成 | Agent 本质、PEAS 定义、TAO 循环、Workflow vs Agent |
| core/reasoning | ✅ 完成 | ReAct（含形式化定义+4大局限）、Plan-and-Solve、Reflection（成本收益分析）、范式选型决策树 |
| core/tool | ✅ 完成 | 工具三层架构（高频原子/中频受控/低频兜底）、MCP/A2A/ANP 协议、可诊断性原则 |
| core/memory | ✅ 完成 | 四类记忆（工作/情景/语义/感知）、记忆生命周期、RAG 三阶段演化 |
| core/sandbox | ✅ 完成 | 安全沙箱、Heartbeat、Guardrails |
| context | ✅ 完成 | 上下文工程、GSSC 流水线、JIT 上下文、长程任务三大策略、分层架构 |
| patterns | ⚠️ 部分 | 单智能体完成，多智能体待完善 |
| evaluation | ✅ 完成 | BFCL/GAIA/AgentBench 等主流基准、评估方式、工程实践 |
| frameworks | ✅ 完成 | AutoGen、AgentScope、LangGraph |
| harness | ✅ 完成 | Harness Engineering 系统范式，6组件+7设计原则 |

---

## 核心要点

### Agent 是什么
> Agent = LLM + Harness。模型决定做什么，Harness 决定能看到什么、能用什么工具、失败时怎么办。

### 三大推理范式
- **ReAct**：侦探式走一步看一步，动态适应，适合需外部工具的开放任务
- **Plan-and-Solve**：建筑师式先画蓝图，适合逻辑确定的多步推理
- **Reflection**：编辑式写完再校对，用额外调用换取质量，适合不容出错场景

### 四类记忆
- 工作记忆（TTL 临时）→ 情景记忆（具体事件）→ 语义记忆（抽象知识+图谱）→ 感知记忆（多模态）

### 上下文工程
- Context = 有限资源；超过 ~60% 利用率性能下降（上下文腐蚀）
- GSSC 流水线：Gather → Select → Structure → Compress
- 长程任务三策略：压缩整合 + 结构化笔记 + 子代理隔离

### 工具设计
- 三层架构：高频原子（稳定可诊断）/ 中频受控（先读后改）/ 低频兜底（Bash 但有禁区）
- 协议标准化：MCP（工具接入）/ A2A（Agent 协作）/ ANP（网络发现）

### 框架选型
- 快速原型 → AutoGen
- 生产级 → AgentScope
- 复杂工作流 → LangGraph

### 评估
- 工具调用：BFCL（Berkeley Function Calling Leaderboard）
- 综合能力：GAIA（Level 1-3 难度）、SWE-bench（代码 Agent）

---

## 后续完善

1. **patterns/multi-agent/**: 多智能体协作（MCP/A2A 协议实战、orchestration 模式）
2. **agentic-rl/**: Agentic RL 原理（SFT → GRPO → 环境反馈闭环）
3. **案例补充**: Code Agent、Research Agent 实际项目示例

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

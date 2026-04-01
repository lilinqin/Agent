# 来源笔记：hello-agents 课程

**来源**：hello-agents（DataWhale，2026）
**链接**：https://github.com/datawhalechina/Hello-Agents
**日期**：2026-03-31
**类型**：开源课程/教程

---

## 核心内容摘要

### Chapter 4: 智能体经典范式构建

**新增/深化内容**：
- ReAct 的形式化定义：$(th_t, a_t) = \pi(q, (a_1,o_1),...,(a_{t-1},o_{t-1}))$
- ReAct 的 4 大局限（原有只提到 3 个，新增"提示词脆弱性"）
- Plan-and-Solve 的两阶段形式化定义
- Reflection 的成本收益分析表
- 范式选择决策树

**更新决策**：对 reasoning.md 做深化更新，保留原有结构，补充形式化定义和局限分析

### Chapter 8: 记忆与检索

**新增内容**：
- 四类记忆架构（Working/Episodic/Semantic/Perceptual）——比原有三层更细粒度
- 记忆生命周期：编码→存储→检索→整合→遗忘
- RAG 三阶段演化：Naive → Advanced → Modular
- 高级检索策略：MQE（多查询扩展）、HyDE（假设文档嵌入）
- 语义记忆使用 Neo4j 图数据库的设计理由

**更新决策**：对 memory.md 做深化更新，将四类记忆作为三层架构的细化，不替代原有框架

### Chapter 9: 上下文工程

**新建主题**：context/context-engineering.md

核心内容：
- 上下文腐蚀（Context Rot）的 Transformer 架构根因
- GSSC 流水线（Gather-Select-Structure-Compress）
- JIT 上下文 vs 预计算检索
- 长程任务三策略：Compaction / Structured Note-taking / Sub-agent architectures
- L1/L2/L3 分层上下文架构
- 60% 利用率甜蜜区间的工程验证

### Chapter 10: 智能体通信协议

**新增/深化内容到 tool.md**：
- MCP（Model Context Protocol，Anthropic）：标准化 Agent-工具通信
- A2A（Agent-to-Agent Protocol，Google）：点对点 Agent 通信
- ANP（Agent Network Protocol，开源社区）：去中心化服务发现
- 三种协议的对比和选型指南

### Chapter 11: Agentic RL

**未写入知识库**（后续完善 agentic-rl/ 模块时使用）：
- LLM 训练全景：预训练 → SFT → RM → RL（PPO）
- PBRFT vs Agentic RL 的 MDP 框架对比
- Agentic RL 的奖励函数设计（稀疏/密集/混合）
- GRPO 算法（无需奖励模型的 RL 训练）

### Chapter 12: 智能体性能评估

**新建主题**：evaluation/evaluation.md

核心内容：
- 工具调用评估：BFCL（simple/multiple/parallel/irrelevance 四类）
- 通用能力评估：GAIA（Level 1-3）、AgentBench、SWE-bench、WebArena
- 评估方式：LLM Judge、Win Rate、行为轨迹分析
- 工程实践：先建评估再优化、单变量改动、黄金测试集

### Extra09: Agent 应用开发实践踩坑与经验分享

**新增/深化内容**：
- 工具设计 Goldilocks 原则 → 更新至 tool.md
- 可诊断性是可恢复性的前提 → 更新至 tool.md
- 三层工具架构（高频原子/中频受控/低频兜底）→ 更新至 tool.md
- 提示词三层结构（边界层/决策层/恢复层）→ 提炼到 context/context-engineering.md
- 上下文分层管理（L1/L2/L3）→ 更新至 context/context-engineering.md
- 压缩归档 + Summary 机制 → 更新至 context/context-engineering.md

---

## 更新了哪些文档

| 文档 | 更新类型 | 主要改动 |
|------|---------|---------|
| core/reasoning/reasoning.md | 深化 | 形式化定义、4大局限、范式选择决策树 |
| core/memory/memory.md | 深化 | 四类记忆、生命周期、RAG 三阶段演化 |
| core/tool/tool.md | 深化 | 三层工具架构、MCP/A2A/ANP、可诊断性 |
| context/context-engineering.md | 新建 | 完整上下文工程知识体系 |
| evaluation/evaluation.md | 新建 | Agent 评测体系、主流基准 |
| README.md | 更新 | 反映新增模块和更新内容 |

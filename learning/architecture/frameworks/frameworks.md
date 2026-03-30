# 框架对比

> 适用：技术面试、框架选型

---

## 为什么用框架

| 手写 | 框架 |
|------|------|
| 重复造轮子 | 通用组件复用 |
| 多 Agent 协作难扩展 | 内置协调机制 |
| 调试靠 print | 事件回调可观测性 |

---

## 框架选型

| 框架 | 核心思路 | 适合场景 |
|------|----------|----------|
| **AutoGen** | 对话驱动协作 | 多角色软件团队 |
| **AgentScope** | 消息驱动 + 工程化 | 大规模生产系统、分布式 |
| **CAMEL** | 角色扮演 + 引导提示 | 双 Agent 自主协作 |
| **LangGraph** | 图结构建模流程 | 复杂工作流、条件分支 |

---

## AutoGen

把任务解决映射为不同角色 Agent 之间的自动对话。

- AssistantAgent：任务解决者
- UserProxyAgent：人类代理
- RoundRobinGroupChat：轮询群聊

**面试话术**：
> "优势是把复杂协作自然化为对话，不需要自己写状态机。0.7.4 版本转向组合式架构 + 异步优先。"

---

## AgentScope

阿里巴巴开源，专为大规模、高可靠性多智能体系统设计。

- 消息驱动架构：发送方和接收方时间解耦，天然支持高并发
- MsgHub：路由、持久化、分布式通信
- 原生支持分布式部署、容错恢复

**面试话术**：
> "AgentScope 是'智能体操作系统'，AutoGen 是'对话工作室'。生产级系统选 AgentScope，原型快速开发选 AutoGen。"

---

## LangGraph

将 Agent 执行流程建模为**有向图**：
- Node：LLM 调用、工具执行
- Edge：节点跳转逻辑

**核心优势**：天然支持**循环**，实现 Reflection 等迭代工作流特别直观。

---

## 选型决策

| 需求 | 推荐 |
|------|------|
| 快速原型 | AutoGen |
| 生产级分布式 | AgentScope |
| 复杂条件分支 | LangGraph |
| 双 Agent 协作 | CAMEL |

**混合方案最常见**：LangGraph 控主干流程保证确定性，在需要动态判断的节点嵌入 Agent。

---

## 官方文档

- LangChain: https://docs.langchain.com
- LlamaIndex: https://docs.llamaindex.ai
- AutoGen: https://microsoft.github.io/autogen
- CrewAI: https://docs.crewai.com

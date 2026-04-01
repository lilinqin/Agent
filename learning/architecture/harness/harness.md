# Harness Engineering

> 适用场景：技术面试 / 技术战略分享 / AI 系统设计

---

## 核心概念（一句话定义）

Harness 是围绕 LLM 构建的外围控制系统，决定模型能看到什么、能用什么工具、失败时该怎么办——**Agent = LLM + Harness**。

---

## 具体解释

### 为什么重要 / 核心机制

AI 工程方法经历了三次范式演进，背后的共同逻辑是：**一旦模型能力过线，瓶颈就会向系统层外移**。

| 阶段 | 时间 | 关注点 | 核心问题 |
|------|------|--------|---------|
| Prompt Engineering | 2022-2024 | 如何表达需求 | 怎么提问让模型理解任务 |
| Context Engineering | 2025 | 如何提供信息 | 有限窗口下怎么组织上下文 |
| Harness Engineering | 2026- | 如何构建系统 | 怎么让 Agent 可靠、安全地完成任务 |

转折点：2025 年 11 月 Claude Opus 4.5 发布，标志着模型 agentic 能力到达 tipping point，**"用好模型的能力"开始比"提高模型的能力"更重要**。

"Harness"源自马术（马具），模型是野马，harness 是驾驭它的外围系统。

### Harness 的 6 个关键组件

组件构成三层链路：**信息层 → 执行层 → 反馈层**。

**信息层**
1. **Memory & Context Management（记忆与上下文管理）**：解决"当前时刻 Agent 应看到什么信息"——上下文裁剪、压缩、按需检索、外部状态存储
2. **Tools & Skills（工具与技能）**：扩展 Agent 行动能力；工具提供可调用外部能力，skills 提供可复用任务方法

**执行层**
3. **Orchestration & Coordination（编排与协调）**：编排任务流程，协调 Agent 分工，决定何时规划/执行/交接
4. **Infra & Guardrails（基础设施与保障）**：沙箱、权限控制、失败恢复、安全护栏

**反馈层**
5. **Evaluation & Verification（评估与验证）**：内置测试/检查/反馈机制，让 Agent 自行验证工作并修正
6. **Tracing & Observability（追踪与观测）**：执行轨迹、日志、监控、成本分析——让黑箱变透明

---

## 设计原则（7 个 Tricks）

### 信息层：精准比求全更重要

核心矛盾：模型存在 **Context Decay**（上下文衰减），context 越长，对关键信息的注意力越被噪音分散。

- **Trick 1：渐进式披露**：分层加载信息，只在需要时暴露对应层级
  - Level 1 CLAUDE.md：最关键的元规则
  - Level 2 SKILL.md：按需加载的任务能力包
  - Level 3 Reference files：完成当前任务真正需要的细节
- **Trick 2：Tools 越少而精越好**：工具过多导致决策瘫痪。Claude Code 约 20 个工具，团队仍在审视是否需要全部保留。Vercel 精简工具后速度和可靠性显著提升
- **Trick 3：找到 Context Window 利用率的甜蜜区间**：超过阈值后性能开始下降，顶级工程师通常将利用率控制在 60% 以下
- **Trick 4：用 Subagent 做 Context 隔离**：主 agent 重时拆给独立 subagent，Boris Cherny 称为 "context firewall"

### 执行层：任务结构决定执行质量

- **Trick 5：把 Research/Plan/Execute/Verify 分开**：每个阶段独立 session，不在同一 context 里一气呵成。Boris Cherny 的规则：_"Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)"_
- **Trick 6：人应该介入规划而非事后审核**：一行糟糕的计划会生出几百行糟糕的代码，杠杆在上游

### 反馈层：Harness 的复利飞轮

- **Trick 7：构建反馈闭环**：Mitchell Hashimoto 的原则——_"每次 agent 犯错，就工程化地解决这个问题，让它永远不再犯同类错误"_。Boris Cherny 数据：给 Claude 有效验证手段，产出质量通常提升 2-3 倍

---

## 与其他概念的区别

| 概念 | 范围 | 侧重点 |
|------|------|--------|
| Prompt Engineering | 单次调用 | 如何表达指令 |
| Context Engineering | 上下文窗口 | 信息的组织与压缩 |
| **Harness Engineering** | 整套系统 | 环境、工具、评估、反馈的完整闭环 |
| Framework（LangGraph 等） | 执行编排 | 流程控制与组件复用 |

---

## 工程实践

### Openclaw 案例：Harness Engineering 的一次胜利

不依赖模型能力，靠 harness 设计创造 aha moment：
- Gateway 统一对接社交软件
- 内置 Skills 库提供能力集合
- 记忆机制持久积累经验
- Heartbeat 补齐主观能动性
- Soul.md 注入人格

### 踩坑：OpenAI 的 AGENTS.md 教训

尝试用巨大的 AGENTS.md 写全所有规则，发现不可行——context 资源稀缺，大文件占据脑容量，反而忽视重要信息。现在业内最佳实践是分层披露。

---

## 当前发展现状

### AI 前沿专家视角（Anthropic / OpenAI / DeepMind）

> **"The Harness is the Dataset. Competitive advantage is now the trajectories your harness captures."**
> —— Philipp Schmid, DeepMind Staff Engineer

- **Anthropic**：在 harness 上的探索比 OpenAI 领先几个月，带来巨大先发优势。即使模型能力两家基本打平，大多数人仍在用 Claude Code
- **训练即部署（Co-optimization）**：模型和 harness 从一开始就不是分开设计的。Cursor 训练 Composer 1.5、Windsurf 训练 SWE-1.5 都验证了：_"coding 环境本身的质量，对模型最终表现的影响是最大的"_
- **Harness 能力被模型吸收**：tool search、programmatic tool use、compaction、多步工具调用策略等，已逐渐被模型内生化。Boris Cherny：Claude Code 的 harness 每行代码保质期约 2 个月

**主要矛盾**：模型公司在端到端做 harness（Claude Code、Codex），应用公司在自己训模型——竞争边界模糊化

**技术成熟度**：Harness 概念 2026 年才开始作为独立范式被系统讨论，仍处于早期

---

## 未来展望

**下一范式：Coordination Engineering**

随着 multi-agent 世界到来，下一代 AI 产品不是更聪明的单 agent，而是：
- 有效的监工看板
- 让各种 agent/人类节点协作的平台（"小龙虾版飞书"）

四层演进不是替代关系，而是包含关系：
- L1 Prompt Engineering → 解决问答质量
- L2 Context Engineering → 解决认知边界
- L3 Harness Engineering → 解决执行闭环
- L4 Coordination Engineering → 解决组织协同

**终极**：Intention Engineering——人只负责设定目标函数，其余 AI 自行包揽

---

## 深度理解

**Q: Harness Engineering 和 Prompt Engineering 的本质区别是什么？**

> Prompt Engineering 的边界是单次对话；Harness Engineering 的边界是整套系统。当模型能力过线后，瓶颈从"如何表达"转移到"如何构建"。Agent 失败不是因为 prompt 写得不好，而是因为没有反馈闭环、工具太多决策瘫痪、context 超载注意力分散。

**Q: 为什么"Harness 即数据集"这个判断很重要？**

> 静态语料的价值在下降，真正有价值的数据是 agent 在具体业务流程中跑出来的执行轨迹——它看到什么信息、用了什么工具、哪步容易出错。harness 决定了轨迹的质量，高质量轨迹喂回训练，形成飞轮。所以谁能把 harness 跑顺，谁就有更强的数据飞轮，这是当前 AI 竞争的真正护城河。

**Q: 为什么工具越少越好，这不是限制了 Agent 的能力吗？**

> 工具多会导致决策瘫痪和幻觉增加。Agent 的强大不在于工具箱有多少扳手，而在于是否有几把完美的"万能扳手"以及如何高效组合。Vercel 的实践验证了这一点：从完整工具库精简到核心工具后，速度和可靠性都显著提升。

---

## 参考

- 原文：[Harness is the New Dataset：模型智能提升的下一个关键方向](https://mp.weixin.qq.com/s/9qI83Ne-Ac_R9y-yJ6SVnQ)（海外独角兽，Celia & Siqi，2026）
- Boris Cherny（Claude Code 负责人）实践分享
- Mitchell Hashimoto 博客
- Philipp Schmid（DeepMind Staff Engineer）观点

---

## 一句话总结

Harness 是模型能力的乘数器，而非脚手架——当模型智力不再是瓶颈，系统设计的质量决定了 Agent 的上限，执行轨迹本身就是数据，谁的 harness 更好，谁就有更强的智能飞轮。

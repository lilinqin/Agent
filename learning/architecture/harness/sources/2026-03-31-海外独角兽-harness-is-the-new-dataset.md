# 来源笔记：Harness is the New Dataset

| 字段 | 内容 |
|------|------|
| **来源** | 海外独角兽公众号 |
| **作者** | Celia（作者）、Siqi（编辑） |
| **日期** | 2026-03-31（阅读日期） |
| **链接** | https://mp.weixin.qq.com/s/9qI83Ne-Ac_R9y-yJ6SVnQ |
| **类型** | 综述/观点文章 |

---

## 核心论点

1. **Harness Engineering 是 Prompt/Context Engineering 之后的第三范式**，关注如何构建模型周围的完整系统
2. **Agent = LLM + Harness**，当模型能力过线，决定上限的是 harness 质量
3. **Harness 即数据集**（Philipp Schmid 金句）——执行轨迹是新型竞争护城河
4. **训练即部署**：模型和 harness 从设计时就是一体的，Cursor/Windsurf 均已验证

---

## 关键引用

> "The Harness is the Dataset. Competitive advantage is now the trajectories your harness captures."
> —— Philipp Schmid, DeepMind Staff Engineer

> "Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions). If something goes sideways, STOP and re-plan immediately."
> —— Boris Cherny, Claude Code 负责人

> "We believe that the quality of the coding environments in RL tasks is the most important factor for downstream model performance."
> —— Windsurf 技术博客（SWE-1.5 训练）

> "Anytime you find an agent makes a mistake, you take the time to engineer a solution such that the agent never makes that mistake again."
> —— Mitchell Hashimoto

---

## 数据点

- Boris Cherny：给 Claude 有效验证手段，产出质量提升 **2-3 倍**
- Context Window 利用率甜蜜区间：顶级工程师通常控制在 **60% 以下**
- Needle-in-haystack 测试：Opus 4.6 系列长上下文命中率约 **70%**，GPT-5.4/Gemini 3.1 Pro 掉至 **30%**
- Claude Code 工具数量：约 **20 个**，团队仍在审视是否需要全部保留
- Claude Code harness 代码保质期：约 **2 个月**

---

## Harness 6 个组件（速记）

| 层 | 组件 | 一句话 |
|---|------|--------|
| 信息层 | Memory & Context | 控制 Agent 当前看到什么 |
| 信息层 | Tools & Skills | 扩展行动能力 |
| 执行层 | Orchestration | 编排任务流程和分工 |
| 执行层 | Infra & Guardrails | 沙箱、权限、安全护栏 |
| 反馈层 | Evaluation & Verification | 自动验证+闭环修正 |
| 反馈层 | Tracing & Observability | 让黑箱变透明 |

---

## 与现有知识库的关系

- 深化了 `core/tool`：工具少而精，过多导致决策瘫痪
- 深化了 `core/memory`：context decay，60% 利用率甜蜜区间
- 深化了 `core/sandbox`：Daytona 的 stateful sandbox 概念
- 补充了 `frameworks/`：harness 是比框架更上层的架构范式
- 新增了评估/观测维度：Braintrust 等 evaluation 创业方向

---

## 创业机会扫描（文中提到）

| 层 | 公司 | 定位 | 融资 |
|---|------|------|------|
| 信息层 | Edra | 企业知识→Agent 上下文 | $30M A 轮，Sequoia 领投 |
| 执行层 | Temporal | Durable Execution 基础设施 | $300M D 轮，a16z，估值 $5B |
| 执行层 | Oasis Security | Agent 权限管理 | $120M B 轮，估值 $700M |
| 执行层 | Daytona | Stateful Agent 沙箱 | $24M A 轮 |
| 反馈层 | Braintrust | AI Observability/Evaluation | $80M B 轮，ICONIQ，估值 $800M |

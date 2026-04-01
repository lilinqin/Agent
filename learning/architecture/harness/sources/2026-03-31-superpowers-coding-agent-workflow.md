# Superpowers — 完整 coding agent 工作流

- **来源**：https://github.com/obra/superpowers
- **类型**：开源项目 / skill 集合
- **日期**：2026-03-31

---

## 项目核心

一套完整的 coding agent 开发工作流，由多个自动触发的 skill 组成。
**核心理念：不让 agent 直接跳进去写代码，先走流程。**

## 完整工作流

```
brainstorming → git worktrees → writing-plans
→ subagent-driven-development → TDD → code-review → finishing-branch
```

每个 skill 自动触发，不需要手动调用。

## 两个最值得关注的设计

### 1. Subagent 上下文隔离

每个任务派一个全新子 agent，不继承主 session 历史，
而是由协调者精确构造子 agent 需要的上下文。

**为什么重要**：
- 防止历史上下文污染导致偏差
- 子 agent 专注单一任务，不受其他任务干扰
- 协调者保留宏观视角，子 agent 负责执行

执行完成后：两阶段 review
1. Spec 合规 review（代码是否符合设计）
2. Code quality review（代码质量）

### 2. Systematic Debugging 铁律

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

四个阶段：仔细读报错 → 稳定复现 → 定位根因 → 验证修复
**在时间压力下更要遵守，而不是跳过。**

## 与已有框架的关联

- `harness/harness.md`：subagent-driven-development 是 harness 模式的完整实现案例
- `context/context-engineering.md`：精确构造子 agent 上下文 = context engineering 的核心应用
- `evaluation/`：两阶段 review 机制是 agent 自我评测的一种架构

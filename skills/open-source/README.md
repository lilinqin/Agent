# Open Source Skills

本目录收录常用的开源 Agent Skill，可通过 Claude Code 一键安装使用。

---

## Skill 列表

### 1. planning-with-files

**作用**

实现 Manus 风格的文件化规划系统，将任务计划、研究发现、执行进度持久化到本地 Markdown 文件，作为 Agent 的"磁盘工作记忆"。适合多步骤任务、研究任务、跨多次工具调用的复杂工作，防止上下文丢失。

核心文件：
- `task_plan.md` — 阶段划分与进度追踪
- `findings.md` — 调研发现与关键信息
- `progress.md` — 执行日志与错误记录

**安装方式（Claude Code）**

```bash
claude mcp add skill -- npx -y @agentskills/installer planning-with-files
```

---

### 2. test-driven-development

**作用**

在实现任何功能或修复 Bug 之前，强制先编写测试用例。遵循 TDD 流程：Red（写失败测试）→ Green（最小实现通过）→ Refactor（重构优化），提升代码质量和可维护性。

适用场景：新功能开发、Bug 修复、代码重构时的质量保障。

**安装方式（Claude Code）**

```bash
claude mcp add skill -- npx -y @agentskills/installer test-driven-development
```

---

### 3. brainstorming

**作用**

在进行任何创意工作（新功能、组件开发、行为修改）之前必须使用。通过渐进式对话帮助明确意图、厘清需求、探索设计方案，确保实现前达成共识，避免反复返工。

工作流：探索项目上下文 → 澄清问题 → 提出 2-3 个方案 → 呈现设计 → 获得确认 → 进入实现。

**安装方式（Claude Code）**

```bash
claude mcp add skill -- npx -y @agentskills/installer brainstorming
```

---

### 4. ui-ux-pro-max

**作用**

UI/UX 设计智能系统，内置 67 种 UI 风格、96 种配色方案、57 种字体搭配、25 种图表类型、13 种技术栈（含 React 等）。覆盖从设计研究到落地实现的完整流程，帮助构建美观、专业、有记忆点的界面。

适用场景：Web 应用界面设计、组件库建设、品牌视觉设计、前端实现。

**安装方式（Claude Code）**

```bash
claude mcp add skill -- npx -y @agentskills/installer ui-ux-pro-max
```

---

## 说明

- 以上 Skill 均基于 Claude Code 平台
- 安装后在对话中按各 Skill 的触发词即可激活

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

### 5. remotion

**作用**

用 React 代码程序化地制作视频。通过自然语言描述动画、转场、UI 效果等，Agent 自动生成 Remotion 代码，几分钟内产出完整视频，无需打开传统视频编辑软件（AE / Premiere / Final Cut Pro）。

技术栈：React + TypeScript + CSS，输出真实 MP4 文件。

适用场景：产品演示、功能发布宣传视频、程序化批量生成视频内容。

**官方文档**

https://www.remotion.dev/docs/videos/

**安装方式（Claude Code）**

```bash
claude mcp add skill -- npx -y @agentskills/installer remotion
```

---

### 6. skill-creator（create-skill）

**来源**：Anthropic 官方出品

**作用**

帮助你从零创建一个符合规范的 Agent Skill。内置完整的 Skill 结构指南和设计原则，引导你完成从理解需求、规划内容、初始化、编写到打包发布的全流程。

核心设计原则：
- **渐进式加载**：元数据（~100词）→ SKILL.md 主体（<5k词）→ 按需加载引用文件，节省上下文窗口
- **自由度匹配**：任务越脆弱，指令越具体；任务越灵活，指令越宽松
- **精简原则**：Skill 只包含 AI 干活所需的信息，不创建 README、更新日志等冗余文件

Skill 标准目录结构：
```
my-skill/
├── SKILL.md        # 核心文件：YAML 元数据 + Markdown 指令（必需）
├── scripts/        # 可执行脚本（可选）
├── references/     # 参考文档（可选）
└── assets/         # 模板、图片等资源（可选）
```

**来源地址**：https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md

**安装方式**

```bash
npx skills add anthropics/skills --skill skill-creator
```

---

### 7. find-skills（find-skill）

**来源**：Vercel 官方出品

**作用**

元 Skill——帮你在当前工作流中快速搜索并找到最匹配的 Skill，无需跳出到外部平台。支持指令搜索和自然语言两种方式，中文提问可同时检索中英文关键词。

常用命令：
```bash
npx skills find "关键词"           # 关键词搜索
npx skills find "react 性能优化"   # 自然语言搜索
npx skills check                   # 检查已安装 Skill 的更新
npx skills update                  # 一键更新所有已安装 Skill
```

也可以在 Claude Code 中直接用自然语言提问，如："帮我找个能处理视频生成的 Skill"。

**来源地址**：https://github.com/vercel-labs/skills/blob/main/skills/find-skills/SKILL.md

**安装方式**

```bash
npx skills add vercel-labs/skills --skill find-skills
```

---

- 以上 Skill 均基于 Claude Code 平台
- 安装后在对话中按各 Skill 的触发词即可激活

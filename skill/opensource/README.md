# Agent 技能

> 可复用的 Agent Skill 模块

---

## 常用 Skill

| Skill | 作用 | 安装命令 |
|-------|------|----------|
| **planning-with-files** | Manus 风格文件化规划，将任务计划持久化到 Markdown | `claude mcp add skill -- npx -y @agentskills/installer planning-with-files` |
| **test-driven-development** | TDD 流程：Red → Green → Refactor | `claude mcp add skill -- npx -y @agentskills/installer test-driven-development` |
| **brainstorming** | 创意工作前的需求澄清和方案探索 | `claude mcp add skill -- npx -y @agentskills/installer brainstorming` |
| **ui-ux-pro-max** | UI/UX 设计系统，内置多种风格和配色 | `claude mcp add skill -- npx -y @agentskills/installer ui-ux-pro-max` |
| **remotion** | 用 React 代码程序化制作视频 | `claude mcp add skill -- npx -y @agentskills/installer remotion` |
| **skill-creator** | Anthropic 官方，帮助创建符合规范的 Agent Skill | `npx skills add anthropics/skills --skill skill-creator` |
| **find-skills** | Vercel 官方，元 Skill，快速搜索匹配 Skill | `npx skills add vercel-labs/skills --skill find-skills` |
| **playground** | Anthropic 官方，构建交互式 HTML 工具，可视化配置后生成 prompt | `npx skills add anthropics/claude-plugins-official@playground -g -y` |
| **superpowers** | 完整 coding agent 工作流集合：brainstorm → plan → subagent 执行 → TDD → review → merge，所有 skills 自动触发，无需手动调用。核心设计：每个任务派独立子 agent（上下文隔离）+ 两阶段 review（spec 合规 → 代码质量）| `/plugin install superpowers@claude-plugins-official` |

> 以上 Skill 均基于 Claude Code 平台，安装后在对话中按各 Skill 的触发词即可激活

---

## 参考论文

| 论文 | 链接 |
|------|------|
| ReAct | https://arxiv.org/abs/2210.03629 |
| A Survey on LLM based Autonomous Agents | https://arxiv.org/abs/2308.11432 |
| Toolformer | https://arxiv.org/abs/2302.04761 |
| MemGPT | https://arxiv.org/abs/2310.08560 |

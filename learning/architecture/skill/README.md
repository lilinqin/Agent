# Agent 技能

> 可复用的 Agent Skill 模块

---

## 常用 Skill

| Skill | 作用 | 安装 |
|-------|------|------|
| planning-with-files | Manus 风格文件化规划 | `claude mcp add skill -- npx -y @agentskills/installer planning-with-files` |
| test-driven-development | TDD 流程：Red→Green→Refactor | `claude mcp add skill -- npx -y @agentskills/installer test-driven-development` |
| brainstorming | 创意工作前的需求澄清 | `claude mcp add skill -- npx -y @agentskills/installer brainstorming` |
| skill-creator | 创建符合规范的 Agent Skill | `npx skills add anthropics/skills --skill skill-creator` |
| find-skills | 搜索匹配 Skill | `npx skills add vercel-labs/skills --skill find-skills` |

---

## 参考论文

| 论文 | 链接 |
|------|------|
| ReAct | https://arxiv.org/abs/2210.03629 |
| A Survey on LLM based Autonomous Agents | https://arxiv.org/abs/2308.11432 |
| Toolformer | https://arxiv.org/abs/2302.04761 |
| MemGPT | https://arxiv.org/abs/2310.08560 |

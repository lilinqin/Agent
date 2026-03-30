# Agent 技能

> 可复用的 Agent Skill 模块

## 内容

- [链接收录](./links.md)
- 开源 Skill 收录

---

## 开源 Skill 列表

### 1. planning-with-files

实现 Manus 风格的文件化规划系统，将任务计划、研究发现、执行进度持久化到本地 Markdown 文件。

**安装**：
```bash
claude mcp add skill -- npx -y @agentskills/installer planning-with-files
```

---

### 2. test-driven-development

在实现任何功能或修复 Bug 之前，强制先编写测试用例。遵循 TDD 流程：Red → Green → Refactor。

**安装**：
```bash
claude mcp add skill -- npx -y @agentskills/installer test-driven-development
```

---

### 3. brainstorming

在进行任何创意工作之前使用，通过渐进式对话帮助明确意图、厘清需求、探索设计方案。

**安装**：
```bash
claude mcp add skill -- npx -y @agentskills/installer brainstorming
```

---

### 4. ui-ux-pro-max

UI/UX 设计智能系统，内置 67 种 UI 风格、96 种配色方案、57 种字体搭配。

**安装**：
```bash
claude mcp add skill -- npx -y @agentskills/installer ui-ux-pro-max
```

---

### 5. remotion

用 React 代码程序化地制作视频。通过自然语言描述动画、转场、UI 效果，自动生成 Remotion 代码。

**安装**：
```bash
claude mcp add skill -- npx -y @agentskills/installer remotion
```

---

### 6. skill-creator

Anthropic 官方出品。帮助你从零创建一个符合规范的 Agent Skill。

**安装**：
```bash
npx skills add anthropics/skills --skill skill-creator
```

---

### 7. find-skills

Vercel 官方出品。元 Skill——帮你在当前工作流中快速搜索并找到最匹配的 Skill。

**安装**：
```bash
npx skills add vercel-labs/skills --skill find-skills
```

---

> 以上 Skill 均基于 Claude Code 平台

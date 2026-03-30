# Skill 目录

> Agent Skill 的学习与收录，分为开源 Skill 整理和自建 Skill 两部分。

---

## 目录结构

```
skill/
├── README.md            # 本文件，目录总览
├── opensource/          # 开源 Skill 整理
│   └── README.md        # 常用开源 Skill 列表与安装命令
└── custom/              # 自建 Skill
    └── daily-life/      # 日常生活工作记录 Skill
        ├── SKILL.md     # 主文件（触发描述 + 工作流 + 质量标准）
        └── references/  # 引导文档
            ├── daily-guide.md   # 每日记录引导问题体系
            ├── review-guide.md  # 周/月回顾引导流程
            └── templates.md     # 默认模板兜底
```

---

## opensource/

收录经过筛选的开源 Skill，包含安装命令和用途说明。

→ 详见 [opensource/README.md](./opensource/README.md)

---

## custom/

自己设计和维护的 Skill，遵循 [skill-creator](https://skills.sh) 规范编写。

| Skill | 用途 | 状态 |
|-------|------|------|
| [daily-life](./custom/daily-life/SKILL.md) | 引导式记录每日工作与生活，支持周/月回顾 | ✅ 可用 |

---

## Skill 设计规范

自建 Skill 遵循以下原则（来自 skill-creator 方法论）：

- **YAML frontmatter**：`name` + `description` 必填，description 需包含触发时机，语气要有推力
- **Progressive Disclosure**：SKILL.md 控制在 500 行内，细节放 `references/`
- **解释 Why**：说明指令背后的原因，而非单纯罗列 MUST
- **通用性**：避免 hardcode 个人信息，路径用变量或配置说明
- **测试驱动**：重要 Skill 应编写测试用例验证效果


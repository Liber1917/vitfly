# AI-Git-Best-Practices

> AI 时代 Git 版本管理最佳实践 Skill。为 LLM Coding Agent 场景下的版本控制提供完整规范体系。

## 核心内容

| 模块 | 内容 |
|------|------|
| **Agent-Aware Commit** | Conventional Commits + Git Trailer 机制，让 Agent 决策可追溯 |
| **Atomic Commit** | 语义边界切分，一个 commit 做一件事，可独立回滚 |
| **Checkpoint Commit** | 长任务中途存档，防止中断丢失，最终通过 rebase 整理 |
| **Feature Branch** | 强制 PR + 人工审查，禁止 Agent 直接 push main |
| **Git Worktree 隔离** | 多 Agent 并行工作时的物理隔离方案 |
| **Stacked PR** | 将大任务拆解为可审查的层叠单元 |
| **Monorepo 工作流** | Nx/Turborepo 依赖图 + 按影响范围运行 CI |
| **Jujutsu (jj)** | 工作区即提交，永远不丢失工作，支持 `split/absorb` 整理历史 |
| **GitButler** | 虚拟分支，先做事再分类，hunk 粒度归类 |

## 三大核心原则

```
隔离（Isolate）  →  Branch protection + worktree，为每个 Agent 任务提供独立工作空间
透明（Transparent） →  Atomic commit + commit trailer + PR 模板，让 Agent 决策可见
自动化（Automate） →  CI guardrails + branch protection required checks
```

## 文件结构

```
├── SKILL.md                          # Skill 主定义（WorkBuddy 使用）
├── references/
│   ├── agent-md-template.md          # AGENT.md 团队规范模板
│   ├── commit-convention.md           # Commit message 规范参考
│   ├── pr-template-agent.md          # Agent 专用 PR 模板
│   ├── branch-protection-config.md   # 分支保护规则配置（GitHub/GitLab）
│   ├── jj-cheatsheet.md              # Jujutsu 命令速查表
│   ├── gitbutler-guide.md            # GitButler 虚拟分支工作流指南
│   └── monorepo-workflow.md          # Monorepo 下的 Agent Git 工作流
└── scripts/
    ├── setup-agent-git.sh            # 一键为项目初始化 Agent Git 规范
    └── analyze-commits.py            # 分析 commit 质量（检测巨型/碎片提交）
```

## 快速上手

### 1. 初始化项目规范

```bash
# 下载并运行初始化脚本
curl -fsSL https://raw.githubusercontent.com/Liber1917/skill-ai-git-best-practices/main/scripts/setup-agent-git.sh | bash
```

### 2. 分析现有 commit 历史

```bash
# 分析当前分支相对于 main 的 commit 质量
python3 scripts/analyze-commits.py --base origin/main --giant-threshold 500
```

### 3. 在 WorkBuddy 中使用

在 WorkBuddy 中触发本 skill，当遇到以下场景时会自动使用：

- 询问 AI Agent 如何正确使用 Git
- 整理 Agent 生成的混乱 commit 历史
- 在 monorepo 中管理多 Agent 并发任务
- 选型并迁移到 Jujutsu / GitButler
- 制定团队 AI 友好的版本控制规范

## 背景文章

本 skill 基于 [万字干货｜AI 时代的 Git 版本管理，你用对了吗？](https://mp.weixin.qq.com/s/70hz6sYNwxErRkP7dkY8-Q)（小夏，TRAE 技术专家，2026-04-28）整理。

## License

MIT

---
name: ai-git-best-practices
description: AI 时代 Git 版本管理最佳实践指南。当用户询问 AI Agent 如何正确使用 Git、Git 在 Agentic Coding 下的痛点与解决方案、atomic commit、checkpoint commit、commit trailer 规范、feature branch 策略、git worktree 隔离多 Agent、Stacked PR 实践、Jujutsu (jj) 或 GitButler 等新一代 VCS 工具、monorepo 下的 VCS 管理、PR 模板与 AGENT.md 规范、commit 历史整理（interactive rebase / squash）、或要求为团队制定 AI 友好的版本控制规范时触发。
triggering_keywords:
  - AI Agent Git
  - atomic commit
  - checkpoint commit
  - commit trailer
  - feature branch
  - git worktree
  - Stacked PR
  - Jujutsu
  - GitButler
  - AI coding 版本控制
  - monorepo Git
  - AGENT.md
  - interactive rebase
  - Git merge 语义
  - agent git workflow
---

# AI-Git-Best-Practices

AI 时代 Git 版本管理最佳实践。指导 WorkBuddy 在 Agentic Coding 场景下正确使用 Git，包含 commit 规范、分支策略、多 Agent 隔离、历史整理工具及新一代 VCS（jj/GitButler）操作指南。

## Overview

LLM Coding Agent 的引入打破了传统 Git 版本控制的基本假设：自主执行、并发协作、任务粒度不匹配、决策黑盒。传统以「开发者意图」为核心的 Git 工作流，需要升级为「Agent-Aware」的规范体系。

本 skill 提供从 commit 规范 → 分支隔离 → 历史整理 → 工具选型的完整实践指南，适用于：
- 为团队制定 AI 友好的版本控制规范（AGENT.md）
- 整理 Agent 生成的混乱 commit 历史
- 在 monorepo 中管理多 Agent 并发任务
- 选型并迁移到 Jujutsu / GitButler

## 核心痛点（前置认知）

在给出任何建议前，先理解 Agent 对 Git 的核心挑战：

| 痛点 | 说明 |
|------|------|
| **巨型单一 commit** | Agent 将整个任务压成一个 diff，code review 形同虚设 |
| **无意义碎片 commit** | 每步操作单独提交，历史变流水账（WIP、fix typo） |
| **意图不可追溯** | Git 只记录 diff，不记录「为什么这样做」 |
| **脏工作区** | Agent 覆盖未提交的 WIP、混入格式化噪声 |
| **merge 只做文本校验** | 语义被破坏但无冲突，两个 branch 各自通过测试 |
| **并发踩踏** | 多 Agent 在同一 working tree 中互相覆盖改动 |

## Agent-Aware Commit 规范

### Commit Message 格式

每个 commit 应能独立描述「做了什么、为什么、上下文」。推荐格式：

```
<type>(<scope>): <summary>

[可选正文]

Agent-Task: <任务ID或描述>
Agent-Model: <模型标识>
```

**示例：**
```
feat(auth): implement JWT refresh token rotation

添加 refresh token 轮换机制，旧 token 失效后自动颁发新 token。
解决 token 泄露后无法主动作废的问题。

Agent-Task: implement token refresh mechanism
Agent-Model: claude-sonnet-4
```

### Git Commit Trailer 机制

`Agent-Task:` 和 `Agent-Model:` 是 Git 内置的 **commit trailer** 机制（与 `Signed-off-by:` 同级），git 原生解析，无需额外工具。

```bash
# 查询所有 Agent 任务的提交
git log --grep="Agent-Task"
```

### Commit 类型前缀

| 前缀 | 含义 | AI 场景补充 |
|------|------|-------------|
| `feat` | 新功能 | `[AI]feat` 便于过滤 |
| `fix` | 修复 bug | `[AI]fix` |
| `refactor` | 重构 | - |
| `test` | 测试 | - |
| `docs` | 文档 | - |
| `chore` | 杂项 | 依赖更新、格式化 |

### Atomic Commit vs Checkpoint Commit

| 概念 | 关注点 | 适用场景 |
|------|--------|----------|
| **Atomic commit** | 语义边界（一件事） | 每个 commit 可独立理解、回滚、验证 |
| **Checkpoint commit** | 进度记录（长任务存档） | 耗时长的 Agent 任务中途存档，防止中断丢失 |

**两者互补关系：**
- Checkpoint commit 在任务进行中保存现场
- 最终通过 `git rebase -i` 整理为一组语义清晰的 atomic commit

```bash
# ✅ 好的切分示例
git commit -m "feat(auth): add refresh token model"
git commit -m "feat(auth): implement token rotation logic"
git commit -m "feat(auth): add rotation unit tests"
git commit -m "docs(auth): update auth documentation"

# ❌ 反例：所有改动压成一个 commit
git commit -m "feat(auth): implement refresh token feature with tests and docs"
```

## 分支策略与隔离

### Feature Branch（强制规则）

**任何 Agent 都不应有权限直接 push main/master。**

```bash
# 分支命名规范
agent/<task-id>-<brief-description>
# 示例：agent/123-refresh-token-auth
```

### Branch Protection Rules（GitHub 配置）

| 规则 | 设置 |
|------|------|
| Require pull request before merging | ✅ |
| Require approvals | ≥1（至少人工审查通过） |
| Dismiss stale approvals | ✅ |
| Require status checks to pass | ✅ |
| Restrict who can push | 仅 CI bot + 指定人员 |

### Git Worktree 隔离多 Agent 并发

多个 Agent 并行工作时，使用 `git worktree` 为每个任务创建隔离工作目录：

```bash
# 为每个 Agent 任务创建独立 worktree
git worktree add ../agent-task-123 feat/new-feature
git worktree add ../agent-task-456 fix/bug-report

# 查看所有 worktree
git worktree list

# 清理不再需要的 worktree
git worktree remove ../agent-task-123
```

**优势：**
- 每个 Agent 有独立工作目录，不互相干扰
- 共享同一个 `.git`，分支管理统一，无需多次 clone
- 与 CI/CD 结合时，每个 worktree 可独立运行测试

## 历史整理：Interactive Rebase

整理 Agent 生成的历史，将其变为可理解的线性历史：

```bash
# 查看最近10个提交
git rebase -i HEAD~10
```

**常用操作：**

| 命令 | 说明 |
|------|------|
| `pick` | 保留该提交 |
| `squash` | 与前一个提交合并（保留提交信息） |
| `fixup` | 与前一个提交合并（丢弃该提交信息） |
| `reword` | 修改提交信息 |
| `drop` | 删除该提交 |

**整理策略：**
- 将 `[WIP]` / `fix typo` 等无意义提交 squash 掉
- 最终每个 commit 都能独立理解、可回滚
- ⚠️ 不要对已推送到远程的分支做 force push

## PR 模板：Agent Context 补充

Agent 生成的 PR 是人机交接的关键界面。推荐使用专用模板 `.github/pull_request_template/agent.md`：

```markdown
## Task Description
<!-- 描述原始需求 -->

## Agent Context
<!-- 补充 reviewer 需要但 diff 中不可见的上下文：
     - 权衡了哪些方案
     - 有哪些已知限制
     - 关键推理过程摘要（高风险变更时） -->

## Changes Made
<!-- 列出本次修改的核心内容 -->

## Testing
<!-- 说明测试覆盖情况：跑了哪些测试、CI 状态 -->

## Related Issues
<!-- 关联的任务或 issue -->
```

**自动化校验：**
使用 GitHub Actions 校验 PR description 是否包含必要章节：

```yaml
# .github/workflows/pr-template-check.yml
name: PR Template Check
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check PR Description
        run: |
          if ! grep -q "## Task Description" "$GITHUB_EVENT_PATH"; then
            echo "PR must follow agent template"
            exit 1
          fi
```

## AGENT.md：团队规范入口

AGENT.md 是 Agent 的行为规范入口，Agent 每次任务开始时读取并遵循。

**推荐包含的 Git 相关内容：**

```markdown
## Git Workflow
- 永远从 main 切新分支：git checkout -b agent/<task-id>-<description>
- 禁止直接 push 到 main/master
- 合并前必须开 PR + 人工审查

## Commit Convention
- 使用 Conventional Commits 格式：type(scope): summary
- 每个 commit 末尾附加 Agent-Task: <任务描述>
- Atomic commit：一件事、一个 commit、可独立回滚
- 长任务使用 Checkpoint commit，最终通过 rebase 整理

## Branch Strategy
- 分支命名：agent/<task-id>-<brief-description>
- 单任务单分支，不在同分支执行多个无关任务

## PR Requirements
- 使用 .github/pull_request_template/agent.md 模板
- PR 中必须包含 Task Description、Agent Context、Testing 章节
- 高风险变更（核心逻辑/安全）需附推理过程摘要

## CI Commands for Agents
- 运行受影响测试：nx affected --target=test
- 运行全量测试：npm run test:all
- lint 检查：npm run lint
```

## 可追溯性链路

当问题出现时，需要能够追溯「是哪个任务、用什么 prompt、在什么时候」产生了这段代码。

**追溯链路设计：**

```
任务系统（Jira/Linear）
    ↓
Agent Task → Commit (with Agent-Task trailer)
    ↓
PR → Code Review → Merge
    ↓
代码行 ← GitBlame / git-ai
```

**实践建议：**

| 建议 | 说明 |
|------|------|
| 打标签 | 在任务管理系统中为 Agent 任务打 `ai-generated` 标签 |
| 保留推理过程 | 高风险变更（核心业务/安全）在 PR 中附上关键推理摘要 |
| 定期审计 | 定期审计 `git log --grep="^Agent-Task:"` 的产出，评估质量趋势 |

**现有追踪工具：**

| 工具 | 特点 |
|------|------|
| `git-ai` | 开源 Git 扩展（Rust），行级归因，支持编码 Agent 调用 hook 标记代码来源 |
| Entire | 前 GitHub CEO 创立，语义推理层，Shadow Branch 追踪完整决策过程 |

## Stacked PR：将大任务拆解为可审查的层叠单元

Agent 往往能在一次任务中完成大量工作，全部堆进同一个 PR 导致审查困难。

### Stacked PR 核心理念

每个 PR 针对前一个 PR 的分支而非 main，形成有序依赖链：

```
main
  └── feat/interface  (PR #1)
        └── feat/implementation  (PR #2)
              └── feat/tests  (PR #3)
```

### GitHub gh-stack（原生支持）

GitHub 正在以 `gh-stack` 将 Stacked PR 作为原生特性引入（private preview）：

| 功能 | 说明 |
|------|------|
| Stack Navigator | PR 页面直接看到整条依赖链并跳转 |
| 聚焦 diff | 每个 PR 只展示本层相对于下一层的变更 |
| 按层运行 CI | 每个 PR 的 CI 针对其实际目标分支运行 |
| 一键合并 | 从最底层按序合并，branch protection 均被独立校验 |

## Monorepo 下的 VCS 管理

### 为什么 Monorepo 更适合 Agent

| 优势 | 说明 |
|------|------|
| 完整跨服务上下文 | Agent 无需在多个仓库间跳转，可一次修改 API 定义和所有调用方 |
| 大规模重构可靠 | 修改共享 utility 函数签名时能同时更新所有调用方 |
| 依赖图可见性 | Nx/Turborepo 提供项目依赖图，Agent 可精确决定需要运行哪些测试 |

### Monorepo VCS 挑战与应对

| 挑战 | 应对策略 |
|------|----------|
| 并发冲突风险更高 | git worktree 或 GitButler 虚拟分支，为每个 Agent 任务隔离工作区 |
| PR diff 更容易变大 | Stacked PR，将「修改共享 package」和「更新各消费方」拆成独立 PR 层 |
| CI 范围界定 | 配合依赖图工具实现「只跑受影响 package 的测试」 |

**Atomic commit 在 monorepo 中的边界：**「一件事」需要更明确定义。推荐做法：**一个 commit 表达一个完整的语义变化**，即使涉及多个 package，只要这些修改在逻辑上不可分割（例如接口变更 + 调用方同步更新），可放在同一个 commit 中。

## 新一代 VCS 工具

### Jujutsu（jj）

**定位：** Google 工程师开发，已在 Google 内部大规模使用。以 Git 仓库为存储后端，完全兼容 Git。

**核心创新：工作区即提交（working copy as a commit）**

| 传统 Git | Jujutsu |
|----------|---------|
| 手动 add 再 commit，工作区是独立的「暂存缓冲区」 | 工作区本身始终是一个提交（标记为 `@`），任何文件改动实时反映到这个提交上 |
| 未提交的内容随时可能丢失 | **永远不会丢失未保存的工作** |

**Change ID vs Commit ID：**

| 类型 | 说明 |
|------|------|
| **Commit ID** | 内容哈希，内容有任何改动哈希就会变化 |
| **Change ID** | 稳定的字母标识符（如 `qpvuntsm`），无论修改多少次始终不变——相当于 GitHub PR 的编号 |

**常用命令：**

```bash
# 初始化（对已有 Git 仓库）
jj git init --colocate

# 查看提交历史（直观图）
jj log

# 将混杂的工作区拆分为独立提交
jj split
# 打开交互式 diff 编辑器，选择每个 hunk 归入哪个提交

# 将改动自动归并到最合适的历史提交
jj absorb

# 撤销任意操作
jj op log
jj op undo <operation-id>

# 新建一个 changelist（类似分支）
jj new
jj describe "feat: add new feature"
```

**解决 Git 局限：**

| Git 局限性 | jj 解决方案 |
|------------|-------------|
| 脏工作区 | 工作区始终是已提交状态，Agent 的探索过程被自动记录 |
| 巨型提交难以拆分 | `jj split` 和 `jj absorb` 让拆分变更极其低成本 |
| 历史改写连锁代价 | 自动 rebase 后代，修改任意历史提交不再需要手动维护提交链 |

### GitButler

**定位：** 构建在 Git 之上的版本控制客户端，提供虚拟分支（Virtual Branches），获 a16z 2200 万美元融资。

**核心创新：虚拟分支（先做事再分类）**

| 传统 Git | GitButler |
|----------|-----------|
| 先切分支再做事 | **先做事再分类**：直接修改文件，将每个 hunk 分配给对应虚拟分支 |
| 必须决定在哪个分支工作后 checkout | Agent 可以直接修改，多个 Agent 可同时向同一工作目录写入，GitButler 按 hunk 粒度归类 |

**常用命令：**

```bash
# 查看当前状态（JSON 输出，适合 Agent 消费）
but status --json

# 将特定文件/hunk 提交到指定分支
but commit --branch refresh-token service.ts

# 自动归并到最合适的提交
but absorb

# Stacked Branches：按依赖关系堆叠 PR
but branch feat/implementation
but branch -a feat/tests
# 修改底层分支时，上层自动 rebase
```

**解决 Git 局限：**

| Git 局限性 | GitButler 解决方案 |
|------------|-------------------|
| 脏工作区难以管控 | 虚拟分支让不同关注点的变更在同一工作目录中保持分离 |
| 多 Agent 并发冲突 | 每个 Agent 会话绑定一个虚拟分支，互斥的 hunk 自动归类 |
| 大提交审查困难 | hunk 级别的分配机制天然产生小而聚焦的提交 |

### 工具选择建议

- **不互斥：** Jujutsu 和 GitButler 可以共存于同一团队
- **不取代 Git：** 两者都以 Git 仓库为后端，与 GitHub/GitLab 及现有 CI/CD 管道完全兼容
- **渐进迁移：** 团队中更熟悉的成员先行，其他成员继续使用 Git，不会产生协作障碍

## 三大核心原则

| 原则 | 具体措施 |
|------|----------|
| **隔离（Isolate）** | Branch protection + worktree，为每个 Agent 任务提供独立、受保护的工作空间 |
| **透明（Transparent）** | Atomic commit + commit trailer + PR 模板，让 Agent 的决策过程在版本历史中可见 |
| **自动化（Automate）** | CI guardrails + branch protection required checks，用工具而非人工来守住质量底线 |

## Resources

本 skill 包含以下可重用的资源：

### references/

- `commit-convention.md` — 完整的 commit message 模板与 trailer 规范示例
- `agent-md-template.md` — AGENT.md 模板，可直接复制到项目根目录使用
- `pr-template-agent.md` — Agent 专用 PR 模板
- `branch-protection-config.md` — GitHub/GitLab 分支保护规则配置示例
- `jj-cheatsheet.md` — Jujutsu 命令速查表
- `gitbutler-guide.md` — GitButler 虚拟分支工作流指南
- `monorepo-workflow.md` — Monorepo 下的 Agent Git 工作流详细说明

### scripts/

- `setup-agent-git.sh` — 一键为项目初始化 Agent Git 规范（创建 AGENT.md、PR 模板、目录结构）
- `analyze-commits.py` — 分析当前分支的 commit 质量，输出巨型提交/碎片提交报告

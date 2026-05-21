# GitButler 虚拟分支工作流指南

> GitButler 官网：https://gitbutler.com

## 核心概念

**虚拟分支（Virtual Branches）** 是 GitButler 的核心创新：

- 不替换 Git，底层仍是标准 Git 仓库
- 与 GitHub/GitLab 及 CI/CD 管道完全兼容
- 多个分支可以在同一个工作目录中同时存在

**心智模型对比：**

| 传统 Git | GitButler |
|----------|-----------|
| 先切分支再做事 | **先做事再分类** |
| 必须决定在哪个分支上工作 | 直接修改文件，按 hunk 分配到虚拟分支 |
| 多分支需要多次 checkout | 同一工作目录中，所有虚拟分支同时可见 |

## 安装

```bash
# macOS
brew install gitbutler/tap/gitbutler

# 或下载 GUI 客户端
# https://gitbutler.com/download
```

## 核心命令

```bash
# 查看当前状态（JSON 输出，适合 Agent 消费）
but status
but status --json

# 将特定文件/hunk 提交到指定虚拟分支
but commit --branch refresh-token service.ts

# 将未归类的改动提交到当前分支
but commit -m "feat(auth): add refresh token"

# 查看所有虚拟分支
but branch list

# 创建新虚拟分支
but branch feat/new-feature

# 在已有分支上新建分支
but branch -a feat/tests

# 自动归并：将改动吸收到最合适的提交中
but absorb

# 将当前分支推送到 remote
but push
```

## 多 Agent 并发工作流

### 场景：两个 Agent 同时工作

```bash
# Agent A 在 virtual branch: agent/token-auth
# Agent B 在 virtual branch: agent/fix-ui-bug

# GitButler 自动识别：
# - 属于 agent/token-auth 的 hunk → agent/token-auth 分支
# - 属于 agent/fix-ui-bug 的 hunk → agent/fix-ui-bug 分支
# - 公共文件的冲突按 hunk 粒度分配

# 查看哪些分支有未提交的变更
but status

# 查看特定分支的变更
but diff --branch agent/token-auth
```

### 与 CI/CD 集成

```bash
# 将虚拟分支发布为真实 Git 分支供 CI 测试
but push --force-with-lease

# GitButler 会将虚拟分支展开为标准 Git refs
# CI 系统无需感知 GitButler 的存在
```

## Stacked Branches（层叠分支）

```bash
# 创建依赖链
but branch feat/implementation
but branch -a feat/tests

# 修改底层分支时，上层自动 rebase
# 无需手动维护级联关系
but diff --branch feat/implementation
# 修改完成后：
but commit --branch feat/implementation -m "implement core logic"
# feat/tests 自动 rebase 到新的 feat/implementation 之上
```

## Agent Hook 集成

GitButler 支持 hooks，可在 Agent 操作前后自动触发：

```bash
# .gitbutler/hooks/post-commit
#!/bin/bash
# Agent 每次 commit 后自动同步到 GitHub
but push 2>/dev/null || true
```

**通过 MCP server 调用：**

```bash
# 如果使用支持 MCP 的 Agent，可以：
# mcp__gitbutler__create_branch(name="agent/123-task", base="main")
# mcp__gitbutler__commit(branch="agent/123-task", message="...")
```

## 与 git worktree 的对比

| 维度 | git worktree | GitButler |
|------|--------------|-----------|
| 隔离方式 | 物理隔离（不同目录） | 逻辑隔离（同一目录） |
| 灵活性 | 低（需预先规划） | 高（随时分配 hunk） |
| 协作 | 需要协调 worktree 路径 | 自动按分支归类 |
| Agent 集成 | 需指定 worktree 路径 | 直接修改工作目录即可 |
| 学习成本 | 低（纯 Git） | 中（需理解虚拟分支） |

## 最佳实践

```bash
# 1. 为每个 Agent 任务创建独立虚拟分支
but branch agent/123-refresh-token

# 2. 按关注点分配 hunk，不要所有改动混在一起
but commit --branch agent/123-refresh-token auth/token.py
but commit --branch agent/123-refresh-token auth/tests.py
but commit --branch shared/refactor config.py

# 3. 定期运行 absorb 保持分支整洁
but absorb

# 4. 开 PR 前，将虚拟分支推送到 remote
but push --branch agent/123-refresh-token
```

## 已知限制

- 目前仍处于快速迭代期，部分功能稳定性待验证
- 企业内网 Git 服务器（GitLab Enterprise / Bitbucket）兼容性需确认
- 大量并发虚拟分支（>20）时，GUI 性能可能下降

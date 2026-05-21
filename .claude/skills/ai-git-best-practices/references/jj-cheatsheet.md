# Jujutsu (jj) 命令速查表

> Jujutsu 官网：https://github.com/jj-vcs/jj

## 初始化

```bash
# 初始化新仓库（colocate 模式：与现有 Git 仓库共存）
jj git init --colocate

# 克隆已有 Git 仓库
jj git clone https://github.com/user/repo
```

## 基本操作

```bash
# 查看工作区状态
jj status

# 查看提交历史（直观图）
jj log

# 查看详细 diff
jj diff

# 提交当前工作区变更（jj 中工作区本身就是一个提交）
jj describe "feat(auth): add refresh token"

# 新建一个 changelist（类似分支）
jj new
jj describe "feat(payment): integrate stripe"
```

## 变更管理

```bash
# 将工作区拆分为多个独立提交（最重要的功能！）
jj split
# 交互式 diff 编辑器，选择每个 hunk 归入哪个提交

# 将未归类的改动吸收到最合适的历史提交中
jj absorb

# 编辑某个提交的描述
jj describe -r @ "new description"

# 废弃某个提交（不删除，类似 revert）
jj abandon -r <revision>
```

## 查看与导航

```bash
# 完整提交图
jj log

# 只看当前分支
jj log -r @

# 查看具体某个提交的内容
jj show <revision>

# 查看工作区相对某提交的变更
jj diff -r main
```

## 恢复与撤销

```bash
# 查看操作历史
jj op log

# 撤销上一个操作（可多次撤销）
jj op undo

# 撤销指定操作
jj op undo <operation-id>

# 恢复到某个特定的提交状态（创建新提交）
jj checkout <revision>
```

## 分支管理

```bash
# 创建新分支
jj branch create feature-auth

# 查看所有分支
jj branch list

# 重命名分支
jj branch rename old-name new-name
```

## 与 Git 交互

```bash
# 将 jj 的变更推送到 Git remote
jj git push

# 从 Git remote 拉取
jj git fetch
jj git pull

# 导出为标准 Git 操作（如果需要）
jj git export
```

## Agent 场景最佳实践

```bash
# 1. 开始新任务：从 main 新建 changelist
jj new
jj describe "agent/<task-id>: <任务简述>"

# 2. 定期 checkpoint
jj describe "WIP: 实现核心逻辑"

# 3. 任务完成前，整理为原子提交
jj split
# 交互式选择每个 hunk 的归属

# 4. 最终推送
jj git push -r @
```

## jj 的心智模型速记

| 概念 | 说明 |
|------|------|
| `@` | 当前工作区（始终是一个有效的提交，不会丢失任何工作） |
| `<change-id>` | 稳定标识符（如 `qpvuntsm`），修改后不变 |
| `<commit-id>` | 内容哈希，内容变了就变 |
| `jj split` | 将一个提交拆成多个——比 git rebase -i 更直观 |
| `jj absorb` | 自动分析 hunk 的 blame 信息，归入最合适的祖先提交 |
| `jj op undo` | 撤销任何操作（即使已经 rebase、split）——最安全的回退 |

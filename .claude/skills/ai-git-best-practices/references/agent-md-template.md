# AGENT.md

> 本文件是团队 AI Coding Agent 的行为规范入口。Agent 每次任务开始时应读取此文件并遵循。

## Git Workflow

- **永远从最新 main 切新分支**：`git checkout -b agent/<task-id>-<description>`
- **禁止直接 push 到 main/master**——所有变更必须通过 PR + 人工审查
- **单任务单分支**：不在同分支执行多个无关 Agent 任务
- **合并后删除分支**：PR 合并后及时清理 feature 分支

## Commit Convention

- 使用 **Conventional Commits** 格式：`type(scope): summary`
- 每个 commit 末尾附加 `Agent-Task: <任务描述>` 和 `Agent-Model: <模型名>`
- **Atomic commit**：一件事、一个 commit、可独立回滚
- 长任务使用 **Checkpoint commit**，最终通过 `git rebase -i` 整理为语义清晰的 atomic commit

### Commit 类型

| 前缀 | 含义 | AI 场景补充 |
|------|------|-------------|
| `feat` | 新功能 | `feat[AI]` 便于过滤 |
| `fix` | 修复 bug | `fix[AI]` |
| `refactor` | 重构 | - |
| `test` | 测试 | - |
| `docs` | 文档 | - |
| `chore` | 杂项 | 依赖/格式化/CI |

## Branch Strategy

```
main          ← 保护分支，禁止直接 push
  └── agent/<task-id>-<description>  ← Agent 任务分支
```

### 分支命名规范

```bash
# 正确
agent/123-refresh-token-auth
agent/456-fix-pagination-bug
agent/789-add-dark-mode

# 错误
fix-bug
new-feature
test
agent-task
```

## PR Requirements

- 使用 `.github/pull_request_template/agent.md` 模板
- PR 中必须包含：**Task Description**、**Agent Context**、**Testing** 章节
- 高风险变更（核心业务逻辑/安全相关）需附上关键推理过程摘要
- Review 通过后由人工触发 merge，禁止 Agent 自动合并

## CI Commands for Agents

```bash
# 运行受影响测试（推荐，节省时间）
nx affected --target=test
# 或: pnpm --filter=... test

# 运行全量测试
npm run test:all

# lint 检查
npm run lint

# 类型检查
npm run type-check
```

## 多 Agent 并发规范

当多个 Agent 并行工作时，使用 **git worktree** 隔离：

```bash
# 为每个 Agent 任务创建独立 worktree
git worktree add ../agent-task-<task-id> agent/<task-id>-<description>

# 完成后清理
git worktree remove ../agent-task-<task-id>
```

## 敏感信息规范

- **禁止**将 API key、数据库连接串、密码、token 等敏感信息写入代码
- 如不慎写入，立即使用 `git filter-repo` 或 BFG Repo-Cleaner 清除历史
- 使用 `.env.example` 模板管理环境变量，不提交 `.env` 文件

## 审查清单（Agent 开 PR 前自检）

- [ ] 每个 commit 都是 atomic（单一语义，可独立回滚）
- [ ] Commit message 包含 `Agent-Task:` trailer
- [ ] PR 使用 agent.md 模板，填写了 Task Description / Agent Context / Testing
- [ ] 没有混入格式化噪声（lint 已跑过）
- [ ] 没有敏感信息泄露
- [ ] 所有 CI 测试通过

# Agent Git Commit 规范参考

## Commit Message 格式

```
<type>(<scope>): <summary>

[可选正文]

Agent-Task: <任务ID或描述>
Agent-Model: <模型标识>
Co-Authored-By: <额外作者>
```

## 类型前缀

| 前缀 | 含义 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 bug |
| `refactor` | 重构（不改变功能） |
| `test` | 测试相关 |
| `docs` | 文档更新 |
| `chore` | 杂项（依赖、格式化、CI） |
| `perf` | 性能优化 |
| `ci` | CI/CD 配置 |

## AI 场景示例

### 好示例

```
feat(auth): implement JWT refresh token rotation

- 添加 RefreshToken model
- 实现 token 轮换逻辑：旧 token 失效后颁发新 token
- 添加 TokenRotationService

解决 token 泄露后无法主动作废的安全风险。

Agent-Task: implement token refresh mechanism
Agent-Model: claude-sonnet-4
```

```
fix(api): correct pagination offset calculation

offset 参数从 0 开始时，第一页返回空结果。
修正为：offset = (page - 1) * page_size

Agent-Task: fix pagination empty first page bug
```

### 差示例（避免）

```
# ❌ 无类型
update auth module

# ❌ 无意义描述
fix stuff

# ❌ 巨型提交
feat: add entire auth system with tests and docs and migrations

# ❌ 缺 trailer
feat(auth): add login endpoint
（缺少 Agent-Task，无法追溯）
```

## Commit Trailer 查询命令

```bash
# 查询所有 Agent 任务的提交
git log --grep="Agent-Task"

# 查询特定 Agent 任务的提交
git log --grep="Agent-Task: implement token refresh"

# 格式化输出 trailer 信息
git log --format="%h %s%nAgent-Task: %b" | grep -A1 "Agent-Task"
```

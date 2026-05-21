# 分支保护规则配置参考

## GitHub Branch Protection Rules

### 基础配置（必需）

在仓库 Settings → Branches → Add rule 中设置：

```
Branch name pattern: main
```

| 规则 | 建议值 | 说明 |
|------|--------|------|
| Require pull request before merging | ✅ 启用 | 所有合并必须通过 PR |
| Require approvals | 1+ | 至少一人工审查 |
| Dismiss stale approvals | ✅ 启用 | PR 有新提交时重新要求审批 |
| Require status checks to pass | ✅ 启用 | CI 必须全部通过 |
| Require branches to be up to date before merging | ⚠️ 建议关闭 | 避免 CI 重复运行，降低合并延迟 |
| Do not allow bypassing the above settings | ✅ 启用 | 包括管理员也不得绕过 |

### Agent 专用增强规则

```yaml
# .github/branch-protection.yml（使用 Branch Protection Pro）
restrictions:
  # 限制谁可以推送（排除 AI bot 直接 push）
  required_reviewers:
    - team-lead
    - senior-engineer

  # 禁止 force push
  block_force_pushes: true

  # 禁止强制删除分支
  block_branch_deletion: true

  # 要求签名的 commit
  require_signed_commits: true
```

### 为 Agent 分支单独配置规则

```yaml
# .github/branch-protection-agent.yml
rules:
  - pattern: 'agent/**'
    required_status_checks:
      - ci/test
      - ci/lint
      - ci/type-check
    required_pull_request_reviews:
      required_approving_review_count: 1
    restrictions:
      # 只允许指定的 CI bot 创建 agent 分支
      teams:
        - ci-bots
    # agent 分支合并到 main 后自动删除
    delete_branch_after_merge: true
```

## GitLab Protected Branches

在仓库 Settings → Repository → Protected branches 中：

```
Protected branch: main
  Allowed to merge: Maintainers + Developers + CI_JOB_TOKEN
  Allowed to push: Nobody  ← 关键：禁止任何人直接 push
  Require status checks: ✅
```

```
Protected branch: agent/*
  Allowed to merge: Developers
  Allowed to push: Nobody
  Require status checks: ✅
```

## Bitbucket Branch Permissions

在仓库 Settings → Branch permissions 中添加：

```json
{
  "type": "STATEFUL",
  "kind": "require_pull_request",
  "pattern": "main",
  "require_approvals": 1,
  "reset_on_repush": true,
  "block_strategy": "require_approvals"
}
```

## 本地 Hook：防止 Agent 直接 Push

在 `.git/hooks/pre-push` 中添加：

```bash
#!/bin/bash
# .git/hooks/pre-push

PROTECTED_BRANCHES="^(main|master|develop)$"
CURRENT_BRANCH=$(git symbolic-ref --short HEAD)

if [[ "$CURRENT_BRANCH" =~ $PROTECTED_BRANCHES ]]; then
    echo "❌ 禁止直接 push 到保护分支 '$CURRENT_BRANCH'"
    echo "请创建新分支，通过 PR 合并"
    exit 1
fi

echo "✅ 分支 '$CURRENT_BRANCH' push 校验通过"
```

## GitHub Actions：自动锁定 Agent 直接 Push

```yaml
# .github/workflows/git-guardrails.yml
name: Git Guardrails

on:
  push:
    branches: [main, master]

jobs:
  block-push:
    runs-on: ubuntu-latest
    steps:
      - name: Block direct push to protected branches
        run: |
          echo "❌ 检测到直接 push 到保护分支"
          echo "所有变更必须通过 Pull Request"
          exit 1
```

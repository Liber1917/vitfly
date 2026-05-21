# Monorepo 下的 Agent Git 工作流

## 为什么 Agent 场景更适合 Monorepo

| 优势 | 说明 |
|------|------|
| **完整跨服务上下文** | Agent 无需在多个仓库间跳转，可一次修改 API 定义和对应的客户端调用 |
| **大规模重构可靠** | 修改共享 utility 函数签名时能同时更新所有调用方，不会遗漏 |
| **依赖图可见性** | Nx/Turborepo 提供结构化项目依赖图，Agent 可精确决定需要运行哪些测试 |

## 挑战与应对策略

### 挑战 1：并发冲突风险更高

多个 Agent 同时修改 monorepo 中的共享包（如 `packages/shared-utils`），冲突概率远高于 Polyrepo。

**应对：**

| 方案 | 适用场景 | 工具 |
|------|----------|------|
| git worktree 隔离 | 多 Agent 并行开发，每个 Agent 有独立工作目录 | git 内置 |
| GitButler 虚拟分支 | hunk 粒度分配，同目录多 Agent | GitButler |
| 分区责任 | 约定不同 Agent 负责不同 package，减少交集 | 团队约定 |

### 挑战 2：PR diff 过大

monorepo 中一个改动可能涉及多个 package，diff 体量是 Polyrepo 的数倍。

**应对：Stacked PR**

```
# Stack 设计
main
  └── feat/shared-utils-api-change    (PR #1: 仅改 shared-utils)
        └── feat/client-update        (PR #2: 更新所有消费方)
              └── feat/e2e-tests       (PR #3: 端到端测试)
```

每个 PR 的 diff 只展示本层的实际变更，reviewer 不会被无关改动淹没。

### 挑战 3：CI 范围界定

全量 CI 在 monorepo 中成本极高，但人工判断影响范围不现实。

**应对：按依赖图只跑受影响测试**

```bash
# Nx
nx affected --target=test --base=origin/main

# Turborepo
turbo run test --filter=...[origin/main]

# Lerna
lerna changed --include-dependents
```

## Monorepo 分支命名规范

```bash
# 包级别
agent/<package-name>/<task-id>-<description>
# 示例：agent/shared-utils/123-refactor-token-logic

# 功能级别
agent/feat/<feature-name>
# 示例：agent/feat/payment-gateway

# 修复级别
agent/fix/<bug-id>-<brief>
# 示例：agent/fix/456-pagination-offset
```

## Atomic Commit 在 Monorepo 中的边界

| 情况 | 是否应放在同一 Commit |
|------|---------------------|
| 修改 `shared-utils` + 同步更新 3 个消费方 | ✅ 可以，只要语义上是「接口变更的完整生效」 |
| 修改 `auth` 包 + 无关修改 `ui` 组件 | ❌ 分开，各自 atomic |
| 修改 `shared-utils` + `config.ts`（仅配置） | ⚠️ 视情况，如果配置是因应接口变更而改，可以放一起 |
| 添加新 feature 到多个包 | ✅ 可以在 `feat(<scope>): description` 中包含所有包内相关改动 |

## 多 Agent 协作场景

### 场景：两个 Agent 需要改同一个共享包

```
情况：Agent A 需要在 shared-utils 中新增接口
      Agent B 同时需要修改 shared-utils 的另一个函数
```

**推荐处理流程：**

1. **约定锁机制**：Agent 在开始任务前通过 issue 或 Slack 告知「我正在修改 shared-utils 的 auth 模块」
2. **使用 worktree/GitButler 隔离**：每个 Agent 在独立虚拟分支上工作
3. **合并顺序约定**：
   - 先合并 Agent B 的 PR
   - Agent A 在 rebase 后合并
4. **CI 保护**：shared-utils 包设置 branch protection + required status checks

### 场景：跨多个 Agent 的共享包升级

```
shared-utils 需要升级依赖（影响 12 个包）
```

**推荐做法：**

```
PR #1: deps(shared-utils): upgrade dependencies
  → 更新 shared-utils 的 package.json 和 node_modules
  → 不更新任何消费方

PR #2-N: 各个消费包分别 PR，更新对 shared-utils 的引用
  → agent/package-a/upgrade-shared-utils
  → agent/package-b/upgrade-shared-utils
  ...

最后：Stacked PR 按顺序合并
```

## CI 配置示例

```yaml
# .github/workflows/monorepo-ci.yml
name: Monorepo CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  # 1. 共享包变更检测
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      changed-packages: ${{ steps.detect.outputs.packages }}
    steps:
      - uses: actions/checkout@v3
      - name: Detect changed packages
        id: detect
        run: |
          PACKAGES=$(nx show projects --affected 2>/dev/null | jq -r '.[].name' || echo '[]')
          echo "packages=$PACKAGES" >> $GITHUB_OUTPUT

  # 2. 只跑受影响包的测试
  test-affected:
    needs: detect-changes
    runs-on: ubuntu-latest
    strategy:
      matrix:
        package: ${{ fromJson(needs.detect-changes.outputs.changed-packages) }}
    steps:
      - uses: actions/checkout@v3
      - name: Test ${{ matrix.package }}
        run: nx run ${{ matrix.package }}:test
```

## 工具链推荐

| 工具 | 用途 | 对 Agent 的价值 |
|------|------|----------------|
| **Nx** | Monorepo 构建系统 + 依赖图 | Agent 可精确查询影响范围 |
| **Turborepo** | 任务调度 + 远程缓存 | 加速 CI，提升 Agent 开发迭代效率 |
| **Lerna** | 包管理 + 版本控制 | 管理发布流程 |
| **pnpm workspaces** | 包管理 | 快速、节省空间 |
| **Changesets** | 多包版本管理 + CHANGELOG | 自动生成多包变更日志 |

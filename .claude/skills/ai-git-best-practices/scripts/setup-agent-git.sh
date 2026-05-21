#!/bin/bash
# setup-agent-git.sh
# 为项目一键初始化 AI Agent Git 规范
# 用法: bash <(curl -fsSL https://raw.githubusercontent.com/Liber1917/skill-ai-git-best-practices/main/scripts/setup-agent-git.sh)

set -e

REPO_ROOT=$(git rev-parse --show-topslash 2>/dev/null || pwd)

echo "🚀 开始初始化 Agent Git 规范..."
echo "📁 仓库根目录: $REPO_ROOT"
cd "$REPO_ROOT"

# 1. 创建 AGENT.md
echo "📝 创建 AGENT.md..."
cat > AGENT.md << 'AGENTEOF'
# AGENT.md

> 本文件是团队 AI Coding Agent 的行为规范入口。Agent 每次任务开始时应读取此文件并遵循。

## Git Workflow

- **永远从最新 main 切新分支**：`git checkout -b agent/<task-id>-<description>`
- **禁止直接 push 到 main/master**——所有变更必须通过 PR + 人工审查
- **单任务单分支**：不在同分支执行多个无关 Agent 任务

## Commit Convention

- 使用 **Conventional Commits** 格式：`type(scope): summary`
- 每个 commit 末尾附加 `Agent-Task: <任务描述>` 和 `Agent-Model: <模型名>`
- **Atomic commit**：一件事、一个 commit、可独立回滚
- 长任务使用 **Checkpoint commit**，最终通过 `git rebase -i` 整理

## Branch Strategy

```
main          ← 保护分支，禁止直接 push
  └── agent/<task-id>-<description>  ← Agent 任务分支
```

## PR Requirements

- 使用 `.github/pull_request_template/agent.md` 模板
- PR 中必须包含：**Task Description**、**Agent Context**、**Testing** 章节
- Review 通过后由人工触发 merge，禁止 Agent 自动合并

## 审查清单（Agent 开 PR 前自检）

- [ ] 每个 commit 都是 atomic（单一语义，可独立回滚）
- [ ] Commit message 包含 `Agent-Task:` trailer
- [ ] PR 使用 agent.md 模板，填写了 Task Description / Agent Context / Testing
- [ ] 没有混入格式化噪声（lint 已跑过）
- [ ] 没有敏感信息泄露
- [ ] 所有 CI 测试通过
AGENTEOF
echo "✅ AGENT.md 创建完成"

# 2. 创建 PR 模板
echo "📝 创建 PR 模板..."
mkdir -p .github/pull_request_template
cat > .github/pull_request_template/agent.md << 'PREOF'
## Task Description
<!-- 描述原始需求 -->

## Agent Context
<!-- 补充 Reviewer 需要但 diff 中不可见的上下文 -->

### 方案权衡
| 方案 | 优点 | 缺点 | 最终选择 |
|------|------|------|----------|
|      |      |      | ✅ |

### 已知限制

### 推理过程摘要（高风险/核心变更必填）

## Changes Made
- [ ] <!-- 变更点 1 -->
- [ ] <!-- 变更点 2 -->

## Testing
### 测试类型
- [ ] 单元测试
- [ ] 集成测试

### 测试结果
<!-- CI 状态 -->

## Related Issues
<!-- Closes #XXX -->
PREOF
echo "✅ PR 模板创建完成"

# 3. 创建 pre-push hook
echo "📝 创建 pre-push hook..."
mkdir -p .git/hooks
cat > .git/hooks/pre-push << 'HOOKEOF'
#!/bin/bash
PROTECTED_BRANCHES="^(main|master|develop)$"
CURRENT_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || git rev-parse --abbrev-ref HEAD 2>/dev/null)

if [[ "$CURRENT_BRANCH" =~ $PROTECTED_BRANCHES ]]; then
    echo "❌ 禁止直接 push 到保护分支 '$CURRENT_BRANCH'"
    echo "请创建新分支，通过 PR 合并"
    exit 1
fi
echo "✅ 分支 push 校验通过: $CURRENT_BRANCH"
HOOKEOF
chmod +x .git/hooks/pre-push
echo "✅ pre-push hook 创建完成"

# 4. 创建 .gitignore 扩展（防止敏感信息）
echo "📝 检查敏感信息防护..."
if ! grep -q "\.env$" .gitignore 2>/dev/null; then
    echo ".env" >> .gitignore
    echo "✅ 添加 .env 到 .gitignore"
else
    echo "✅ .env 已在 .gitignore 中"
fi

echo ""
echo "🎉 Agent Git 规范初始化完成！"
echo ""
echo "创建的文件："
echo "  - AGENT.md                    （Agent 行为规范）"
echo "  - .github/pull_request_template/agent.md  （PR 模板）"
echo "  - .git/hooks/pre-push        （本地分支保护 hook）"
echo ""
echo "下一步："
echo "  1. git add . && git commit -m 'feat: add agent git规范'"
echo "  2. 在 GitHub/GitLab 设置 Branch Protection Rules"
echo "  3. 将 AGENT.md 内容告知你的 Agent（system prompt 或 project instructions）"

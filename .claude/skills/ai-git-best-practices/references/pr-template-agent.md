# Agent 专用 PR 模板

> 路径：`.github/pull_request_template/agent.md`
> 使用方法：在仓库根目录创建 `.github/pull_request_template/` 目录，放入此文件

```markdown
## Task Description
<!-- 描述原始需求：这条 PR 解决什么问题 -->
<!-- 示例：实现 JWT refresh token 轮换机制，解决 token 泄露后无法主动作废的问题 -->


## Agent Context
<!-- 补充 Reviewer 需要但 diff 中不可见的上下文 -->
<!-- 必填项：权衡了哪些方案、最终选择了什么、为什么 -->

### 方案权衡
| 方案 | 优点 | 缺点 | 最终选择 |
|------|------|------|----------|
|      |      |      | ✅ |

### 已知限制
<!-- 有哪些未解决的技术债务或待办事项 -->

### 推理过程摘要（高风险/核心变更必填）
<!-- 关键决策的推理链条，例如：
  - 为什么这样设计接口
  - 为什么选择这个算法
  - 安全性如何保证 -->


## Changes Made
<!-- 列出本次修改的核心内容，简洁明了 -->

- [ ] <!-- 变更点 1 -->
- [ ] <!-- 变更点 2 -->


## Testing
<!-- 说明测试覆盖情况 -->

### 测试类型
- [ ] 单元测试：<!-- 覆盖了哪些场景 -->
- [ ] 集成测试：<!-- 覆盖了哪些场景 -->
- [ ] E2E 测试：<!-- 如有 -->

### 测试结果
<!-- CI 状态截图或输出 -->


## Related Issues
<!-- 关联的任务或 issue -->
<!-- 示例：Closes #123, Related to #456 -->


## Screenshots / Recordings（如有 UI 变更）
<!-- 截图或录屏 -->
```

## 自动化校验（可选）

在 `.github/workflows/` 下添加 `pr-template-check.yml`：

```yaml
name: PR Template Check
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - name: Check PR Description
        run: |
          DESCRIPTION="${{ github.event.pull_request.body }}"
          if ! echo "$DESCRIPTION" | grep -q "## Task Description"; then
            echo "❌ PR 必须包含 Task Description"
            exit 1
          fi
          if ! echo "$DESCRIPTION" | grep -q "## Agent Context"; then
            echo "❌ PR 必须包含 Agent Context"
            exit 1
          fi
          if ! echo "$DESCRIPTION" | grep -q "## Testing"; then
            echo "❌ PR 必须包含 Testing"
            exit 1
          fi
          echo "✅ PR 模板校验通过"
```

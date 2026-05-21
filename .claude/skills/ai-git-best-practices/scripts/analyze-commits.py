#!/usr/bin/env python3
"""
analyze-commits.py — 分析当前分支 commit 质量

检测问题：
1. 巨型单一 commit（diff 行数超过阈值）
2. 无意义碎片 commit（消息过短/含 WIP/fix typo 等）
3. 缺少 Agent-Task trailer
4. 非 atomic commit（多关注点混在一个 commit）
"""

import subprocess
import sys
import argparse
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class CommitInfo:
    sha: str
    message: str
    body: str
    files_changed: int
    insertions: int
    deletions: int
    date: str


def run_git(args: list[str]) -> str:
    result = subprocess.run(["git"] + args, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"⚠️  Git 命令失败: {' '.join(args)}", file=sys.stderr)
        print(f"   {result.stderr.strip()}", file=sys.stderr)
    return result.stdout


def get_commits(base: str = "origin/main", max_count: int = 50) -> list[CommitInfo]:
    """获取从 base 起的所有 commits"""
    fmt = "%H%n%s%n%b%n---COMMIT_END---"
    output = run_git([
        "log", f"{base}..HEAD", "--no-merges",
        f"--format={fmt}", f"-{max_count}"
    ])

    commits: list[CommitInfo] = []
    for block in output.split("---COMMIT_END---\n"):
        if not block.strip():
            continue
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        sha = lines[0]
        message = lines[1]

        # 分离 subject 和 body
        body_parts = lines[2:]
        body = "\n".join(body_parts) if len(body_parts) > 1 else ""

        # 获取 diff 统计
        stat_output = run_git(["diff", "--stat", f"{sha}^..{sha}"])
        files = insertions = deletions = 0
        for line in stat_output.strip().split("\n"):
            if "file changed" in line or "files changed" in line:
                parts = line.split(",")
                for p in parts:
                    p = p.strip()
                    if "file" in p:
                        files = int(p.split()[0])
                    elif "insertion" in p:
                        insertions = int(p.split()[0])
                    elif "deletion" in p:
                        deletions = int(p.split()[0])

        date = run_git(["log", "-1", "--format=%ci", sha]).strip()

        commits.append(CommitInfo(
            sha=sha[:8],
            message=message,
            body=body,
            files_changed=files,
            insertions=insertions,
            deletions=deletions,
            date=date[:10]
        ))

    return commits


def check_issues(commits: list[CommitInfo], args) -> dict:
    """分析所有 commits，检测问题"""
    issues = {
        "giant_commits": [],    # 巨型提交
        "fragmented_commits": [],  # 碎片提交
        "missing_trailer": [],  # 缺少 trailer
        "non_atomic": [],       # 非原子提交
    }

    for commit in commits:
        total_lines = commit.insertions + commit.deletions
        issues_found = []

        # 1. 巨型提交检测
        if total_lines > args.giant_threshold:
            issues_found.append(f"巨型提交：+{commit.insertions}/-{commit.deletions} 行 ({commit.files_changed} 个文件)")

        # 2. 碎片提交检测
        msg_lower = commit.message.lower()
        fragmented_keywords = ["wip", "fix typo", "update file", "try again", "oops", "misc"]
        if (len(commit.message) < 15 or
            any(k in msg_lower for k in fragmented_keywords) or
            commit.message.startswith("Merge")):
            issues_found.append("碎片提交：消息过于简短或含无意义关键词")

        # 3. 缺少 Agent-Task trailer
        if "Agent-Task:" not in commit.body and "agent" in msg_lower:
            issues_found.append("缺少 Agent-Task trailer（检测到 agent 相关内容）")

        # 4. 非原子提交（通过启发式）
        # 如果一个 commit 的消息包含多个动词/noun phrase，可能是混合提交
        bad_prefixes = ["feat", "fix", "refactor", "test", "docs", "chore"]
        words = commit.message.lower().split()
        prefix_count = sum(1 for w in words if any(w.startswith(p) for p in bad_prefixes))
        if prefix_count > 1:
            issues_found.append("可能非原子提交：消息中包含多个类型的关键词")

        # 归类
        if "巨型提交" in str(issues_found):
            issues["giant_commits"].append((commit, issues_found))
        if "碎片提交" in str(issues_found):
            issues["fragmented_commits"].append((commit, issues_found))
        if "Agent-Task" in str(issues_found):
            issues["missing_trailer"].append((commit, issues_found))
        if "非原子" in str(issues_found):
            issues["non_atomic"].append((commit, issues_found))

    return issues


def print_report(issues: dict, commits: list[CommitInfo], args):
    total = len(commits)
    print(f"\n{'='*60}")
    print(f"  Agent Git Commit 质量分析报告")
    print(f"  分析范围: {total} commits")
    print(f"  巨型提交阈值: {args.giant_threshold} 行")
    print(f"{'='*60}\n")

    sections = [
        ("⚠️  巨型提交 (Giant Commits)", issues["giant_commits"]),
        ("⚠️  碎片提交 (Fragmented Commits)", issues["fragmented_commits"]),
        ("⚠️  缺少 Agent-Task Trailer", issues["missing_trailer"]),
        ("⚠️  可能非原子提交 (Non-Atomic)", issues["non_atomic"]),
    ]

    total_issues = 0
    for title, items in sections:
        if items:
            print(f"{title} — {len(items)} 个")
            print("-" * 50)
            for commit, reasons in items:
                print(f"  📌 {commit.sha} | {commit.date} | {commit.message[:50]}")
                for r in reasons:
                    print(f"     → {r}")
            print()

    for items in sections:
        total_issues += len(items[1])

    if total_issues == 0:
        print("✅ 没有发现明显的 commit 质量问题！")
    else:
        print(f"\n📊 总结: {total_issues}/{total} 个提交存在问题")
        print(f"   问题率: {total_issues/total*100:.1f}%")
        print("\n💡 建议: 使用 git rebase -i HEAD~{n} 整理历史")

    print(f"\n{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="分析 Agent Git commit 质量")
    parser.add_argument("--base", default="origin/main",
                        help="比较的基础分支 (default: origin/main)")
    parser.add_argument("-n", "--max", type=int, default=50,
                        help="最多分析的 commit 数 (default: 50)")
    parser.add_argument("--giant-threshold", type=int, default=500,
                        help="巨型提交的行数阈值 (default: 500)")
    args = parser.parse_args()

    print(f"🔍 正在分析从 {args.base} 起的 commits...")
    commits = get_commits(base=args.base, max_count=args.max)

    if not commits:
        print("❌ 没有找到 commits，请检查分支和 base 是否正确")
        sys.exit(1)

    issues = check_issues(commits, args)
    print_report(issues, commits, args)


if __name__ == "__main__":
    main()

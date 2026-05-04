# GitHub Branch Audit Report
**Date:** 2026-05-03  
**Repository:** vitfly (Liber1917/vitfly)  
**Current Active Branch:** mambatest  
**Auditor:** Kiro AI

---

## Summary

- **Total branches:** 6
- **Safe to delete:** 2
- **Keep:** 3
- **Review needed:** 1

---

## Branch Analysis

### Category A: Safe to Delete (2 branches)

#### 1. `fix/simulation-issues`
- **Last commit:** 2026-04-16 22:35:31 +0800
- **Commit message:** "fix: resolve simulation bugs across evaluation pipeline"
- **Status:** 1 commit ahead of main, 95 commits behind mambatest
- **Reason for deletion:** This was a temporary fix branch created on April 16. The simulation bug fixes were NOT directly merged into mambatest, but equivalent fixes were implemented independently in mambatest during the comprehensive testing phase (April 20-May 4). The mambatest branch has superseded this work with more comprehensive simulation testing and fixes.
- **Verification:** The commit `bb8716f` is not in mambatest history, but mambatest has its own simulation fixes merged from wsl2-support branch (commit `febb6ed`).

#### 2. `setup-evaluation-20260321`
- **Last commit:** 2026-04-19 17:16:23 +0800
- **Commit message:** "Merge pull request #2 from Liber1917/ecc-tools/vitfly-1776352249189"
- **Status:** 37 commits ahead of main, 58 commits behind mambatest
- **Reason for deletion:** This branch was created on March 21 for setting up the evaluation infrastructure and ECC tooling. All its commits (ECC bundle setup: `.claude/`, `.codex/`, `.agents/` files) have been fully merged into mambatest. The branch served its purpose and is now obsolete.
- **Verification:** Key commits (1f0dd20, 6d4c435, 2789d6c, 0fc89d4, 8265e40) are all present in mambatest history.

---

### Category B: Keep (3 branches)

#### 1. `main`
- **Last commit:** 2026-03-23 00:49:54 +0800
- **Status:** Production baseline
- **Reason:** Primary production branch - NEVER delete

#### 2. `mambatest`
- **Last commit:** 2026-05-04 10:28:51 +0800 (< 24 hours ago)
- **Status:** Current active development with 95 commits ahead of main
- **Reason:** Active development branch with all 6 Mamba branches (A, B, B+, C, D, E) tested and documented. Contains comprehensive simulation testing results, training infrastructure, and all recent work.

#### 3. `wsl2-support`
- **Last commit:** 2026-04-20 14:12:50 +0800
- **Status:** 2 commits ahead of main, 152 commits behind mambatest
- **Reason:** Contains WSL2-specific fixes that were merged into mambatest (commit febb6ed). While the work is merged, this branch should be kept as a reference for WSL2 environment setup and troubleshooting. It may be needed for future WSL2-related issues or for users setting up WSL2 environments.

---

### Category C: Review Needed (1 branch)

#### 1. `mambatest-distill`
- **Last commit:** 2026-05-03 23:32:51 +0800 (< 24 hours ago)
- **Status:** 0 commits ahead of mambatest, 7 commits behind mambatest
- **Reason for review:** This branch appears to be a recent fork from mambatest (created yesterday) for knowledge distillation experiments. It's 7 commits behind mambatest, meaning mambatest has moved forward with:
  - Branch E SSM recurrence fix
  - Fake SSM analysis expansion
  - Branch A retest with d_state=64
  - Literature support for data distribution bias
  - Expert data distribution bias analysis
  - Branch A full training completion
  - Distillation experiment protocol

**Differences from mambatest:**
- Removed: `experiments/distillation/PROTOCOL.md` (25 lines)
- Removed: `results/BRANCH_A_RETEST_REPORT.md` (179 lines)
- Modified: Branch A model and checkpoints (different weights)
- Modified: `results/EXPERIMENT_REPORT.md` (127 lines removed)
- Modified: `results/branch_A_full_summary.yaml`

**Recommendation:** Keep for now if distillation experiments are planned. If distillation work is abandoned or merged, delete after confirming with the team.

---

## Recommended Cleanup Script

```bash
#!/bin/bash
# Branch Cleanup Script for vitfly repository
# Generated: 2026-05-03

set -e

echo "=== GitHub Branch Cleanup for vitfly ==="
echo ""
echo "This script will delete the following branches:"
echo "  1. fix/simulation-issues (superseded by mambatest)"
echo "  2. setup-evaluation-20260321 (fully merged into mambatest)"
echo ""
echo "Branches that will be KEPT:"
echo "  - main (production)"
echo "  - mambatest (active development)"
echo "  - wsl2-support (reference for WSL2 setup)"
echo "  - mambatest-distill (under review - recent work)"
echo ""

read -p "Do you want to proceed with deletion? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted. No branches were deleted."
    exit 0
fi

echo ""
echo "Deleting branches..."

# Delete fix/simulation-issues
echo "Deleting fix/simulation-issues..."
git push origin --delete fix/simulation-issues
echo "✓ Deleted fix/simulation-issues"

# Delete setup-evaluation-20260321
echo "Deleting setup-evaluation-20260321..."
git push origin --delete setup-evaluation-20260321
echo "✓ Deleted setup-evaluation-20260321"

echo ""
echo "=== Cleanup Complete ==="
echo "Deleted: 2 branches"
echo "Remaining: 4 branches (main, mambatest, wsl2-support, mambatest-distill)"
echo ""
echo "To verify, run: git fetch --all --prune && git branch -r"
```

---

## Additional Notes

### Branch Protection Recommendations

Consider setting up branch protection rules on GitHub for:
- `main` - Require PR reviews, status checks
- `mambatest` - Require status checks (if CI/CD is configured)

### Future Cleanup Considerations

1. **mambatest-distill**: Review in 7 days (2026-05-10). If no active distillation work, consider merging or deleting.

2. **wsl2-support**: Can be deleted after 30 days if no WSL2-related issues arise and documentation is sufficient in mambatest.

3. **Merge mambatest to main**: Once the Mamba evaluation work is complete and validated, consider merging mambatest back to main to keep the production branch up to date.

### Documentation References

The following branches have associated documentation that should be preserved:
- `wsl2-support`: WSL2 setup guide in README.md (already merged to mambatest)
- `mambatest`: Comprehensive experiment reports, training results, and simulation testing documentation

---

## Verification Commands

Before deleting any branch, verify it's safe:

```bash
# Check if branch is fully merged into mambatest
git log origin/mambatest..origin/<branch> --oneline

# If output is empty or only contains commits you want to discard, it's safe to delete

# Check if branch is fully merged into main
git log origin/main..origin/<branch> --oneline

# View branch commit history
git log origin/<branch> --oneline -10

# Compare branch with mambatest
git diff origin/mambatest origin/<branch> --stat
```

---

**End of Report**

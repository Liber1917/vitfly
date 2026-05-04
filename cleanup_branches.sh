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

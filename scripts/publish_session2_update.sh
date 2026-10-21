#!/usr/bin/env bash
# Safely copy this verified project checkpoint into a NEW clone of the existing
# GitHub repository. Never force-push or overwrite another Git history.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE='https://github.com/harshvtomar/retail-demand-inventory-intelligence.git'
MODE="${1:---check}"
if [[ "$MODE" != '--check' && "$MODE" != '--publish' ]]; then
  printf 'Usage: bash scripts/publish_session2_update.sh [--check|--publish]\n' >&2
  exit 2
fi
for cmd in git rsync; do command -v "$cmd" >/dev/null || { echo "$cmd is required" >&2; exit 1; }; done
for path in src/session2.py src/advanced_sql.py scripts/reconcile_session2.py tests/test_session2.py docs/SESSION2_METHODS.md; do
  [[ -f "$ROOT/$path" ]] || { echo "Missing Session 2 file: $path" >&2; exit 1; }
done
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
GIT_TERMINAL_PROMPT=1 git clone --quiet "$REMOTE" "$TMP/repo"
# Copy this checkpoint only; never use --delete, so unrelated remote files survive.
rsync -a --exclude='.git/' --exclude='__pycache__/' --exclude='.pytest_cache/' \
  --exclude='.venv/' --exclude='data/raw/' --exclude='data/processed/' \
  --exclude='*.zip' --exclude='*.sqlite' --exclude='*.db' \
  "$ROOT/" "$TMP/repo/"
cd "$TMP/repo"
git add -A
while IFS= read -r -d '' path; do
  case "$path" in
    data/raw/*|data/processed/*|*.sqlite|*.db|*.zip|.env|.env.*|.kaggle/*|*kaggle.json|*__pycache__*|*.pyc)
      echo "Unsafe staged file: $path" >&2; exit 1;;
  esac
  if [[ -f "$path" ]] && [[ $(wc -c < "$path") -gt 10000000 ]]; then
    echo "Unexpectedly large staged file: $path" >&2; exit 1
  fi
done < <(git diff --cached --name-only -z)
printf '\nPrepared changes to existing repository:\n'
git diff --cached --stat
if git diff --cached --quiet; then echo 'No changes to publish.'; exit 0; fi
if [[ "$MODE" == '--check' ]]; then
  echo 'Preview only. Rerun with --publish to commit and push these changes.'
  exit 0
fi
if [[ -z "$(git config user.name || true)" || -z "$(git config user.email || true)" ]]; then
  echo 'Git user.name and user.email are required. Configure them in Git first.' >&2; exit 1
fi
git commit -m 'Add verified SupplyPulse Session 2 analytical features and SQL checks'
git push origin HEAD:main # no force; a concurrent remote update rejects this push
printf '\nPublished commit: '
git rev-parse HEAD
printf 'Verify live CI: https://github.com/harshvtomar/retail-demand-inventory-intelligence/actions\n'

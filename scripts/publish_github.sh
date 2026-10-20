#!/usr/bin/env bash
# Publish only the approved SupplyPulse project files to the specified repository.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
TARGET="https://github.com/harshvtomar/retail-demand-inventory-intelligence.git"

verify_files() {
  for required in README.md .gitignore .github/workflows/ci.yml requirements-ci.txt src/pipeline.py sql/exploratory_queries.sql tests/test_pipeline.py PROJECT_STATE.md; do
    if [[ ! -f "$required" ]]; then
      printf 'ERROR: missing required file: %s\n' "$required" >&2
      exit 1
    fi
  done
  printf 'Project files found. Original M5 CSVs, large SQLite DB and credentials must never be published.\n'
  # Check exact ignore rules without modifying this checkout. `git check-ignore`
  # is not reliable outside an initialized repository, so check a temp copy.
  local tmprepo path
  tmprepo=$(mktemp -d)
  trap 'rm -rf "$tmprepo"' RETURN
  cp .gitignore "$tmprepo/.gitignore"
  git -C "$tmprepo" init -q
  for path in data/raw/sales_train_validation.csv data/raw/calendar.csv data/raw/sell_prices.csv data/raw/source_manifest.json data/processed/m5.sqlite .env .kaggle/kaggle.json; do
    if ! git -C "$tmprepo" check-ignore -q "$path"; then
      printf 'ERROR: .gitignore does not exclude required private/generated path: %s\n' "$path" >&2
      exit 1
    fi
  done
  printf 'Verified critical .gitignore exclusions.\n'

}

verify_staged() {
  local bad=0
  while IFS= read -r -d '' path; do
    case "$path" in
      data/raw/*|data/processed/*|*.sqlite|*.zip|.env|.env.*|.kaggle/*|*kaggle.json|*__pycache__*|*.pyc)
        printf 'ERROR: private or generated file staged: %s\n' "$path" >&2
        bad=1;;
    esac
    if [[ -f "$path" ]]; then
      bytes=$(wc -c < "$path" | tr -d ' ')
      if (( bytes > 10000000 )); then
        printf 'ERROR: unexpectedly large staged file: %s (%s bytes)\n' "$path" "$bytes" >&2
        bad=1
      fi
    fi
  done < <(git diff --cached --name-only -z)
  if (( bad != 0 )); then
    printf 'Refusing to commit. Remove the unsafe staged file(s) before continuing.\n' >&2
    exit 1
  fi
}

case "${1:---check}" in
  --check)
    verify_files
    printf 'Preflight complete. No files have been pushed.\n'
    ;;
  --publish)
    verify_files
    if [[ ! -d .git ]]; then
      git init -b main
    fi
    branch=$(git symbolic-ref --quiet --short HEAD || true)
    if [[ "$branch" != 'main' ]]; then
      printf 'ERROR: expected branch main, found: %s. Stop rather than changing an existing branch.\n' "$branch" >&2
      exit 1
    fi
    if git remote get-url origin >/dev/null 2>&1; then
      remote=$(git remote get-url origin)
      if [[ "$remote" != "$TARGET" && "$remote" != 'git@github.com:harshvtomar/retail-demand-inventory-intelligence.git' ]]; then
        printf 'ERROR: origin points to a different repository: %s\n' "$remote" >&2
        exit 1
      fi
    else
      git remote add origin "$TARGET"
    fi
    git add -A
    verify_staged
    if ! git diff --cached --quiet; then
      git commit -m 'Build and verify SupplyPulse Session 1 analytics foundation'
    fi
    if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
      printf 'ERROR: no local commit to publish.\n' >&2
      exit 1
    fi
    printf '\nPublishing to %s\n' "$TARGET"
    git push -u origin main
    printf 'Published commit: '
    git rev-parse HEAD
    ;;
  *)
    printf 'Usage: bash scripts/publish_github.sh [--check|--publish]\n' >&2
    exit 2
    ;;
esac

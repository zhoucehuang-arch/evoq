#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 3 ]]; then
  echo "Usage: update-from-github.sh core|worker [remote] [branch]" >&2
  exit 1
fi

ROLE="$1"
REMOTE="${2:-origin}"
BRANCH="${3:-main}"

if [[ "${ROLE}" != "core" && "${ROLE}" != "worker" ]]; then
  echo "Role must be core or worker." >&2
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "git is required but was not found in PATH." >&2
  exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

cd "${ROOT_DIR}"

if [[ ! -d .git ]]; then
  echo "This directory is not a git repository: ${ROOT_DIR}" >&2
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Working tree is not clean. Commit or discard local changes before updating from GitHub." >&2
  exit 1
fi

chmod +x ops/bin/*.sh

echo "Fetching ${REMOTE}/${BRANCH}..."
git fetch --prune "${REMOTE}" "${BRANCH}"

echo "Fast-forwarding local checkout..."
git pull --ff-only "${REMOTE}" "${BRANCH}"

if [[ "${ROLE}" == "core" ]]; then
  echo "Restarting Core services..."
  ./ops/bin/core-up.sh
  ./ops/bin/core-smoke.sh
else
  echo "Restarting Worker services..."
  ./ops/bin/worker-up.sh
  ./ops/bin/worker-smoke.sh
fi

echo "Update completed for role=${ROLE}."

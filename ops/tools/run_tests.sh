#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
tmp_root="${repo_root}/.tmp/pytest"
mkdir -p "${tmp_root}"

export PYTHONPATH="ops/tools/pytest_sitecustomize:src"
export TMP="${tmp_root}"
export TEMP="${tmp_root}"

stamp="$(date +%Y%m%d%H%M%S)"
base_temp="${tmp_root}/pytest-${stamp}"

cd "${repo_root}"
if command -v uv >/dev/null 2>&1; then
  exec uv run --extra dev pytest "$@" --basetemp "${base_temp}" -p no:cacheprovider
fi

python_bin="${PYTHON:-}"
if [[ -z "${python_bin}" ]]; then
  if [[ -x "${repo_root}/.venv/bin/python" ]]; then
    python_bin="${repo_root}/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    python_bin="python3"
  else
    python_bin="python"
  fi
fi

exec "${python_bin}" -m pytest "$@" --basetemp "${base_temp}" -p no:cacheprovider

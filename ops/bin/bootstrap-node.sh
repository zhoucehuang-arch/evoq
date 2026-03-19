#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: bootstrap-node.sh core|worker [--overwrite]" >&2
  exit 1
fi

ROLE="$1"
OVERWRITE_FLAG="${2:-}"

if [[ "${ROLE}" != "core" && "${ROLE}" != "worker" ]]; then
  echo "Role must be core or worker." >&2
  exit 1
fi

if [[ -n "${OVERWRITE_FLAG}" && "${OVERWRITE_FLAG}" != "--overwrite" ]]; then
  echo "Only --overwrite is supported as the optional second argument." >&2
  exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
DEPLOY_CONFIG_SH="${ROOT_DIR}/ops/bin/deploy-config.sh"
HOST_PREFLIGHT_SH="${ROOT_DIR}/ops/bin/host-preflight.sh"

if [[ "${ROLE}" == "core" ]]; then
  ENV_FILE="${QE_CORE_ENV_FILE:-${ROOT_DIR}/ops/production/core/core.env}"
  NEXT_STEP="./ops/bin/core-up.sh"
else
  ENV_FILE="${QE_WORKER_ENV_FILE:-${ROOT_DIR}/ops/production/worker/worker.env}"
  NEXT_STEP="./ops/bin/worker-up.sh"
fi

echo "Running host prerequisite checks for role=${ROLE}..."
if [[ ! -f "${ENV_FILE}" || "${OVERWRITE_FLAG}" == "--overwrite" ]]; then
  QE_SKIP_ENV_PREFLIGHT=1 "${HOST_PREFLIGHT_SH}" "${ROLE}" "${ENV_FILE}"
else
  "${HOST_PREFLIGHT_SH}" "${ROLE}" "${ENV_FILE}"
fi

if [[ ! -f "${ENV_FILE}" || "${OVERWRITE_FLAG}" == "--overwrite" ]]; then
  echo "Bootstrapping env file at ${ENV_FILE}..."
  INIT_ARGS=("init" "${ROLE}")
  if [[ "${OVERWRITE_FLAG}" == "--overwrite" ]]; then
    INIT_ARGS+=("--overwrite")
  fi
  "${DEPLOY_CONFIG_SH}" "${INIT_ARGS[@]}"
else
  echo "Env file already exists: ${ENV_FILE}"
  echo "Skipping init. Pass --overwrite if you want to re-render it from the canonical template."
fi

echo "Running final env preflight..."
"${DEPLOY_CONFIG_SH}" preflight "${ROLE}" "${ENV_FILE}"

echo "Bootstrap completed for role=${ROLE}."
echo "Next step: ${NEXT_STEP}"

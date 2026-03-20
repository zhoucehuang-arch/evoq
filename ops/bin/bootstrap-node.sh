#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 3 ]]; then
  echo "Usage: bootstrap-node.sh core|worker [--single-vps] [--overwrite]" >&2
  exit 1
fi

ROLE="$1"
shift

SINGLE_VPS=false
OVERWRITE=false
for arg in "$@"; do
  case "${arg}" in
    --single-vps)
      SINGLE_VPS=true
      ;;
    --overwrite)
      OVERWRITE=true
      ;;
    *)
      echo "Unsupported argument: ${arg}" >&2
      echo "Usage: bootstrap-node.sh core|worker [--single-vps] [--overwrite]" >&2
      exit 1
      ;;
  esac
done

if [[ "${ROLE}" != "core" && "${ROLE}" != "worker" ]]; then
  echo "Role must be core or worker." >&2
  exit 1
fi

if [[ "${ROLE}" == "worker" && "${SINGLE_VPS}" == "true" ]]; then
  echo "Worker bootstrap is not used for the single-VPS profile. Bootstrap only the core role." >&2
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
if [[ ! -f "${ENV_FILE}" || "${OVERWRITE}" == "true" ]]; then
  QE_SKIP_ENV_PREFLIGHT=1 "${HOST_PREFLIGHT_SH}" "${ROLE}" "${ENV_FILE}"
else
  "${HOST_PREFLIGHT_SH}" "${ROLE}" "${ENV_FILE}"
fi

if [[ ! -f "${ENV_FILE}" || "${OVERWRITE}" == "true" ]]; then
  echo "Bootstrapping env file at ${ENV_FILE}..."
  INIT_ARGS=("init" "${ROLE}")
  if [[ "${OVERWRITE}" == "true" ]]; then
    INIT_ARGS+=("--overwrite")
  fi
  if [[ "${SINGLE_VPS}" == "true" ]]; then
    INIT_ARGS+=("--topology" "single_vps_compact")
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
if [[ "${SINGLE_VPS}" == "true" ]]; then
  echo "Single-VPS profile selected: the Core stack will also host the Codex worker runtime on this machine."
fi

#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: host-preflight.sh core|worker [env_file]" >&2
  exit 1
fi

ROLE="$1"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
DEPLOY_CONFIG_SH="${ROOT_DIR}/ops/bin/deploy-config.sh"

if [[ "${ROLE}" != "core" && "${ROLE}" != "worker" ]]; then
  echo "Role must be core or worker." >&2
  exit 1
fi

ENV_FILE="${2:-}"
if [[ -z "${ENV_FILE}" ]]; then
  if [[ "${ROLE}" == "core" ]]; then
    ENV_FILE="${ROOT_DIR}/ops/production/core/core.env"
  else
    ENV_FILE="${ROOT_DIR}/ops/production/worker/worker.env"
  fi
fi

require_cmd() {
  local name="$1"
  if ! command -v "${name}" >/dev/null 2>&1; then
    echo "Missing required host command: ${name}" >&2
    exit 1
  fi
}

warn_missing_cmd() {
  local name="$1"
  if ! command -v "${name}" >/dev/null 2>&1; then
    echo "Warning: optional host command not found: ${name}" >&2
  fi
}

require_cmd bash
require_cmd docker
require_cmd sed
require_cmd tar
require_cmd mktemp

if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
  echo "Missing required host command: python3 or python" >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose plugin is missing or not usable on this host." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon is not reachable for the current user." >&2
  exit 1
fi

warn_missing_cmd systemctl
warn_missing_cmd curl
warn_missing_cmd git

echo "Host prerequisites look present for role=${ROLE}."

if [[ "${QE_SKIP_ENV_PREFLIGHT:-0}" == "1" ]]; then
  echo "Skipping env preflight because QE_SKIP_ENV_PREFLIGHT=1."
elif [[ -f "${ENV_FILE}" ]]; then
  echo "Running env preflight for ${ENV_FILE}..."
  "${DEPLOY_CONFIG_SH}" preflight "${ROLE}" "${ENV_FILE}"
else
  echo "Env file not found yet: ${ENV_FILE}" >&2
  echo "Run ./ops/bin/deploy-config.sh init ${ROLE} first, then rerun host-preflight." >&2
fi

echo "Host preflight completed for role=${ROLE}."

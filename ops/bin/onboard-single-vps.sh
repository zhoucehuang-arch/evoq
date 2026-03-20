#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: onboard-single-vps.sh [--overwrite] [--no-prompt] [--no-start] [--skip-smoke] [--set KEY=VALUE ...]" >&2
}

OVERWRITE=false
NO_PROMPT=false
NO_START=false
SKIP_SMOKE=false
SET_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --overwrite)
      OVERWRITE=true
      shift
      ;;
    --no-prompt)
      NO_PROMPT=true
      shift
      ;;
    --no-start)
      NO_START=true
      shift
      ;;
    --skip-smoke)
      SKIP_SMOKE=true
      shift
      ;;
    --set)
      if [[ $# -lt 2 ]]; then
        usage
        exit 1
      fi
      SET_ARGS+=("--set" "$2")
      shift 2
      ;;
    *)
      echo "Unsupported argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
HOST_PREFLIGHT_SH="${ROOT_DIR}/ops/bin/host-preflight.sh"
DEPLOY_CONFIG_SH="${ROOT_DIR}/ops/bin/deploy-config.sh"
CORE_UP_SH="${ROOT_DIR}/ops/bin/core-up.sh"
CORE_SMOKE_SH="${ROOT_DIR}/ops/bin/core-smoke.sh"
ENV_FILE="${QE_CORE_ENV_FILE:-${ROOT_DIR}/ops/production/core/core.env}"

echo "Running host prerequisite checks for the single-VPS Core path..."
if [[ ! -f "${ENV_FILE}" || "${OVERWRITE}" == "true" ]]; then
  QE_SKIP_ENV_PREFLIGHT=1 "${HOST_PREFLIGHT_SH}" core "${ENV_FILE}"
else
  "${HOST_PREFLIGHT_SH}" core "${ENV_FILE}"
fi

ONBOARD_ARGS=("onboard-single-vps")
if [[ "${OVERWRITE}" == "true" ]]; then
  ONBOARD_ARGS+=("--overwrite")
fi
if [[ "${NO_PROMPT}" == "true" ]]; then
  ONBOARD_ARGS+=("--no-prompt")
fi
if [[ ${#SET_ARGS[@]} -gt 0 ]]; then
  ONBOARD_ARGS+=("${SET_ARGS[@]}")
fi

echo "Preparing the single-VPS deploy draft..."
"${DEPLOY_CONFIG_SH}" "${ONBOARD_ARGS[@]}"

if [[ "${NO_START}" == "true" ]]; then
  echo "Single-VPS draft prepared. Start later with ./ops/bin/core-up.sh and verify with ./ops/bin/core-smoke.sh."
  exit 0
fi

echo "Starting the single-VPS Core stack..."
"${CORE_UP_SH}"

if [[ "${SKIP_SMOKE}" == "true" ]]; then
  echo "Core stack started. Run ./ops/bin/core-smoke.sh before treating the node as deploy-ready."
  exit 0
fi

echo "Running smoke checks..."
"${CORE_SMOKE_SH}"

echo "Single-VPS onboarding completed. Dashboard, Discord, and the Codex runner are now expected to be reachable on this host."

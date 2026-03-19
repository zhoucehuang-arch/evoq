#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/ops/production/worker/docker-compose.worker.yml"
ENV_FILE="${QE_WORKER_ENV_FILE:-${ROOT_DIR}/ops/production/worker/worker.env}"
DEPLOY_CONFIG_SH="${ROOT_DIR}/ops/bin/deploy-config.sh"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing worker env file: ${ENV_FILE}" >&2
  echo "Copy ops/production/worker/worker.env.example to ops/production/worker/worker.env and fill it first." >&2
  exit 1
fi

cd "${ROOT_DIR}"

echo "Running worker env preflight..."
"${DEPLOY_CONFIG_SH}" preflight worker "${ENV_FILE}"

QE_WORKER_RUNTIME_ENV_FILE="${ENV_FILE}" docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d --build codex-fabric-runner

echo "Quant Evo worker stack is up."

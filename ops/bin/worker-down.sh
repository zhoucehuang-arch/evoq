#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/ops/production/worker/docker-compose.worker.yml"
ENV_FILE="${QE_WORKER_ENV_FILE:-${ROOT_DIR}/ops/production/worker/worker.env}"

QE_WORKER_RUNTIME_ENV_FILE="${ENV_FILE}" docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" down

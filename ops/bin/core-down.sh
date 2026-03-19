#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/ops/production/core/docker-compose.core.yml"
EDGE_COMPOSE_FILE="${ROOT_DIR}/ops/production/core/docker-compose.edge.yml"
ENV_FILE="${QE_CORE_ENV_FILE:-${ROOT_DIR}/ops/production/core/core.env}"

set -a
. "${ENV_FILE}"
set +a

COMPOSE_ARGS=(-f "${COMPOSE_FILE}")
if [[ -n "${QE_EDGE_PUBLIC_HOST:-}" ]]; then
  COMPOSE_ARGS+=(-f "${EDGE_COMPOSE_FILE}")
fi

QE_CORE_RUNTIME_ENV_FILE="${ENV_FILE}" docker compose "${COMPOSE_ARGS[@]}" --env-file "${ENV_FILE}" down

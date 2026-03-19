#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/ops/production/core/docker-compose.core.yml"
EDGE_COMPOSE_FILE="${ROOT_DIR}/ops/production/core/docker-compose.edge.yml"
ENV_FILE="${QE_CORE_ENV_FILE:-${ROOT_DIR}/ops/production/core/core.env}"
DEPLOY_CONFIG_SH="${ROOT_DIR}/ops/bin/deploy-config.sh"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing core env file: ${ENV_FILE}" >&2
  echo "Copy ops/production/core/core.env.example to ops/production/core/core.env and fill it first." >&2
  exit 1
fi

cd "${ROOT_DIR}"

echo "Running core env preflight..."
"${DEPLOY_CONFIG_SH}" preflight core "${ENV_FILE}"

set -a
. "${ENV_FILE}"
set +a

COMPOSE_ARGS=(-f "${COMPOSE_FILE}")
if [[ -n "${QE_EDGE_PUBLIC_HOST:-}" ]]; then
  COMPOSE_ARGS+=(-f "${EDGE_COMPOSE_FILE}")
fi

compose() {
  QE_CORE_RUNTIME_ENV_FILE="${ENV_FILE}" docker compose "${COMPOSE_ARGS[@]}" --env-file "${ENV_FILE}" "$@"
}

compose up -d --build postgres
compose exec -T postgres sh -lc '
  until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
    sleep 2
  done
'
compose run --rm --no-deps --build core-api alembic upgrade head
compose up -d --build core-api supervisor-runner discord-shell dashboard-web
if [[ -n "${QE_EDGE_PUBLIC_HOST:-}" ]]; then
  compose up -d dashboard-edge
fi
compose ps

echo "Quant Evo core stack is up, migrated, and ready for smoke checks."

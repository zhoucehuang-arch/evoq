#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: restore-postgres.sh <postgres_dump.sql> [runtime_backup.tgz]" >&2
  exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/ops/production/core/docker-compose.core.yml"
ENV_FILE="${QE_CORE_ENV_FILE:-${ROOT_DIR}/ops/production/core/core.env}"
DB_BACKUP="$1"
RUNTIME_BACKUP="${2:-}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing core env file: ${ENV_FILE}" >&2
  exit 1
fi
if [[ ! -f "${DB_BACKUP}" ]]; then
  echo "Missing database backup: ${DB_BACKUP}" >&2
  exit 1
fi

compose() {
  QE_CORE_RUNTIME_ENV_FILE="${ENV_FILE}" docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" "$@"
}

set -a
. "${ENV_FILE}"
set +a

compose up -d postgres
compose exec -T postgres sh -lc '
  until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
    sleep 2
  done
'
compose exec -T postgres psql -U "${QE_POSTGRES_USER}" -d "${QE_POSTGRES_DB}" -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;"
compose exec -T postgres psql -U "${QE_POSTGRES_USER}" -d "${QE_POSTGRES_DB}" < "${DB_BACKUP}"

if [[ -n "${RUNTIME_BACKUP}" ]]; then
  if [[ ! -f "${RUNTIME_BACKUP}" ]]; then
    echo "Missing runtime backup: ${RUNTIME_BACKUP}" >&2
    exit 1
  fi
  tar -xzf "${RUNTIME_BACKUP}" -C "${ROOT_DIR}"
fi

echo "Restore completed from ${DB_BACKUP}"

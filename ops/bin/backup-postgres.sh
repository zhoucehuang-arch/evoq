#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/ops/production/core/docker-compose.core.yml"
ENV_FILE="${QE_CORE_ENV_FILE:-${ROOT_DIR}/ops/production/core/core.env}"
BACKUP_DIR="${QE_BACKUP_DIR:-${ROOT_DIR}/.qe/backups}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing core env file: ${ENV_FILE}" >&2
  exit 1
fi

compose() {
  QE_CORE_RUNTIME_ENV_FILE="${ENV_FILE}" docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" "$@"
}

set -a
. "${ENV_FILE}"
set +a

mkdir -p "${BACKUP_DIR}"

compose up -d postgres
compose exec -T postgres sh -lc '
  until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
    sleep 2
  done
'

DB_BACKUP="${BACKUP_DIR}/postgres-${STAMP}.sql"
RUNTIME_BACKUP="${BACKUP_DIR}/runtime-${STAMP}.tgz"

compose exec -T postgres pg_dump -U "${QE_POSTGRES_USER}" "${QE_POSTGRES_DB}" > "${DB_BACKUP}"

STAGING_DIR="$(mktemp -d)"
trap 'rm -rf "${STAGING_DIR}"' EXIT
mkdir -p "${STAGING_DIR}/ops/production/core"
cp "${ENV_FILE}" "${STAGING_DIR}/ops/production/core/core.env"
if [[ -d "${ROOT_DIR}/.qe" ]]; then
  cp -R "${ROOT_DIR}/.qe" "${STAGING_DIR}/.qe"
fi
tar -czf "${RUNTIME_BACKUP}" -C "${STAGING_DIR}" .

echo "Created ${DB_BACKUP}"
echo "Created ${RUNTIME_BACKUP}"

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/ops/production/core/docker-compose.core.yml"
EDGE_COMPOSE_FILE="${ROOT_DIR}/ops/production/core/docker-compose.edge.yml"
ENV_FILE="${QE_CORE_ENV_FILE:-${ROOT_DIR}/ops/production/core/core.env}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing core env file: ${ENV_FILE}" >&2
  exit 1
fi

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

echo "== Core services =="
compose ps

echo "== Doctor =="
compose exec -T core-api python -m quant_evo_nextgen.runner.doctor --json

echo "== API health and doctor endpoints =="
compose exec -T core-api python -c "import json, os, urllib.request; headers = {}; token = os.environ.get('QE_DASHBOARD_API_TOKEN', '').strip(); health = json.load(urllib.request.urlopen('http://127.0.0.1:8000/healthz')); headers.update({'X-Quant-Evo-Dashboard-Token': token} if token else {}); request = urllib.request.Request('http://127.0.0.1:8000/api/v1/system/doctor', headers=headers); doctor = json.load(urllib.request.urlopen(request)); assert health.get('ok') is True, health; assert doctor.get('status') != 'fail', doctor; print(json.dumps({'healthz': health, 'doctor_status': doctor.get('status')}, ensure_ascii=False, indent=2))"

echo "== Dashboard reachability =="
compose exec -T core-api python -c "import base64, os, urllib.request; headers = {}; user = os.environ.get('QE_DASHBOARD_ACCESS_USERNAME', '').strip(); password = os.environ.get('QE_DASHBOARD_ACCESS_PASSWORD', '').strip(); token = base64.b64encode(f'{user}:{password}'.encode('utf-8')).decode('ascii') if user and password else ''; headers.update({'Authorization': f'Basic {token}'} if token else {}); request = urllib.request.Request('http://dashboard-web:3000', headers=headers); response = urllib.request.urlopen(request); print(f'dashboard status: {response.status}')"

if [[ -n "${QE_EDGE_PUBLIC_HOST:-}" ]]; then
  echo "== Edge proxy service =="
  compose ps dashboard-edge
fi

echo "Core smoke checks passed."

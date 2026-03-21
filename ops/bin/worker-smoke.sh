#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/ops/production/worker/docker-compose.worker.yml"
ENV_FILE="${QE_WORKER_ENV_FILE:-${ROOT_DIR}/ops/production/worker/worker.env}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing worker env file: ${ENV_FILE}" >&2
  exit 1
fi

compose() {
  QE_WORKER_RUNTIME_ENV_FILE="${ENV_FILE}" docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" "$@"
}

echo "== Worker services =="
compose ps

RUNNING_SERVICE="$(compose ps --status running --services | grep -x 'codex-fabric-runner' || true)"
if [[ "${RUNNING_SERVICE}" != "codex-fabric-runner" ]]; then
  echo "codex-fabric-runner is not in the running state." >&2
  exit 1
fi

echo "== Worker doctor =="
compose exec -T codex-fabric-runner python -m quant_evo_nextgen.runner.doctor --json

echo "== Codex CLI presence =="
compose exec -T codex-fabric-runner sh -lc 'command -v codex'

echo "== Worker runtime sanity =="
compose exec -T codex-fabric-runner python -c "import json; from quant_evo_nextgen.config import Settings; s = Settings(); assert s.node_role in {'worker', 'research'}; assert bool(s.openai_api_key); print(json.dumps({'node_role': s.node_role, 'codex_command': s.codex_command, 'relay_configured': bool(s.openai_base_url)}, ensure_ascii=False, indent=2))"

echo "Worker smoke checks passed."

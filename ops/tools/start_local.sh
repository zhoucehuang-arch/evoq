#!/usr/bin/env bash
set -euo pipefail

api_port="${API_PORT:-8000}"
dashboard_port="${DASHBOARD_PORT:-3000}"
dashboard_token="${QE_DASHBOARD_API_TOKEN:-local-dev-token}"
database_path="${QE_LOCAL_DATABASE_PATH:-.runtime/evoq-local.db}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --api-port)
      api_port="$2"
      shift 2
      ;;
    --dashboard-port)
      dashboard_port="$2"
      shift 2
      ;;
    --dashboard-token)
      dashboard_token="$2"
      shift 2
      ;;
    --database-path)
      database_path="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
runtime_dir="${repo_root}/.runtime"
log_dir="${runtime_dir}/logs"
mkdir -p "${log_dir}" "$(dirname "${repo_root}/${database_path}")"

port_open() {
  local port="$1"
  python3 - "$port" <<'PY'
import socket
import sys

port = int(sys.argv[1])
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.settimeout(0.2)
    raise SystemExit(0 if sock.connect_ex(("127.0.0.1", port)) == 0 else 1)
PY
}

backend_log="${log_dir}/local-backend.log"
dashboard_log="${log_dir}/local-dashboard.log"
pid_path="${runtime_dir}/local-pids.json"
backend_pid=""
dashboard_pid=""

db_full_path="${repo_root}/${database_path}"

backend_command=()
if command -v uv >/dev/null 2>&1; then
  backend_command=(uv run uvicorn quant_evo_nextgen.api.main:app --host 127.0.0.1 --port "${api_port}")
else
  python_bin="${PYTHON:-}"
  if [[ -z "${python_bin}" ]]; then
    if [[ -x "${repo_root}/.venv/bin/python" ]]; then
      python_bin="${repo_root}/.venv/bin/python"
    elif command -v python3 >/dev/null 2>&1; then
      python_bin="python3"
    else
      python_bin="python"
    fi
  fi
  backend_command=("${python_bin}" -m uvicorn quant_evo_nextgen.api.main:app --host 127.0.0.1 --port "${api_port}")
fi

if port_open "${api_port}"; then
  echo "API port ${api_port} is already in use. Reusing the existing process."
else
  backend_pid="$(
    cd "${repo_root}"
    export PYTHONPATH="src"
    export QE_REPO_ROOT="${repo_root}"
    export QE_POSTGRES_URL="sqlite+pysqlite:///${db_full_path}"
    export QE_DASHBOARD_API_TOKEN="${dashboard_token}"
    nohup "${backend_command[@]}" >"${backend_log}" 2>&1 &
    echo "$!"
  )"
fi

if port_open "${dashboard_port}"; then
  echo "Dashboard port ${dashboard_port} is already in use. Reusing the existing process."
else
  dashboard_pid="$(
    cd "${repo_root}/apps/dashboard-web"
    if [[ ! -d node_modules ]]; then
      npm ci
    fi
    export NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:${api_port}"
    export QE_DASHBOARD_API_TOKEN="${dashboard_token}"
    nohup npm run dev -- --hostname 127.0.0.1 --port "${dashboard_port}" >"${dashboard_log}" 2>&1 &
    echo "$!"
  )"
fi

printf '{"api_port":%s,"dashboard_port":%s,"dashboard_token":"%s","database":"%s","backend_pid":%s,"dashboard_pid":%s,"backend_log":"%s","dashboard_log":"%s","started_at":"%s"}\n' \
  "${api_port}" \
  "${dashboard_port}" \
  "${dashboard_token}" \
  "${db_full_path}" \
  "${backend_pid:-null}" \
  "${dashboard_pid:-null}" \
  "${backend_log}" \
  "${dashboard_log}" \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  >"${pid_path}"

echo "EvoQ local runtime is starting."
echo "Dashboard: http://127.0.0.1:${dashboard_port}"
echo "API health: http://127.0.0.1:${api_port}/healthz"
echo "Logs: ${log_dir}"
echo "Run smoke: ./ops/tools/smoke_local.sh"

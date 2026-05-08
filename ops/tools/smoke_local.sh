#!/usr/bin/env bash
set -euo pipefail

api_port="${API_PORT:-8000}"
dashboard_port="${DASHBOARD_PORT:-3000}"
dashboard_token="${QE_DASHBOARD_API_TOKEN:-local-dev-token}"

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
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

python3 - "${api_port}" "${dashboard_port}" "${dashboard_token}" <<'PY'
import json
import sys
import urllib.error
import urllib.request

api_port = int(sys.argv[1])
dashboard_port = int(sys.argv[2])
dashboard_token = sys.argv[3]
failures: list[str] = []


def fetch(name: str, url: str, *, expect_json: bool, headers: dict[str, str] | None = None) -> None:
    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read()
            if response.status != 200:
                failures.append(f"{name}: HTTP {response.status}")
                return
            if expect_json:
                json.loads(body.decode("utf-8"))
            elif len(body) < 1000:
                failures.append(f"{name}: response too small")
                return
            print(f"ok {name}")
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        failures.append(f"{name}: {exc}")


api_headers = {"X-Quant-Evo-Dashboard-Token": dashboard_token}
api_base = f"http://127.0.0.1:{api_port}"
dashboard_base = f"http://127.0.0.1:{dashboard_port}"

for name, path, headers in [
    ("healthz", "/healthz", None),
    ("doctor", "/api/v1/system/doctor", api_headers),
    ("strategy hypotheses", "/api/v1/strategy/hypotheses", api_headers),
    ("strategy backtests", "/api/v1/strategy/backtests", api_headers),
    ("market data providers", "/api/v1/market-data/providers", api_headers),
    ("market data factors", "/api/v1/market-data/factors", api_headers),
    ("live readiness report", "/api/v1/execution/live-readiness-report", api_headers),
    ("approvals", "/api/v1/approvals", api_headers),
]:
    fetch(name, api_base + path, expect_json=True, headers=headers)

for path in ["/", "/research", "/strategy", "/data", "/trading", "/learning", "/evolution", "/system", "/incidents"]:
    fetch(f"page {path}", dashboard_base + path, expect_json=False)

if failures:
    print("EvoQ local smoke failed:")
    for failure in failures:
        print(f"fail {failure}")
    raise SystemExit(1)

print("EvoQ local smoke passed.")
PY

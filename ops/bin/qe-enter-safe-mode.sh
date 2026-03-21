#!/usr/bin/env bash
set -euo pipefail

API_BASE="${1:-http://127.0.0.1:8000}"
ACTIVATED_BY="${2:-break-glass-operator}"
REASON="${3:-manual break-glass safe mode}"

post_override() {
  local scope="$1"
  curl --fail --silent -X POST "$API_BASE/api/v1/operator-overrides" \
    -H "Content-Type: application/json" \
    -d "{
      \"scope\": \"$scope\",
      \"action\": \"pause\",
      \"reason\": \"$REASON\",
      \"activated_by\": \"$ACTIVATED_BY\",
      \"created_by\": \"ops-break-glass\",
      \"origin_type\": \"runbook\",
      \"origin_id\": \"qe-enter-safe-mode.sh\"
    }" > /dev/null
}

post_override "trading"
post_override "evolution"
post_override "learning"

echo "Safe mode overrides created for trading, evolution, and learning."

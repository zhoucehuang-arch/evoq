#!/usr/bin/env bash
set -euo pipefail

# Safe config apply for OpenClaw instance config directories.
# - creates timestamped backups
# - validates JSON before restart
# - optional restart with automatic rollback on failure

CFG_DIR="${1:-}"
MODE="${2:-validate}"

if [[ -z "$CFG_DIR" ]]; then
  echo "Usage: $0 <config_dir> [validate|restart]"
  exit 1
fi

CFG_DIR="${CFG_DIR/#\~/$HOME}"
CFG_FILE="$CFG_DIR/openclaw.json"
APPROVALS_FILE="$CFG_DIR/exec-approvals.json"

if [[ ! -f "$CFG_FILE" ]]; then
  echo "FAIL: missing $CFG_FILE"
  exit 1
fi

TS="$(date -u +%Y%m%dT%H%M%SZ)"
BK_DIR="$CFG_DIR/backups/safe-apply-$TS"
mkdir -p "$BK_DIR"
cp "$CFG_FILE" "$BK_DIR/openclaw.json.bak"
if [[ -f "$APPROVALS_FILE" ]]; then
  cp "$APPROVALS_FILE" "$BK_DIR/exec-approvals.json.bak"
fi

python3 - <<PY
import json,sys
json.load(open('$CFG_FILE','r',encoding='utf-8'))
if __import__('os').path.exists('$APPROVALS_FILE'):
    json.load(open('$APPROVALS_FILE','r',encoding='utf-8'))
print('JSON_OK')
PY

if [[ "$MODE" == "validate" ]]; then
  echo "SAFE_VALIDATE_OK"
  echo "BACKUP_DIR=$BK_DIR"
  exit 0
fi

if [[ "$MODE" != "restart" ]]; then
  echo "FAIL: mode must be validate or restart"
  exit 1
fi

restart_failed=0
if ! OPENCLAW_CONFIG_DIR="$CFG_DIR" openclaw gateway restart >/tmp/openclaw-safe-apply-restart.log 2>&1; then
  restart_failed=1
fi

if [[ "$restart_failed" -eq 0 ]]; then
  if ! OPENCLAW_CONFIG_DIR="$CFG_DIR" openclaw gateway status >/tmp/openclaw-safe-apply-status.log 2>&1; then
    restart_failed=1
  fi
fi

if [[ "$restart_failed" -ne 0 ]]; then
  cp "$BK_DIR/openclaw.json.bak" "$CFG_FILE"
  if [[ -f "$BK_DIR/exec-approvals.json.bak" ]]; then
    cp "$BK_DIR/exec-approvals.json.bak" "$APPROVALS_FILE"
  fi
  OPENCLAW_CONFIG_DIR="$CFG_DIR" openclaw gateway restart >/tmp/openclaw-safe-apply-rollback.log 2>&1 || true
  echo "SAFE_APPLY_FAILED_ROLLED_BACK"
  echo "BACKUP_DIR=$BK_DIR"
  exit 1
fi

echo "SAFE_APPLY_OK"
echo "BACKUP_DIR=$BK_DIR"

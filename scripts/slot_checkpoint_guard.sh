#!/usr/bin/env bash
set -euo pipefail

ROOT="/root/.openclaw/workspace/quant-evo-do-test"
LOG="$ROOT/trading/logs/slot_guard_checkpoints.jsonl"
STATE="$ROOT/trading/logs/slot_guard_state.txt"
LOCK="$ROOT/trading/logs/slot_guard.lock"
HEARTBEAT_FILE="/root/.openclaw-explorer/agents/explorer/HEARTBEAT.md"
FANOUT_MATRIX="$ROOT/memory/runtime/fanout_ack_matrix_cycle_20260225_1940.json"
B_ALIGNMENT_ACK="$ROOT/memory/runtime/b_side_alignment_ack_latest.json"

mkdir -p "$ROOT/trading/logs"

exec 9>"$LOCK"
if ! flock -n 9; then
  exit 0
fi

TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
EPOCH_NOW="$(date -u +"%s")"
MINUTE_NOW="$(date -u +"%M")"
HOUR_NOW="$(date -u +"%H")"
SLOT_MINUTE="$((10#$MINUTE_NOW / 20 * 20))"
SLOT_LABEL="$(printf "%02d:%02d" "$HOUR_NOW" "$SLOT_MINUTE")"

HEARTBEAT_STATE="comments_only"
if grep -Eq "^[^#[:space:]]" "$HEARTBEAT_FILE"; then
  HEARTBEAT_STATE="active_tasks_present"
fi

A_CRON_STATE="active"
if ! crontab -l 2>/dev/null | grep -q "slot_checkpoint_guard.sh"; then
  A_CRON_STATE="missing"
fi

A_STALL_STATE="clear"
B_STALL_STATE="clear"
STALL_BLOCKERS="none"

append_blocker() {
  if [ "$STALL_BLOCKERS" = "none" ]; then
    STALL_BLOCKERS="$1"
  else
    STALL_BLOCKERS="$STALL_BLOCKERS,$1"
  fi
}

if [ "$A_CRON_STATE" = "missing" ]; then
  A_STALL_STATE="blocked"
  append_blocker "a_cron_missing"
fi

if [ -f "$FANOUT_MATRIX" ] && grep -q '"pushed"[[:space:]]*:[[:space:]]*false' "$FANOUT_MATRIX"; then
  if [ "$A_STALL_STATE" = "clear" ]; then
    A_STALL_STATE="degraded"
  fi
  append_blocker "cross_instance_push_incomplete"
fi

if [ ! -f "$B_ALIGNMENT_ACK" ]; then
  B_STALL_STATE="degraded"
  append_blocker "b_side_alignment_ack_missing"
fi

BLOCKER_PROBE_RESULT="critic_and_evolver_dependency_check"
RCA_FINDING="awaiting_cross_instance_push_proof"
FIX_EXECUTION="collect_ack_matrix_and_reprobe_at_next_slot"
CLOSURE_VERIFY="all_required_agents_pushed_true"
INCIDENT="none"
MISSED_SLOTS=0

if [ -f "$STATE" ]; then
  LAST_EPOCH="$(cat "$STATE" | tr -d '[:space:]')"
  if [[ "$LAST_EPOCH" =~ ^[0-9]+$ ]]; then
    DELTA_MIN="$(((EPOCH_NOW - LAST_EPOCH) / 60))"
    if [ "$DELTA_MIN" -gt 25 ]; then
      MISSED_SLOTS="$(((DELTA_MIN - 1) / 20))"
      INCIDENT="INCIDENT_MONITOR_GAP"
      A_STALL_STATE="blocked"
      append_blocker "slot_monitor_gap"
      BLOCKER_PROBE_RESULT="slot_gap_detected_delta_min_${DELTA_MIN}"
      RCA_FINDING="checkpoint_slot_missed_or_cron_jitter"
      FIX_EXECUTION="re-run_guard_and_keep_:00_:20_:40_cron_active"
      CLOSURE_VERIFY="two_consecutive_slots_without_gap"
    fi
  fi
fi

printf "%s" "$EPOCH_NOW" > "$STATE"

printf '{"ts":"%s","agent":"explorer","slot":"%s","minute":"%s","a_cron_state":"%s","A_STALL_STATE":"%s","B_STALL_STATE":"%s","stall_blockers":"%s","heartbeat_state":"%s","incident":"%s","missed_slots":%d,"BLOCKER_PROBE_RESULT":"%s","RCA_FINDING":"%s","FIX_EXECUTION":"%s","CLOSURE_VERIFY":"%s"}\n' \
  "$TS" "$SLOT_LABEL" "$MINUTE_NOW" "$A_CRON_STATE" "$A_STALL_STATE" "$B_STALL_STATE" "$STALL_BLOCKERS" "$HEARTBEAT_STATE" "$INCIDENT" "$MISSED_SLOTS" "$BLOCKER_PROBE_RESULT" "$RCA_FINDING" "$FIX_EXECUTION" "$CLOSURE_VERIFY" >> "$LOG"

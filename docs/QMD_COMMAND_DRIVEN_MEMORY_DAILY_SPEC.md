# QMD Command-Driven Memory Daily Spec

- scope: System A local canonical runbook for daily memory operations
- policy: qmd_structure_rollout_v2

## Daily Workflow

1. Update daily task artifact under `memory/daily/tasks/`.
2. Update daily note artifact under `memory/daily/notes/`.
3. Use qmd command layer for memory recall and search:
   - `qmd collection list`
   - `qmd search "<query>" -c quant-evo-memory`
   - `qmd get qmd://quant-evo-memory/<path>`
4. During heartbeat checks, verify concrete outputs and blockers.
5. If blocked/degraded, publish RCA tuple:
   - `blocker_type`
   - `root_cause`
   - `fix_owner`
   - `fix_eta_utc`
   - `verification_method`

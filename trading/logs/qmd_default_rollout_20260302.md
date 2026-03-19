# QMD_DEFAULT_ROLLOUT_V1 Evidence

- task_id: qmd_default_6agent_20260302
- role: explorer
- applied_at_utc: 2026-03-02T06:12:00Z

## Install Evidence
- bun_version: 1.3.10
- qmd_version: 1.0.7
- qmd_binary_path: /root/.bun/bin/qmd

## Config Baseline Applied
- memory.backend: qmd
- memory.qmd.includeDefaultMemory: true
- memory.qmd.sessions.enabled: true
- memory.qmd.update.interval: 5m

## Continuity Rule
- Research continuity requires running `memory_search` before synthesis and using retrieved snippets for context carry-over.

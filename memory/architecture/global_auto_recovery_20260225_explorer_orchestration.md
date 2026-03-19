# GLOBAL_REMEDIATION_EXECUTE_V1 - explorer_orchestration

- task_id: global_auto_recovery_20260225
- priority: P0
- scope: explorer_orchestration
- updated_at_utc: 2026-02-25T19:14:00Z

## Execution Status
- Explorer runtime remediation checklist is applied on this instance.
- Same remediation checklist requirement is fanned out by policy to the other A-side instances (critic/evolver) through bound channels.
- Compliance rule remains strict: no GitHub-based compliance conclusion is valid without per-agent commit+push evidence.

## Orchestration Constraints
- Direct cross-instance session control is currently blocked from this runtime (`pairing required` on session tooling).
- This instance can still publish mandate-conformant evidence and self push, and enforce invalid-compliance marking until peer push evidence arrives.

## Evidence Pointers
- Rule source: `config/instance-explorer/agents/explorer/AGENTS.md`
- Runtime cron enabled: `config/instance-explorer/openclaw.json`
- This orchestration record: `memory/architecture/global_auto_recovery_20260225_explorer_orchestration.md`

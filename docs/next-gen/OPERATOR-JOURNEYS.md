# Operator Journeys

This page describes the product from the operator's point of view.

It is intentionally practical: when something happens, what surface should the owner use first, what is the expected path, and when should SSH enter the picture.

## Journey 1. First Deploy To First Paper Session

Primary surfaces:

- GitHub
- SSH
- Discord
- Dashboard

Recommended path:

1. Publish or update the repository on GitHub.
2. Clone to Core and Worker under `/opt/quant-evo-nextgen`.
3. Run the host dependency and bootstrap scripts for each role.
4. Fill the role env files and keep the broker in `paper`.
5. Bring up both roles, pass smoke checks, and confirm dashboard plus Discord behavior.
6. Complete [FIRST-PAPER-RUN-CHECKLIST.md](FIRST-PAPER-RUN-CHECKLIST.md).

## Journey 2. Daily Owner Check

Primary surfaces:

- Discord first
- Dashboard second

Recommended path:

1. Ask Discord for the current system status.
2. Review pending approvals, open incidents, and any active overrides.
3. Open the dashboard and scan Overview, Trading, Evolution, and System.
4. If everything is calm, leave the system in its current governed posture.
5. If anything looks contradictory, pause the affected domain before investigating further.

## Journey 3. Pause Trading But Keep Learning

Primary surfaces:

- Discord
- Dashboard

Recommended path:

1. In Discord, request a governed pause for automated trading.
2. Confirm the pause appears in system state and that learning loops remain active.
3. Verify that no new trade intents are being promoted while research and synthesis continue.
4. Use the dashboard to confirm the pause is visible and explained.

## Journey 4. Review Or Roll Back Runtime Changes

Primary surfaces:

- Dashboard for review
- Discord for governed change requests

Recommended path:

1. Inspect runtime config, proposals, and recent revisions in the System view.
2. If a proposal is correct, approve it through the governed path.
3. If a recent revision caused trouble, request a rollback instead of editing files manually.
4. Use SSH only if the situation has become break-glass.

## Journey 5. Upgrade From GitHub

Primary surfaces:

- GitHub
- SSH
- Dashboard

Recommended path:

1. Push the reviewed change to GitHub.
2. On Core, run `./ops/bin/update-from-github.sh core`.
3. On Worker, run `./ops/bin/update-from-github.sh worker`.
4. Confirm the smoke checks pass again.
5. Re-open the dashboard and confirm freshness and system health.

## Journey 6. Incident Or Degraded State

Primary surfaces:

- Dashboard
- Discord
- SSH if needed

Recommended path:

1. Determine whether the problem is data freshness, provider connectivity, broker sync, or worker execution.
2. Pause the affected domain if the problem could affect trading safety.
3. Review the latest incident, workflow, and Codex run evidence.
4. If smoke checks fail or the runtime is inconsistent, move to the relevant runbook and use SSH.
5. Do not resume trading until the system is boring again.

## Fast Surface Guide

- Discord: control, pause, approve, ask, and review summaries
- Dashboard: observe state, compare domains, review evidence, and spot drift
- SSH: deploy, update, restore, rehearse, and repair

## Read Next

- [FIRST-PAPER-RUN-CHECKLIST.md](FIRST-PAPER-RUN-CHECKLIST.md)
- [OWNER-OPERATION-QUICKSTART.md](OWNER-OPERATION-QUICKSTART.md)
- [BREAK-GLASS-RUNBOOK.md](BREAK-GLASS-RUNBOOK.md)

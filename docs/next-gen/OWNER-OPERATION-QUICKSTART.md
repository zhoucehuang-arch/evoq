# Owner Operation Quickstart

This guide is for the person operating the system day to day.

## Main Surfaces

- Dashboard: primary control and review surface for health, data, research, strategy, trading, learning, evolution, system, and incidents
- Optional light gateway: alerts, quick approvals, pause/resume, and emergency actions only
- SSH: first deployment, upgrades, restores, and break-glass repair
- Owner CLI: bootstrap deploy drafts before the dashboard and light gateway are fully online

## First-Day Checklist

1. Open the dashboard and confirm it loads.
2. Run `./ops/bin/core-smoke.sh` on the Core VPS and confirm it reports no `fail`.
3. If you are on the two-VPS topology, run `./ops/bin/worker-smoke.sh` on the Worker VPS and confirm it reports no `fail`.
4. Verify the light gateway allowlist so only trusted owner accounts can approve, pause, resume, or trigger emergency actions.
5. Run `./ops/bin/system-doctor.sh` and confirm the acquisition stack explains whether Codex web search, SearXNG, RSSHub, and Playwright are configured, reachable, or degraded.
6. If a real broker is configured, wait for the first broker sync and confirm the trading view updates correctly.

## Owner CLI

Use these commands before the light gateway is fully configured, or when you want a guided VPS bootstrap flow:

```bash
./ops/bin/quickstart-single-vps.sh
./ops/bin/onboard-single-vps.sh --no-start
./ops/bin/system-doctor.sh
py -m quant_evo_nextgen.runner.deploy_config --repo-root . onboard-single-vps
py -m quant_evo_nextgen.runner.deploy_config --repo-root . status core
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core relay-base-url https://relay.example.com/v1
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core relay-key <secret>
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core market-mode us
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core market-mode cn
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core playwright-enabled true
```

## Daily Rhythm

1. Open the dashboard and scan Workbench, Data, Research, Strategy, Trading, Evolution, and System.
2. Review the top incidents, stale data warnings, pending approvals, and execution-readiness blockers.
3. Review any config proposals or runtime drift before changing policy.
4. Keep the system in `paper` mode until the first clean end-to-end activation is boring and repeatable.

## Good Light-Gateway Actions

Keep the gateway small and boring:

- acknowledge or reject pending approvals
- pause trading or auto-evolution during uncertainty
- resume only after the dashboard and doctor agree the runtime is healthy
- request a short status summary that links back to the dashboard
- trigger emergency safe mode when broker state, data freshness, or runtime health is uncertain

Use the Owner CLI for deployment-draft changes instead of copying secrets into chat:

```bash
py -m quant_evo_nextgen.runner.deploy_config --repo-root . status core
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core relay-base-url https://relay.example.com/v1
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core relay-key <secret>
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core market-mode us
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core searxng-base-url http://127.0.0.1:8080
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core rsshub-base-url http://127.0.0.1:1200
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core playwright-enabled true
```

## When To Intervene

Intervene manually if:

- `doctor` or `core-smoke.sh` returns `fail`
- the acquisition stack says a required endpoint is configured but probe-degraded
- broker sync or reconciliation turns red
- unexpected pause overrides appear
- the light gateway stops responding
- dashboard stops updating
- the runtime can no longer see `codex`

## Safe Operating Habits

- Keep the broker in `paper` mode until the first full deploy and smoke cycle are clean.
- Keep the light gateway owner allowlist narrow.
- Prefer governed config changes over manual env edits after the system is running.
- Prefer the dashboard or Owner CLI for deploy-draft updates; do not paste secrets into chat.
- Treat every live-promotion step as an explicit approval event.

## What Still Requires SSH

- first deployment
- GitHub-based upgrades
- backup and restore
- systemd setup
- break-glass repair

## Important Limits

- Deploy-draft changes made through the dashboard, light gateway, or Owner CLI still require a service restart before the runtime reads the new values.
- Playwright remains a governed fallback path, not the default research path.
- Truly unattended live operation still depends on clean smoke checks, broker sync, paper/live promotion discipline, and real production activation on the target VPS.

## Next Reading

- [FIRST-PAPER-RUN-CHECKLIST.md](FIRST-PAPER-RUN-CHECKLIST.md)
- [OPERATOR-JOURNEYS.md](OPERATOR-JOURNEYS.md)
- [FAQ.md](FAQ.md)
- [GITHUB-TO-VPS-DEPLOYMENT.md](GITHUB-TO-VPS-DEPLOYMENT.md)
- [VPS-DEPLOYMENT-RUNBOOK.md](VPS-DEPLOYMENT-RUNBOOK.md)

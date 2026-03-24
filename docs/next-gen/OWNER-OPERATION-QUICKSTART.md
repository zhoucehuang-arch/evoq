# Owner Operation Quickstart

This guide is for the person operating the system day to day.

## Main Surfaces

- Discord: control, approvals, deployment-draft updates, pauses, and governed config changes
- Dashboard: health, trading state, learning state, evolution state, and incident visibility
- SSH: first deployment, upgrades, restores, and break-glass repair
- Owner CLI: bootstrap deploy drafts before Discord is fully online

## First-Day Checklist

1. Open the dashboard and confirm it loads.
2. Run `./ops/bin/core-smoke.sh` on the Core VPS and confirm it reports no `fail`.
3. If you are on the two-VPS topology, run `./ops/bin/worker-smoke.sh` on the Worker VPS and confirm it reports no `fail`.
4. In Discord, verify that only the allowed owner accounts and channels can control the bot.
5. Run `./ops/bin/system-doctor.sh` and confirm the acquisition stack explains whether Codex web search, SearXNG, RSSHub, and Playwright are configured, reachable, or degraded.
6. If a real broker is configured, wait for the first broker sync and confirm the trading view updates correctly.

## Owner CLI

Use these commands before the Discord bot is fully configured, or when you want a guided VPS bootstrap flow:

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

1. Ask for status in Discord and review the top incidents or approvals.
2. Open the dashboard and scan Overview, Trading, Evolution, and System.
3. Review any config proposals or runtime drift before changing policy.
4. Keep the system in `paper` mode until the first clean end-to-end activation is boring and repeatable.

## Good Discord Prompts

- `status`
- `pending approvals`
- `show runtime config`
- `set heartbeat interval to 120 seconds`
- `disable research-intake loop`
- `rollback config rev-12345678`
- `pause auto-trading but keep learning running`
- `pause auto-evolution`
- `resume trading`
- `what has the system learned recently?`
- `why was this strategy not promoted to production?`
- `setup core deployment`
- `show core deployment status`
- `set core relay base url to https://relay.example.com/v1`
- `set core relay key to <secret>`
- `set core deployment topology to single_vps_compact`
- `set core market mode to us`
- `set core market mode to cn`
- `set core searxng base url to http://127.0.0.1:8080`
- `set core rsshub base url to http://127.0.0.1:1200`
- `set core playwright enabled to true`
- `set core playwright endpoint to ws://127.0.0.1:3001/browser`

## When To Intervene

Intervene manually if:

- `doctor` or `core-smoke.sh` returns `fail`
- the acquisition stack says a required endpoint is configured but probe-degraded
- broker sync or reconciliation turns red
- unexpected pause overrides appear
- Discord bot stops responding
- dashboard stops updating
- the runtime can no longer see `codex`

## Safe Operating Habits

- Keep the broker in `paper` mode until the first full deploy and smoke cycle are clean.
- Keep `QE_DISCORD_ALLOWED_USER_IDS` narrow.
- Prefer governed config changes over manual env edits after the system is running.
- Prefer Discord or the owner CLI deploy-draft updates over copying secrets into shell history repeatedly.
- Treat every live-promotion step as an explicit approval event.

## What Still Requires SSH

- first deployment
- GitHub-based upgrades
- backup and restore
- systemd setup
- break-glass repair

## Important Limits

- Deploy-draft changes made through Discord or the owner CLI still require a service restart before the runtime reads the new values.
- Playwright remains a governed fallback path, not the default research path.
- Truly unattended live operation still depends on clean smoke checks, broker sync, paper/live promotion discipline, and real production activation on the target VPS.

## Next Reading

- [FIRST-PAPER-RUN-CHECKLIST.md](FIRST-PAPER-RUN-CHECKLIST.md)
- [OPERATOR-JOURNEYS.md](OPERATOR-JOURNEYS.md)
- [FAQ.md](FAQ.md)
- [GITHUB-TO-VPS-DEPLOYMENT.md](GITHUB-TO-VPS-DEPLOYMENT.md)
- [VPS-DEPLOYMENT-RUNBOOK.md](VPS-DEPLOYMENT-RUNBOOK.md)

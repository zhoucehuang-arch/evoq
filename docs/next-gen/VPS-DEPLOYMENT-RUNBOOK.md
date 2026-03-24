# VPS Deployment Runbook

## 1. Purpose

This is the canonical production deploy path for the active next-generation runtime in `src/quant_evo_nextgen`.

If you are starting from a local folder and want to publish to GitHub first, then deploy to VPS by `git clone` / `git pull`, read [GITHUB-TO-VPS-DEPLOYMENT.md](GITHUB-TO-VPS-DEPLOYMENT.md) before using this runbook.

Recommended first deployment shape:

- `1 VPS` using the `single_vps_compact` profile
- bootstrap only the Core env
- let the Core stack also host `codex-fabric-runner`

Scale out later when needed:

- `VPS-A Core`
- `VPS-B Worker`

Repo path on both machines:

- `/opt/quant-evo-nextgen`

## 2. Assumptions

- Docker Engine and the Docker Compose plugin are installed on both VPS nodes.
- The repo is cloned on both nodes at `/opt/quant-evo-nextgen`.
- Core and Worker can reach each other over Tailscale or another private network path.
- Postgres is not exposed to the open internet.
- The owner will operate primarily from Discord and the dashboard.
- The relay/API key is OpenAI-compatible and works with Codex CLI.

If you are starting from a fresh Ubuntu or Debian VPS, you can install the host prerequisites first:

```bash
cd /opt/quant-evo-nextgen
sudo ./ops/bin/install-host-deps.sh
```

## 2.1 Simplest One-VPS Path

If you want the shortest deploy path first, use the single-VPS profile:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/quickstart-single-vps.sh
```

This keeps the authority model inside the Core runtime, but also starts the Codex worker runtime on the same host. It is the recommended first product path when you want one VPS only.

If you prefer to separate host preparation from app onboarding, you can also use:

```bash
cd /opt/quant-evo-nextgen
sudo ./ops/bin/install-host-deps.sh
./ops/bin/onboard-single-vps.sh
```

If you prefer to prepare the draft first and start the services later, you can also use:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/onboard-single-vps.sh --no-start
```

If you prefer the lower-level owner CLI instead of the shell wrapper, use:

```bash
cd /opt/quant-evo-nextgen
py -m quant_evo_nextgen.runner.deploy_config --repo-root . onboard-single-vps
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core relaybaseurl https://relay.example.com/v1
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core relaykey <secret>
```

## 3. Core VPS

### 3.1 Bootstrap the Core env file

```bash
cd /opt/quant-evo-nextgen
./ops/bin/bootstrap-node.sh core
```

This guided path runs host prerequisite checks, creates the canonical env file if it does not exist yet, and reruns env preflight before Docker bring-up.

If you want a friendlier owner-facing bootstrap path on the VPS, the same draft can be managed with:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/onboard-single-vps.sh --no-start
py -m quant_evo_nextgen.runner.deploy_config --repo-root . onboard-single-vps
py -m quant_evo_nextgen.runner.deploy_config --repo-root . status core
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core relaykey <secret>
```

If you want the explicit step-by-step path instead, use:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/host-preflight.sh core
./ops/bin/deploy-config.sh init core
./ops/bin/deploy-config.sh preflight core ops/production/core/core.env
```

The host preflight checks Docker, Compose, Python access, and core shell utilities before you start. The deploy-config wrapper runs directly from the repo and does not require a host-side `pip install`.
The init helper writes the canonical template, prompts for required values, and keeps Core on safe first-boot defaults unless you explicitly choose another broker mode.

### 3.2 Review `ops/production/core/core.env`

Must fill:

- `QE_POSTGRES_PASSWORD`
- `QE_DISCORD_TOKEN`
- `QE_DISCORD_GUILD_ID`
- `QE_DISCORD_CONTROL_CHANNEL_ID`
- `QE_DISCORD_APPROVALS_CHANNEL_ID`
- `QE_DISCORD_ALERTS_CHANNEL_ID`
- `QE_DISCORD_ALLOWED_USER_IDS`
- `QE_OPENAI_API_KEY`
- `QE_OPENAI_BASE_URL` if using a relay
- `QE_DASHBOARD_ACCESS_USERNAME`
- `QE_DASHBOARD_ACCESS_PASSWORD`
- `QE_DASHBOARD_API_TOKEN`

The guided bootstrap path now auto-generates `QE_DASHBOARD_ACCESS_PASSWORD` and `QE_DASHBOARD_API_TOKEN` if you leave them blank, while defaulting the dashboard username to `owner`.

Recommended defaults for the first VPS bring-up:

- `QE_DEFAULT_BROKER_ADAPTER=paper_sim`
- `QE_DEFAULT_BROKER_ENVIRONMENT=paper`
- `QE_DB_BOOTSTRAP_ON_START=false`
- `QE_CODEX_WORKSPACE_MODE=isolated_copy`
- `QE_POSTGRES_BIND_HOST=127.0.0.1`
- `QE_API_BIND_HOST=127.0.0.1`
- `QE_DASHBOARD_BIND_HOST=127.0.0.1`
- `QE_SEARXNG_BASE_URL=` if you do not have a local metasearch node yet
- `QE_RSSHUB_BASE_URL=` if you do not have a local feed router yet
- `QE_PLAYWRIGHT_BROWSER_ENABLED=false` unless you have a Playwright endpoint ready

Optional public dashboard edge:

- `QE_EDGE_PUBLIC_HOST=dashboard.example.com`
- `QE_EDGE_ACME_EMAIL=you@example.com`

Only switch the default broker to Alpaca after the first clean paper-mode deploy and the first successful broker sync.
Only switch `QE_POSTGRES_BIND_HOST` away from `127.0.0.1` after you have a private-network address ready for the Worker VPS.
`./ops/bin/core-up.sh` reruns preflight automatically and will stop before Docker bring-up if the env file is still invalid.
If `QE_EDGE_PUBLIC_HOST` is set, `./ops/bin/core-up.sh` also starts the bundled Caddy reverse proxy from `ops/production/core/docker-compose.edge.yml`. Keep `QE_API_BIND_HOST=127.0.0.1` and `QE_DASHBOARD_BIND_HOST=127.0.0.1` in that mode so the edge proxy remains the only public surface.
If `QE_DEPLOYMENT_TOPOLOGY=single_vps_compact`, `./ops/bin/core-up.sh` also starts `codex-fabric-runner` on the Core VPS so a second machine is not required.

## 4. Worker VPS

### 4.1 Bootstrap the Worker env file

```bash
cd /opt/quant-evo-nextgen
./ops/bin/bootstrap-node.sh worker
```

If you want the explicit step-by-step path instead, use:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/host-preflight.sh worker
./ops/bin/deploy-config.sh init worker
./ops/bin/deploy-config.sh preflight worker ops/production/worker/worker.env
```

The init helper writes the canonical Worker template with `QE_NODE_ROLE=worker` and prompts for the minimum required relay/database values.

### 4.2 Review `ops/production/worker/worker.env`

Must fill:

- `QE_POSTGRES_URL`
- `QE_OPENAI_API_KEY`
- `QE_OPENAI_BASE_URL` if using a relay

Rules:

- `QE_POSTGRES_URL` must point to Core Postgres over a private network path.
- Do not place broker credentials on the Worker VPS.
- On the Core VPS, change `QE_POSTGRES_BIND_HOST` from `127.0.0.1` to the Core node's private-network IP or Tailscale IP before bringing the Worker online.
`./ops/bin/worker-up.sh` reruns preflight automatically and will stop if the Worker env still points to `localhost`, `127.0.0.1`, `postgres`, or carries Core-only secrets.
Do not bootstrap the Worker env when the topology is `single_vps_compact`; that profile is intentionally Core-only.

## 5. Bring Up Core

```bash
cd /opt/quant-evo-nextgen
./ops/bin/core-up.sh
./ops/bin/core-smoke.sh
```

What this does:

- starts Postgres
- waits for Postgres health
- runs `alembic upgrade head`
- starts API, supervisor, Discord shell, and dashboard
- starts the bundled edge proxy too when `QE_EDGE_PUBLIC_HOST` is configured
- `core-smoke.sh` runs doctor, API health, API doctor endpoint, and dashboard reachability checks from inside the compose network

## 6. Bring Up Worker

```bash
cd /opt/quant-evo-nextgen
./ops/bin/worker-up.sh
./ops/bin/worker-smoke.sh
```

## 7. Enable On Boot

On Core VPS:

```bash
cd /opt/quant-evo-nextgen
sudo ./ops/bin/install-systemd.sh core /opt/quant-evo-nextgen
```

On Worker VPS:

```bash
cd /opt/quant-evo-nextgen
sudo ./ops/bin/install-systemd.sh worker /opt/quant-evo-nextgen
```

## 7.1 Upgrade From GitHub

If the repo on the VPS is tracked from GitHub and you want the simplest safe update path:

Core VPS:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/update-from-github.sh core
```

Worker VPS:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/update-from-github.sh worker
```

This helper refuses to run on a dirty working tree, performs `git pull --ff-only`, then reruns the role-specific bring-up and smoke checks.

## 8. First Post-Deploy Checks

Run on Core VPS:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/core-smoke.sh
```

Then confirm:

- `./ops/bin/core-smoke.sh` reports no `fail`
- `./ops/bin/system-doctor.sh` reports no `fail`
- `/api/v1/system/doctor` shows `node_vps_deploy=ok` before treating the node as deploy-ready
- `/api/v1/system/doctor` should be reviewed together with worker reachability, broker sync state, smoke checks, and the current paper/live activation posture before treating the deployment as production-ready
- `http://127.0.0.1:${QE_API_HOST_PORT:-8000}/healthz` returns `ok: true`
- dashboard loads on the configured dashboard host and port
- Discord bot responds only in the configured control path
- trading dashboard shows broker snapshots after the first broker sync cycle
- `./ops/bin/worker-smoke.sh` reports no `fail` and confirms the Worker container can see `codex`

## 9. Backup

Create a backup on Core VPS:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/backup-postgres.sh
```

This creates:

- SQL dump of Postgres
- compressed archive of `.qe/` runtime state plus the active Core env file

Minimum cadence:

- nightly backup
- before every upgrade
- before switching broker environment from `paper` to `live`

## 10. Restore

Restore on Core VPS:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/restore-postgres.sh .qe/backups/postgres-YYYYMMDDTHHMMSSZ.sql .qe/backups/runtime-YYYYMMDDTHHMMSSZ.tgz
./ops/bin/core-up.sh
./ops/bin/core-smoke.sh
```

## 11. Break-Glass

### 11.1 Stop the stack

```bash
cd /opt/quant-evo-nextgen
./ops/bin/core-down.sh
```

### 11.2 Force a durable trading pause through the API

```bash
curl -X POST http://127.0.0.1:8000/api/v1/operator-overrides \
  -H "Content-Type: application/json" \
  -d '{
    "scope": "trading",
    "action": "pause",
    "reason": "Break-glass manual pause",
    "activated_by": "operator",
    "created_by": "operator",
    "origin_type": "runbook"
  }'
```

### 11.3 Safe operating posture

If broker state, Discord control, or relay quality is uncertain:

- keep `QE_DEFAULT_BROKER_ADAPTER=paper_sim`
- keep live promotion paused
- keep Discord allowlist narrow
- run `core-smoke.sh` before resuming normal automation

## 12. Security Minimums

- Bind API and dashboard to localhost unless they sit behind a reverse proxy.
- Keep Postgres on `127.0.0.1` until the Worker private-network path is ready, then bind it only to a private-network address or a tightly controlled firewall rule.
- Keep broker credentials on Core only.
- Keep `QE_DISCORD_ALLOWED_USER_IDS` populated before exposing the bot.
- Use a strong `QE_POSTGRES_PASSWORD`.
- Keep `QE_DASHBOARD_ACCESS_PASSWORD` and `QE_DASHBOARD_API_TOKEN` strong and secret.
- Keep the API on localhost even when the dashboard is public through the bundled edge proxy.

## 13. Honest Current Limits

This runbook closes the repository-side deploy path, but real activation still depends on environment truth:

- real VPS networking, restart behavior, and Linux service management must be verified on the target nodes
- real secrets, broker sync, and owner allowlists must be configured correctly
- first activation should remain in `paper` mode until smoke checks and broker state are clean
- restore drills and break-glass drills should be rehearsed on the actual VPS nodes before treating the system as unattended

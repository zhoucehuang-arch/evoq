# GitHub to VPS Deployment Guide

This guide is for the owner who wants to publish the repository on GitHub first, then deploy it to VPS nodes with `git clone`, and later maintain it with `git pull`.

## Recommended Starting Point

The product currently supports two valid deployment shapes:

- simplest first deploy: `1 VPS` with `single_vps_compact`
- stronger long-term isolation: `1 Core VPS + 1 Worker VPS`

If this is your first real deployment, start with `1 VPS` unless you already know you need the two-node shape.

## What You Need Before You Start

- a GitHub repository for this project
- one Ubuntu or Debian VPS for the first deploy
- Discord bot token, guild ID, channel IDs, and allowed owner user IDs
- an OpenAI-compatible API key or relay key
- `QE_OPENAI_BASE_URL` if you use a relay
- a market choice for this deployment: `us` or `cn`
- optional broker credentials if you plan to move beyond `paper`

## 1. Push the Project to GitHub

If the local folder is not already a Git repository:

```bash
git init
git branch -M main
git add .
git commit -m "Initial deployable Quant Evo Next-Gen"
git remote add origin <your-github-repo-url>
git push -u origin main
```

If it is already a Git repository:

```bash
git add .
git commit -m "Update deployment-ready runtime"
git push
```

## 2. Deploy the Single-VPS Product Path

Run on the VPS:

```bash
cd /opt
sudo git clone <your-github-repo-url> quant-evo-nextgen
sudo chown -R "$USER":"$USER" /opt/quant-evo-nextgen
cd /opt/quant-evo-nextgen
./ops/bin/quickstart-single-vps.sh
```

This creates the simplest supported product shape:

- Core services
- dashboard
- Discord bot
- Postgres
- Codex runner on the same host

If you want the practical one-liner first-deploy path on a Debian or Ubuntu VPS, use:

```bash
sudo apt-get update && sudo apt-get install -y git && cd /opt && sudo git clone <your-github-repo-url> quant-evo-nextgen && sudo chown -R "$USER":"$USER" /opt/quant-evo-nextgen && cd /opt/quant-evo-nextgen && ./ops/bin/quickstart-single-vps.sh
```

## 3. Fill the Core Env File

Edit:

- `ops/production/core/core.env`

Minimum values:

- `QE_POSTGRES_PASSWORD`
- `QE_DEPLOYMENT_MARKET_MODE`
- `QE_DISCORD_TOKEN`
- `QE_DISCORD_GUILD_ID`
- `QE_DISCORD_CONTROL_CHANNEL_ID`
- `QE_DISCORD_APPROVALS_CHANNEL_ID`
- `QE_DISCORD_ALERTS_CHANNEL_ID`
- `QE_DISCORD_ALLOWED_USER_IDS`
- `QE_OPENAI_API_KEY`
- `QE_OPENAI_BASE_URL` if you use a relay
- `QE_DASHBOARD_ACCESS_USERNAME`
- `QE_DASHBOARD_ACCESS_PASSWORD`
- `QE_DASHBOARD_API_TOKEN`

Recommended safe first-boot values:

- `QE_DEPLOYMENT_TOPOLOGY=single_vps_compact`
- `QE_DEPLOYMENT_MARKET_MODE=us` for the US equities + US options product surface
- `QE_DEFAULT_BROKER_ADAPTER=paper_sim`
- `QE_DEFAULT_BROKER_ENVIRONMENT=paper`
- `QE_POSTGRES_BIND_HOST=127.0.0.1`
- `QE_API_BIND_HOST=127.0.0.1`
- `QE_DASHBOARD_BIND_HOST=127.0.0.1`

If this VPS is for the China A-share product surface, use:

- `QE_DEPLOYMENT_MARKET_MODE=cn`
- `QE_MARKET_TIMEZONE=Asia/Shanghai`
- `QE_MARKET_CALENDAR=XSHG`
- keep the first-boot broker posture on `paper_sim` until the CN broker edge is ready

## 4. Owner-Friendly Draft Control

If you prefer to separate host preparation from app onboarding, use:

```bash
sudo ./ops/bin/install-host-deps.sh
./ops/bin/onboard-single-vps.sh
```

If you prefer to prepare the single-VPS draft first and start the stack later, use:

```bash
./ops/bin/onboard-single-vps.sh --no-start
```

If you want the lower-level owner CLI instead of the shell wrapper, use:

```bash
./ops/bin/deploy-config.sh init core
py -m quant_evo_nextgen.runner.deploy_config --repo-root . onboard-single-vps
py -m quant_evo_nextgen.runner.deploy_config --repo-root . status core
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core relay-base-url https://relay.example.com/v1
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core relay-key <secret>
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core playwright-enabled true
```

## 5. Start and Verify

```bash
cd /opt/quant-evo-nextgen
./ops/bin/core-up.sh
./ops/bin/core-smoke.sh
./ops/bin/system-doctor.sh
```

Also check:

- dashboard loads
- Discord bot responds only in the allowed owner path
- `./ops/bin/system-doctor.sh` reports no `fail`
- `/api/v1/system/doctor` reports no `fail`

## 6. Safe First Activation

Do not switch straight into live trading.

Recommended order:

1. finish the first clean bring-up on the single VPS
2. confirm the deployment market mode is correct for this VPS
3. keep the broker path in `paper`
4. let the first broker sync and reconciliation finish cleanly
5. verify dashboard, Discord, and doctor all agree on runtime health
6. only then consider a paper-broker path or later live approval

## 7. Scale to Core + Worker Later

When you want stronger isolation or more research throughput, keep the same repo and add a second machine:

- Core remains the authority node
- Worker runs Codex-heavy execution and research loops
- broker credentials stay on Core only
- Worker connects to Core Postgres through a private-network address

Bootstrap the Worker later with:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/bootstrap-node.sh worker
./ops/bin/deploy-config.sh init worker
```

Then fill:

- `ops/production/worker/worker.env`

Minimum Worker values:

- `QE_POSTGRES_URL`
- `QE_OPENAI_API_KEY`
- `QE_OPENAI_BASE_URL` if you use a relay

Important rules:

- `QE_POSTGRES_URL` must point to the Core private-network address, not `localhost`
- do not place broker credentials on the Worker
- do not bootstrap a Worker at all when you intentionally stay on `single_vps_compact`

## 8. Enable Start-on-Boot

Single-VPS or Core node:

```bash
cd /opt/quant-evo-nextgen
sudo ./ops/bin/install-systemd.sh core /opt/quant-evo-nextgen
```

Worker node, when used:

```bash
cd /opt/quant-evo-nextgen
sudo ./ops/bin/install-systemd.sh worker /opt/quant-evo-nextgen
```

## 9. Update Later from GitHub

On the single-VPS or Core host:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/update-from-github.sh core
```

On the Worker, when used:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/update-from-github.sh worker
```

## 10. Common Mistakes

- switching to live before the first clean paper deployment
- filling Worker secrets on a one-VPS deployment that does not use a Worker
- leaving `QE_OPENAI_BASE_URL` empty when you depend on a relay
- exposing the API directly to the public internet
- putting broker credentials on the Worker

## Recommended Reading Order

1. [README.md](../../README.md)
2. [VPS-DEPLOYMENT-RUNBOOK.md](VPS-DEPLOYMENT-RUNBOOK.md)
3. [OWNER-OPERATION-QUICKSTART.md](OWNER-OPERATION-QUICKSTART.md)
4. [FIRST-PAPER-RUN-CHECKLIST.md](FIRST-PAPER-RUN-CHECKLIST.md)
5. [CURRENT-DELIVERY-STATUS.md](CURRENT-DELIVERY-STATUS.md)

# Quant Evo Next-Gen

## 中文简介

Quant Evo Next-Gen 是一套面向 Discord / IM 自然语言交互的自主投资系统。

它的目标不是继续叠加 OpenClaw 风格的角色提示词文件，而是把多 agent 讨论、持续联网学习、自进化治理、自动交易、审计留痕、风险控制、Dashboard 可视化、以及 VPS 长期运行能力，收敛成一套更容易治理、恢复、部署和长期维护的系统。

当前仓库的主线是可部署的 next-gen runtime，而不是旧版 prompt-file 架构。

推荐生产拓扑：

- 1 个 Discord Bot
- 1 台 Core VPS
- 1 台 Worker VPS
- Core 持有控制面、数据库、Dashboard、Discord Shell
- Worker 承担 Codex / 研究 / 执行类重任务
- Postgres 作为运行时真实状态

## English Overview

Quant Evo Next-Gen is a Discord-first autonomous investment system built for long-running operation.

Instead of extending the old OpenClaw-style prompt-file runtime, this repository consolidates multi-agent debate, continuous web learning, governed self-improvement, automated trading, auditability, risk controls, dashboard operations, and VPS deployment into a more manageable production architecture.

The active target in this repository is the deployable next-gen runtime, not the legacy prompt layout.

Recommended production topology:

- 1 Discord bot
- 1 Core VPS
- 1 Worker VPS
- Core owns control-plane, database, dashboard, and Discord shell duties
- Worker owns Codex, research, and heavy execution workloads
- Postgres is the runtime source of truth

## What This Repository Contains

- `src/quant_evo_nextgen`: the active Python runtime and control plane
- `apps/dashboard-web`: the operator dashboard web app
- `ops`: VPS deploy, bootstrap, smoke, backup, restore, and systemd helpers
- `docs/next-gen`: architecture, operations, deployment, governance, and review docs
- legacy OpenClaw-era folders kept as historical reference material

## Owner Experience

- Operate mainly through Discord in natural language
- Inspect health, trading, learning, and evolution through the dashboard
- Use SSH mainly for deployment, upgrade, restore, or break-glass repair
- Keep Codex-compatible execution behind governed workflows instead of one-shot agent runs

## Suggested GitHub Repository Description

Chinese:
`面向 Discord 自然语言运营的多智能体自主投资、自进化与交易系统，基于 Codex 兼容执行与双 VPS 长期运行架构。`

English:
`Discord-first autonomous investment, self-improvement, and trading system with governed Codex-compatible workers and a 2-VPS production topology.`

## Start Here

If you want to publish this project to GitHub and then deploy it to VPS, read in this order:

1. [GitHub to VPS Deployment Guide](docs/next-gen/GITHUB-TO-VPS-DEPLOYMENT.md)
2. [VPS Deployment Runbook](docs/next-gen/VPS-DEPLOYMENT-RUNBOOK.md)
3. [Owner Operation Quickstart](docs/next-gen/OWNER-OPERATION-QUICKSTART.md)
4. [Current Delivery Status](docs/next-gen/CURRENT-DELIVERY-STATUS.md)
5. [Next-Gen Docs Index](docs/next-gen/README.md)

## Quick Deploy Summary

1. Push this repository to GitHub.
2. Clone it to `/opt/quant-evo-nextgen` on the Core VPS and Worker VPS.
3. Run `sudo ./ops/bin/install-host-deps.sh` on both nodes.
4. Run `./ops/bin/bootstrap-node.sh core` on Core, and `./ops/bin/bootstrap-node.sh worker` on Worker.
5. Fill the env files, including `QE_OPENAI_API_KEY` and `QE_OPENAI_BASE_URL` if you use a relay.
6. Start the stacks with `./ops/bin/core-up.sh` and `./ops/bin/worker-up.sh`.
7. Verify with `./ops/bin/core-smoke.sh` and `./ops/bin/worker-smoke.sh`.
8. Keep the first activation in `paper` mode before any live promotion.

For later GitHub-based upgrades on the VPS nodes, you can use:

- `./ops/bin/update-from-github.sh core`
- `./ops/bin/update-from-github.sh worker`

If you prefer the explicit preflight path instead of the guided bootstrap wrapper, use:

- `./ops/bin/host-preflight.sh core`
- `./ops/bin/deploy-config.sh init core`
- `./ops/bin/deploy-config.sh preflight core ops/production/core/core.env`
- `./ops/bin/host-preflight.sh worker`
- `./ops/bin/deploy-config.sh init worker`
- `./ops/bin/deploy-config.sh preflight worker ops/production/worker/worker.env`

## Relay / Codex Note

This system supports OpenAI-compatible relays and Codex-compatible execution.

If your API provider is a relay, configure at least:

- `QE_OPENAI_API_KEY`
- `QE_OPENAI_BASE_URL`

These values should be present on both Core and Worker nodes so the control plane and Codex execution fabric can both work correctly.

## Current Status

Repository-side implementation is in handoff state: the next major step is actual VPS deployment and environment-specific activation, not another foundational architecture rewrite.

What still must be validated on the real target nodes:

- real secrets
- broker sync
- paper-to-live promotion discipline
- restore drill and break-glass drill
- actual VPS networking and service restart behavior

## Documentation Map

- [GitHub to VPS Deployment Guide](docs/next-gen/GITHUB-TO-VPS-DEPLOYMENT.md)
- [VPS Deployment Runbook](docs/next-gen/VPS-DEPLOYMENT-RUNBOOK.md)
- [Backup and Restore Runbook](docs/next-gen/BACKUP-AND-RESTORE-RUNBOOK.md)
- [Break-Glass Runbook](docs/next-gen/BREAK-GLASS-RUNBOOK.md)
- [Owner Operation Quickstart](docs/next-gen/OWNER-OPERATION-QUICKSTART.md)
- [Current Delivery Status](docs/next-gen/CURRENT-DELIVERY-STATUS.md)
- [Next-Gen Architecture Index](docs/next-gen/README.md)

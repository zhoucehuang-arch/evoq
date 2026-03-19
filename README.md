# Quant Evo Next-Gen

## English

Quant Evo Next-Gen is an autonomous investment platform designed for long-running operation on VPS infrastructure.

It brings research, multi-agent review, strategy development, governed execution, risk control, operator approvals, and dashboard monitoring into one system. The main operator experience is built around Discord and a web dashboard, so the owner can manage the system in natural language without living in the terminal.

### What This Project Does

- Collects and organizes market research and external information
- Uses specialized agents to debate, review, and refine ideas before action
- Turns research into strategy proposals, backtests, paper runs, and production decisions
- Runs governed trading workflows with audit trails, approvals, and rollback paths
- Exposes runtime status through Discord and a dashboard
- Supports long-running deployment on VPS infrastructure with recovery and maintenance workflows

### How It Is Meant To Be Used

- Discord is the main control surface for the owner
- The dashboard is the main monitoring surface for health, trading, learning, and system state
- Core services keep durable state, supervision, approvals, and trading authority
- Worker services handle heavier research and Codex-powered execution tasks

### Recommended Deployment Shape

- 1 Discord bot
- 1 Core VPS
- 1 Worker VPS
- Postgres as the runtime source of truth
- Paper mode first, then controlled promotion to live

### Repository Layout

- `src/quant_evo_nextgen`: backend runtime, control plane, services, and workflows
- `apps/dashboard-web`: operator dashboard
- `ops`: deployment scripts, smoke checks, backup, restore, and systemd helpers
- `docs/next-gen`: architecture, operations, deployment, and runbooks
- `tests`: regression and service-level coverage

### Getting Started

If you want to publish this project to GitHub and deploy it to VPS nodes, start here:

1. [GitHub to VPS Deployment Guide](docs/next-gen/GITHUB-TO-VPS-DEPLOYMENT.md)
2. [VPS Deployment Runbook](docs/next-gen/VPS-DEPLOYMENT-RUNBOOK.md)
3. [Owner Operation Quickstart](docs/next-gen/OWNER-OPERATION-QUICKSTART.md)
4. [Current Delivery Status](docs/next-gen/CURRENT-DELIVERY-STATUS.md)
5. [Next-Gen Docs Index](docs/next-gen/README.md)

### Quick Deploy Summary

1. Push this repository to GitHub.
2. Clone it to `/opt/quant-evo-nextgen` on the Core VPS and Worker VPS.
3. Run `sudo ./ops/bin/install-host-deps.sh` on both nodes.
4. Run `./ops/bin/bootstrap-node.sh core` on Core and `./ops/bin/bootstrap-node.sh worker` on Worker.
5. Fill the env files, including `QE_OPENAI_API_KEY` and `QE_OPENAI_BASE_URL` if you use a relay.
6. Start the services with `./ops/bin/core-up.sh` and `./ops/bin/worker-up.sh`.
7. Verify with `./ops/bin/core-smoke.sh` and `./ops/bin/worker-smoke.sh`.
8. Keep the first activation in `paper` mode before any live promotion.

For GitHub-based upgrades later:

- `./ops/bin/update-from-github.sh core`
- `./ops/bin/update-from-github.sh worker`

If you prefer the explicit preflight path:

- `./ops/bin/host-preflight.sh core`
- `./ops/bin/deploy-config.sh init core`
- `./ops/bin/deploy-config.sh preflight core ops/production/core/core.env`
- `./ops/bin/host-preflight.sh worker`
- `./ops/bin/deploy-config.sh init worker`
- `./ops/bin/deploy-config.sh preflight worker ops/production/worker/worker.env`

### Relay Support

This system supports OpenAI-compatible relay endpoints and Codex-compatible execution.

When you use a relay, configure these values on both Core and Worker nodes:

- `QE_OPENAI_API_KEY`
- `QE_OPENAI_BASE_URL`

### Documentation

- [GitHub to VPS Deployment Guide](docs/next-gen/GITHUB-TO-VPS-DEPLOYMENT.md)
- [VPS Deployment Runbook](docs/next-gen/VPS-DEPLOYMENT-RUNBOOK.md)
- [Backup and Restore Runbook](docs/next-gen/BACKUP-AND-RESTORE-RUNBOOK.md)
- [Break-Glass Runbook](docs/next-gen/BREAK-GLASS-RUNBOOK.md)
- [Owner Operation Quickstart](docs/next-gen/OWNER-OPERATION-QUICKSTART.md)
- [Current Delivery Status](docs/next-gen/CURRENT-DELIVERY-STATUS.md)
- [Next-Gen Architecture Index](docs/next-gen/README.md)

## 中文

Quant Evo Next-Gen 是一套面向 VPS 长期运行的自主投资平台。

它把研究、多个 agent 的讨论与评审、策略生成、受治理的执行、风控、审批、运行监控和仪表板整合在同一套系统里。整个产品的主要使用方式是 Discord 自然语言交互加 Dashboard 观察面，让使用者不需要长期停留在命令行里，也能管理整个系统。

### 这个项目能做什么

- 持续收集、整理和沉淀市场研究与外部信息
- 通过不同角色的 agent 进行讨论、评审和交叉校验
- 将研究结果推进为策略提案、回测、纸面运行和生产决策
- 以可审计、可审批、可回滚的方式执行交易流程
- 通过 Discord 和 Dashboard 暴露系统运行状态
- 支持在 VPS 上长期运行，并具备维护、恢复和运维流程

### 这个项目怎么使用

- Discord 是面向使用者的主要控制面
- Dashboard 是查看健康状态、交易状态、学习状态和系统状态的主要观察面
- Core 服务负责状态、监督、审批和交易权限
- Worker 服务负责更重的研究任务和基于 Codex 的执行任务

### 推荐部署形态

- 1 个 Discord Bot
- 1 台 Core VPS
- 1 台 Worker VPS
- 使用 Postgres 作为运行时真实状态
- 第一次先用 `paper` 模式运行，再逐步推进到 live

### 仓库结构

- `src/quant_evo_nextgen`：后端运行时、控制面、服务和工作流
- `apps/dashboard-web`：操作仪表板
- `ops`：部署脚本、烟雾测试、备份、恢复和 systemd 辅助脚本
- `docs/next-gen`：架构、运维、部署和运行手册
- `tests`：回归测试和服务级验证

### 从哪里开始

如果你要把项目上传到 GitHub，并部署到 VPS，请按这个顺序阅读：

1. [GitHub to VPS Deployment Guide](docs/next-gen/GITHUB-TO-VPS-DEPLOYMENT.md)
2. [VPS Deployment Runbook](docs/next-gen/VPS-DEPLOYMENT-RUNBOOK.md)
3. [Owner Operation Quickstart](docs/next-gen/OWNER-OPERATION-QUICKSTART.md)
4. [Current Delivery Status](docs/next-gen/CURRENT-DELIVERY-STATUS.md)
5. [Next-Gen Docs Index](docs/next-gen/README.md)

### 快速部署摘要

1. 先把仓库推送到 GitHub。
2. 在 Core VPS 和 Worker VPS 上 clone 到 `/opt/quant-evo-nextgen`。
3. 两台机器都运行 `sudo ./ops/bin/install-host-deps.sh`。
4. Core 运行 `./ops/bin/bootstrap-node.sh core`，Worker 运行 `./ops/bin/bootstrap-node.sh worker`。
5. 填写环境变量文件；如果使用中转，还要填写 `QE_OPENAI_API_KEY` 和 `QE_OPENAI_BASE_URL`。
6. 使用 `./ops/bin/core-up.sh` 和 `./ops/bin/worker-up.sh` 启动服务。
7. 用 `./ops/bin/core-smoke.sh` 和 `./ops/bin/worker-smoke.sh` 做检查。
8. 第一次上线先保持 `paper` 模式，不要直接切 live。

后续通过 GitHub 更新时，可以直接使用：

- `./ops/bin/update-from-github.sh core`
- `./ops/bin/update-from-github.sh worker`

如果你更希望使用显式的预检查路径：

- `./ops/bin/host-preflight.sh core`
- `./ops/bin/deploy-config.sh init core`
- `./ops/bin/deploy-config.sh preflight core ops/production/core/core.env`
- `./ops/bin/host-preflight.sh worker`
- `./ops/bin/deploy-config.sh init worker`
- `./ops/bin/deploy-config.sh preflight worker ops/production/worker/worker.env`

### 中转支持

这套系统支持 OpenAI 兼容中转和 Codex 兼容执行。

如果你使用中转，Core 和 Worker 两边都需要配置：

- `QE_OPENAI_API_KEY`
- `QE_OPENAI_BASE_URL`

### 文档入口

- [GitHub to VPS Deployment Guide](docs/next-gen/GITHUB-TO-VPS-DEPLOYMENT.md)
- [VPS Deployment Runbook](docs/next-gen/VPS-DEPLOYMENT-RUNBOOK.md)
- [Backup and Restore Runbook](docs/next-gen/BACKUP-AND-RESTORE-RUNBOOK.md)
- [Break-Glass Runbook](docs/next-gen/BREAK-GLASS-RUNBOOK.md)
- [Owner Operation Quickstart](docs/next-gen/OWNER-OPERATION-QUICKSTART.md)
- [Current Delivery Status](docs/next-gen/CURRENT-DELIVERY-STATUS.md)
- [Next-Gen Architecture Index](docs/next-gen/README.md)

# FAQ

## What is this project?

Quant Evo Next-Gen is a Discord-operated investment platform with research, strategy, execution, governance, and monitoring built into one system.

## Do I need to use the terminal every day?

No. The intended owner workflow is:

- Discord for control and approvals
- Dashboard for monitoring and review
- SSH only for deployment, upgrade, restore, or break-glass work

## How many VPS nodes do I need?

Recommended production shape:

- 1 Core VPS
- 1 Worker VPS

You can experiment locally, but the intended long-running setup is two nodes.

## How many Discord bots do I need?

One bot.

The system is designed around one operator-facing Discord bot, not one bot per agent persona.

## Can I use an OpenAI-compatible relay?

Yes.

Set these on both Core and Worker:

- `QE_OPENAI_API_KEY`
- `QE_OPENAI_BASE_URL`

## Where should broker credentials live?

On Core only.

Do not place broker credentials on the Worker node.

## Should I start in live trading mode?

No.

Start in `paper` mode, complete smoke checks, verify broker sync behavior, and only then move toward live activation.

## What does the Worker do?

The Worker handles heavier Codex-powered execution and research tasks so the Core can stay focused on authority, state, governance, and runtime control.

## How do I update the system after deployment?

On each node:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/update-from-github.sh core
```

or on the Worker:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/update-from-github.sh worker
```

## How do I know the deploy is healthy?

Check:

- `./ops/bin/core-smoke.sh`
- `./ops/bin/worker-smoke.sh`
- `/api/v1/system/doctor`
- dashboard health
- Discord command responsiveness

## Where should I start reading?

1. [PRODUCT-OVERVIEW.md](PRODUCT-OVERVIEW.md)
2. [GITHUB-TO-VPS-DEPLOYMENT.md](GITHUB-TO-VPS-DEPLOYMENT.md)
3. [OWNER-OPERATION-QUICKSTART.md](OWNER-OPERATION-QUICKSTART.md)
4. [CURRENT-DELIVERY-STATUS.md](CURRENT-DELIVERY-STATUS.md)

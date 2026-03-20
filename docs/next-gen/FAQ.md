# FAQ

## What is this project?

Quant Evo Next-Gen is a Discord-operated investment platform with research, strategy, execution, governance, and monitoring built into one system.

## Do I need to use the terminal every day?

No. The intended owner workflow is:

- Discord for control and approvals
- Dashboard for monitoring and review
- SSH only for deployment, upgrade, restore, or break-glass work

## How many VPS nodes do I need?

Recommended long-term production shape:

- 1 Core VPS
- 1 Worker VPS

Simplest supported product path:

- 1 VPS with the `single_vps_compact` profile

That one-VPS mode keeps the same Discord and dashboard experience, but runs the Codex worker runtime on the Core host too. The intended long-running upgrade path is still two nodes.

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

## How does web research work without paid search APIs?

The intended order is:

- Codex web search
- self-hosted metasearch or search/scrape fallback
- official feeds and RSSHub
- Playwright browser fallback

Browser automation is important, but it is treated as a governed fallback instead of the default research path.

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

## What should I read before the first paper activation?

Start here:

1. [GITHUB-TO-VPS-DEPLOYMENT.md](GITHUB-TO-VPS-DEPLOYMENT.md)
2. [FIRST-PAPER-RUN-CHECKLIST.md](FIRST-PAPER-RUN-CHECKLIST.md)
3. [OPERATOR-JOURNEYS.md](OPERATOR-JOURNEYS.md)
4. [OWNER-OPERATION-QUICKSTART.md](OWNER-OPERATION-QUICKSTART.md)

## Where should I start reading?

1. [PRODUCT-OVERVIEW.md](PRODUCT-OVERVIEW.md)
2. [GITHUB-TO-VPS-DEPLOYMENT.md](GITHUB-TO-VPS-DEPLOYMENT.md)
3. [FIRST-PAPER-RUN-CHECKLIST.md](FIRST-PAPER-RUN-CHECKLIST.md)
4. [OWNER-OPERATION-QUICKSTART.md](OWNER-OPERATION-QUICKSTART.md)
5. [CURRENT-DELIVERY-STATUS.md](CURRENT-DELIVERY-STATUS.md)

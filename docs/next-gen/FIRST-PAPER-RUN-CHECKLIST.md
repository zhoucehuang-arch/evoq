# First Paper Run Checklist

This page is the shortest safe path from "the repo is deployed" to "the system is running its first trustworthy paper session."

Use it after both VPS nodes are provisioned and before any live promotion is even discussed.

## Success Criteria

You are done with this checklist only when all of the following are true:

- Core and Worker both pass smoke checks
- the dashboard loads and shows non-broken freshness
- Discord responds only for approved owner identities and channels
- the broker adapter is still in `paper` mode
- the first broker sync and reconciliation cycle look sane
- there are no unexplained overrides, halted loops, or red incidents

## Before You Start

Confirm these assumptions:

- the repository is cloned to `/opt/evoq` on both nodes
- `QE_OPENAI_API_KEY` is present on both nodes
- `QE_OPENAI_BASE_URL` is set on both nodes if you use a relay
- broker credentials exist on Core only
- Worker `QE_POSTGRES_URL` points to the Core private-network address, not `localhost`

## Step 1. Bring Up Core

Run on Core:

```bash
cd /opt/evoq
./ops/bin/core-up.sh
./ops/bin/core-smoke.sh
```

Stop and fix the environment if `core-smoke.sh` reports any `fail`.

## Step 2. Bring Up Worker

Run on Worker:

```bash
cd /opt/evoq
./ops/bin/worker-up.sh
./ops/bin/worker-smoke.sh
```

Stop and fix the environment if `worker-smoke.sh` reports any `fail`.

## Step 3. Confirm Owner Surfaces

Verify:

- the dashboard opens successfully
- Discord is reachable
- only the intended owner accounts and channels can control the bot
- the dashboard and Discord agree on basic system state

## Step 4. Confirm Safe Trading Posture

Verify:

- `QE_DEFAULT_BROKER_ENVIRONMENT=paper`
- there is no accidental live broker binding
- there are no unexplained trading overrides
- recent incidents do not show broker or reconciliation failures

## Step 5. Wait For The First Healthy Sync Cycle

Do not rush this step.

Wait for:

- the first broker snapshot
- the first reconciliation result
- the first strategy/trading dashboard refresh
- the first worker-to-core research writeback

If any of these look stale, broken, or contradictory, treat the activation as incomplete.

## Step 6. Record A Go Or No-Go Decision

The first paper run should end with an explicit operator judgment:

- `go`: the system is healthy enough to continue paper observation
- `no-go`: the system stays in safe mode until the problem is understood

Useful evidence to capture:

- screenshot of the dashboard Overview and Trading pages
- the latest `core-smoke.sh` and `worker-smoke.sh` outputs
- the first successful Discord status exchange
- notes about any incident, override, or loop that needed intervention

## Stop Conditions

Do not move forward if any of these is true:

- dashboard freshness is `broken`
- Discord is responding in the wrong channel or for the wrong account
- worker execution cannot reach the configured provider or relay
- broker sync is missing, stale, or inconsistent
- system state looks healthy in one surface but unhealthy in another

## What This Checklist Does Not Mean

Passing this checklist does not mean the system is ready for unattended live trading.

It means only that the deployment is healthy enough to continue paper-mode observation and controlled operator review.

## Read Next

- [OPERATOR-JOURNEYS.md](OPERATOR-JOURNEYS.md)
- [OWNER-OPERATION-QUICKSTART.md](OWNER-OPERATION-QUICKSTART.md)
- [CURRENT-DELIVERY-STATUS.md](CURRENT-DELIVERY-STATUS.md)

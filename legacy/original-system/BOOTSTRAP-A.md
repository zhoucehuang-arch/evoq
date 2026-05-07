# OpenClaw System A Bootstrap Guide - Self-Evolving System

This document is the bootstrap guide for the Self-Evolution System. The system runs as three separate OpenClaw instances (Explorer, Critic, Evolver), each with its own Discord bot identity. After reading this document, the system should be able to complete configuration and start the first evolution cycle.

## Who You Are

You are a quantitative strategy self-evolving system composed of three agents running as three independent OpenClaw instances:
- **Explorer** (`Bot-Explorer`): researches papers and news, proposes strategy hypotheses, explores capability improvements
- **Critic** (`Bot-Critic`): stress-tests strategies, identifies flaws, assesses feasibility
- **Evolver** (`Bot-Evolver`): adjudicates debates, executes backtests, manages evolution cycles

Each agent runs as a separate Discord bot. Agents communicate by posting messages to shared Discord channels. All bots have `allowBots: true` enabled, so they can see and respond to each other's messages.

Your mission is to run 24/7 and continuously evolve quantitative trading strategies and system capabilities through a triangular adversarial mechanism.

## Configuration Steps

### Step 1: Environment Variables

Each instance has its own `.env.template`:
- `config/instance-explorer/.env.template` -> one API key (`OPENAI_KEY_A1`) + Bot-Explorer token
- `config/instance-critic/.env.template` -> one API key (`OPENAI_KEY_A2`) + Bot-Critic token
- `config/instance-evolver/.env.template` -> one API key (`OPENAI_KEY_A3`) + Bot-Evolver token

All three instances share the same GitHub PAT and Guild ID.

### Step 2: Discord Channels

Create the following channels in the Discord server:

| Channel Name | Used By | Purpose |
|---|---|---|
| `#a-arena` | Explorer + Critic + Evolver | Debate arena (hypotheses, challenges, triggers) |
| `#a-verdict` | Evolver | Verdicts + backtest reports |
| `#a-research` | Explorer | Paper and news discoveries |
| `#a-report` | Evolver (write) + All (read) | Reports + admin directions |
| `#bridge` | Evolver | Cross-system sync with System B |
| `#admin` | Evolver | System health + escalations |

### Step 3: Agent Configuration

Each instance has its own config directory:
- `config/instance-explorer/agents/explorer/` -> `SOUL.md`, `AGENTS.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`
- `config/instance-critic/agents/critic/` -> `SOUL.md`, `AGENTS.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`
- `config/instance-evolver/agents/evolver/` -> `SOUL.md`, `AGENTS.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`

### Step 4: Understand Communication Protocols

Read the following protocol files:
- `protocols/schemas.md` for message formats
- `protocols/orchestration.md` for cycle orchestration rules
- `protocols/schedules.md` for the runtime schedule
- `protocols/discord-permissions.md` for channel access rules

## Cold Start: First Cycle

Start the three instances in this order:

1. Start the Evolver instance first because it drives the cycle.
2. Start the Explorer and Critic instances so they can respond to triggers.

Evolver cold-start sequence:
1. Check `evo/feature_map.json`; if it is empty, enter cold-start mode.
2. Read seed strategies from `strategies/candidates/`.
3. Run backtests on seed strategies and populate the first cell of the feature map.
4. Post a cold-start completion notification in `#a-report`.
5. Post `CYCLE_TRIGGER` in `#a-arena` so Bot-Explorer begins research.
6. Begin the normal evolution cycle (Explorer -> Critic -> Evolver loop via Discord).

## Strategy Focus

Core strategy directions for this system:
- **Frequency**: medium-high frequency (holding period 5 minutes to 5 days)
- **Style**: medium to short term, aggressive
- **Strategy Types**: momentum, mean reversion, stat arb, event driven, insider following, options flow, sentiment driven
- **Assets**: US equities (via Alpaca)
- **Objective**: maximize Sharpe ratio while keeping max drawdown below 15%

## Three Cycle Modes

The system operates in three modes selected by Evolver each cycle:
- **Mode A - Strategy Discovery** (~60%): research -> hypothesize -> debate -> backtest
- **Mode B - Strategy Optimization** (~15%): diagnose underperforming strategies -> improve -> validate
- **Mode C - Capability Evolution** (~25%): explore cross-disciplinary improvements -> propose -> adopt

## Runtime Schedule

See `protocols/schedules.md` for details. Core rhythm:
- **Micro-cycle**: one full cycle every two hours (research -> debate -> verdict -> backtest -> reflection)
- **Synthesis cycle**: every six hours, aggregate recent results
- **Evolution cycle**: daily at 22:00 UTC, meta-reflection + feature map analysis
- **24/7 operation**: runs on both trading days and non-trading days, with different mode allocations

## Admin Interaction

The admin can interact with System A by posting messages in `#a-report`. Evolver reads admin directions and adjusts priorities accordingly. Examples:
- "Focus on momentum strategies this week"
- "Increase Mode C frequency"
- "Pause evolution for maintenance"

All admin reports should be written in English.

## Key File Paths

| Path | Purpose | Permissions |
|---|---|---|
| `strategies/candidates/` | Backtest-passed candidate strategies | Read-write |
| `evo/feature_map.json` | MAP-Elites feature map | Read-write |
| `evo/cycles/` | Micro-cycle records | Read-write |
| `memory/principles/` | Effective strategy principles | Read-write |
| `memory/causal/` | Causal relationship memory | Read-write |
| `memory/reflections/` | Failure reflections | Read-write |
| `knowledge/papers/` | Paper distillations | Read-write |
| `knowledge/strategy-frameworks.md` | Reference frameworks | Read-write |
| `trading/metrics/` | System B performance feedback | Read-only |

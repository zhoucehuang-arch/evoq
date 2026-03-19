# System Restart Handoff · 2026-03-18

> Purpose: capture the current system architecture, roles, runtime, strategy state, operating rules, learned admin preferences, active issues, hidden assumptions, and restart checkpoints into the project before a possible rebuild/restart.
>
> Important: this handoff is **sanitized**. Secrets/tokens/api keys are intentionally excluded.

## 1. Current overall system picture

### 1.1 High-level split
The project currently operates as a split A/B system:

- **System A**: research / evolution / idea generation / experimentation
- **System B**: execution-side operating system for Alpaca paper trading

### 1.2 Current B-side instance topology on this host
This host currently exposes these local OpenClaw agents:

- `main` → display name: `wattson_nadah`
- `operator` → System B operator / PM-COO / coordination hub
- `trader` → System B signal generation and order execution role
- `guardian` → System B risk / halt / monitoring role

### 1.3 Channel ownership observed in current local config
Bindings currently show:

- `#b-ops` → operator
- `#b-desk` → trader
- `#b-risk` → guardian
- `#b-report` → operator
- `#bridge` → operator
- `#admin` → operator
- `main` agent is bound to another Discord channel and appears as the wattson-facing general agent

## 2. Repo and knowledge layout

Project repo root:
- `/root/.openclaw/workspace/repos/quant-evo-do-test`

Important top-level directories:
- `config/`
- `docs/`
- `evo/`
- `knowledge/`
- `memory/`
- `protocols/`
- `strategies/`
- `trading/`

### 2.1 Repo subtrees that matter most
- `config/instance-b/agents/` → B-side related config assets
- `config/instance-explorer/agents/`
- `config/instance-critic/agents/`
- `config/instance-evolver/agents/`
- `knowledge/market/`, `knowledge/papers/`, `knowledge/sources/`
- `memory/architecture/`, `memory/operations/`, `memory/principles/`, `memory/runtime/`
- `protocols/orchestration.md`, `protocols/schedules.md`, `protocols/schemas.md`
- `strategies/candidates/`, `strategies/staging/`, `strategies/production/`
- `trading/metrics/realtime/`, `trading/logs/`, `trading/positions/`

## 3. B-side role definitions

### 3.1 Operator
Source of role rules:
- `bot-b/operator/AGENTS.md`
- `bot-b/operator/SOUL.md`
- `bot-b/operator/TOOLS.md`
- `bot-b/operator/USER.md`
- `bot-b/operator/HEARTBEAT.md`

Main function:
- deployment coordination
- strategy promotion / withdrawal governance
- human/admin reporting
- A↔B bridge and runtime coordination
- incident handling, checkpoint handling, anti-stall governance

### 3.2 Trader
Source of role rules:
- `bot-b/trader/AGENTS.md`

Main function:
- read active strategies from `strategies/production/`
- fetch Alpaca market/account data
- generate signals
- submit / monitor orders
- write execution outputs to `trading/logs/`
- respect hard limits and Guardian HALT

### 3.3 Guardian
Source of role rules:
- `bot-b/guardian/AGENTS.md`

Main function:
- monitor PnL / VaR / exposure / concentration / correlation
- publish WARNING / CRITICAL / HALT
- write risk/performance snapshots to `trading/metrics/realtime/`
- independently stop execution via HALT

## 4. Strategy state currently in repo

### 4.1 Candidates
`strategies/candidates/` contains many exploratory or hypothesis files, including themes such as:
- options flow
- pre-earnings drift
- insider cluster
- flow regime recovery
- congressional/options breakout

### 4.2 Staging
Current staging files include:
- `adaptive_basket_event_react_v1.py`
- `adaptive_basket_momo_breakout_v1.py`
- `adaptive_basket_momo_breakout_v2.py`
- `adaptive_basket_mr_pullback_v1.py`
- `multi_logic_router_v1.py`
- `multi_logic_router_v2.py`
- `solid_altflow_technical_v1.py`
- `solid_altflow_technical_v2.py`

### 4.3 Production
Critical current fact:
- `strategies/production/` currently contains only `.gitkeep`
- This means **there is no active production strategy file on disk right now**

This is likely one of the direct reasons why no new trade generation has been advancing.

## 5. Trading / metrics state observed at handoff time

### 5.1 Live account connectivity
Recent refresh shows:
- Alpaca paper account reachable
- account status `ACTIVE`
- positions still exist
- latest paper account snapshot refresh is alive

### 5.2 Current break in pipeline
Observed mismatch:
- `paper_account_snapshot_latest.json` is fresh
- but `opportunity_research_latest.json` is stale at 2026-03-07
- and `community_signal_watch_latest.json` is stale at 2026-03-07

Interpretation:
- broker/account path is alive
- portfolio snapshot path is alive
- but research/opportunity generation is stale
- execution-generation chain is not advancing correctly

### 5.3 Trading inactivity concern
Admin observation is consistent with current evidence:
- no meaningful new trading action after ~2026-03-07
- account is not flat, but appears to be carrying legacy positions rather than actively generating new validated orders

## 6. Current enabled automation jobs on this host

Enabled jobs observed in current cron store:
- `a-network-learning-dispatch-v1`
- `b-opportunity-dispatch-v1`
- `b-snapshot-refresh-5m-v1`
- `b-report-autopublish-v3-30m`
- `a-hourly-report-autopublish-v1`
- `trading-hours-health-15m-v1`
- `preopen-action-plan-5m-v1` (moved to 20:30 BJT = 08:30 ET)
- `post-market-review-daily-v1`
- `daily-evolution-report-daily-v1`
- `kj-clove-repair-progress-15m-v1`
- `open-bell-report-v1` (21:30 BJT = 09:30 ET)
- `first-30m-open-report-v1` (22:00 BJT = 10:00 ET)

Important disabled or stale-relevant items observed:
- `trader-research-tick-lite` is disabled
- several audit/guard jobs are disabled

## 7. Admin preferences and standing policies recently added

Recent explicit admin preferences written into memory include:
- `memory/preferences/admin_continuous_autonomous_operation_20260318.md`
- `memory/preferences/admin_immediate_error_repair_not_hourly_report_20260318.md`
- `memory/preferences/admin_sleep_autonomous_supervision_20260318.md`
- `memory/preferences/admin_strategy_universe_options_shorts_20260318.md`

These imply the following standing rules:
1. do not wait for admin nudges
2. keep running continuously
3. errors must trigger immediate repair, not next-report delay
4. system should not search only long-equity opportunities
5. options / shorts / hedges are allowed in principle, subject to execution and risk checks

## 8. Protocols and knowledge sources to preserve

Current project protocol files:
- `protocols/discord-permissions.md`
- `protocols/discussion-rules.md`
- `protocols/orchestration.md`
- `protocols/schedules.md`
- `protocols/schemas.md`

Current memory tree in repo:
- `memory/architecture/`
- `memory/causal/`
- `memory/daily/`
- `memory/operations/`
- `memory/principles/`
- `memory/reflections/`
- `memory/runtime/`
- `memory/templates/`

These directories should be preserved in any rebuild because they encode operational history and learned guardrails.

## 9. Current known problems / active risks

### 9.1 Execution-side stall
Most important current issue:
- account connectivity is alive
- but opportunity/research outputs are stale
- trader execution generation appears stalled
- production strategy set is empty

### 9.2 Report ownership drift / speaker drift
Observed admin confusion is valid:
- A-side content has sometimes been surfaced through the operator/wattson path
- that is a governance / routing problem, not the intended role design

### 9.3 Cron / gateway delivery quirks
Recent logs showed issues like:
- `cron announce delivery failed`
- `gateway closed (1008): pairing required`
- slow Discord listener warnings
- qmd embed timeouts

Meaning:
- the system may be partially alive while some delivery/reporting channels are degraded
- messaging health and execution health are not the same thing

### 9.4 Production strategy gap
If `strategies/production/` remains empty, new trade generation should not be expected from a production-only execution model.
This is a structural issue, not just a scheduler issue.

## 10. Assumptions, blind spots, and things easy to miss

These are the main assumptions that may have been implicitly carried and should be made explicit:

1. **Assumption: account freshness means execution health**
   - False. Account snapshots can update while research/execution is stale.

2. **Assumption: no new trades means no opportunities existed**
   - Not proven. It may also mean disabled emitters, empty production, stale research artifacts, or broken routing.

3. **Assumption: A/B reporting ownership is cleanly separated in output**
   - False in practice. There has been speaker drift.

4. **Assumption: production strategy directory reflects intended live trading set**
   - Currently it does not contain active strategy files.

5. **Assumption: all important rules are in one place**
   - False. Critical behavior is split across:
     - repo files
     - bot-b role files
     - local OpenClaw config
     - cron jobs store
     - memory preference files
     - Discord channel routing

6. **Assumption: restart alone fixes the main issue**
   - Not necessarily. If the research/execution chain is logically disabled or if production is empty, restart will not be sufficient.

## 11. What should survive any rebuild/restart

At minimum, preserve these categories:

1. **Role rules**
- `bot-b/operator/*`
- `bot-b/trader/*`
- `bot-b/guardian/*`

2. **Protocols**
- `protocols/*`

3. **Knowledge**
- `knowledge/*`

4. **Repo memory**
- `memory/*`

5. **Strategy inventory**
- `strategies/candidates/*`
- `strategies/staging/*`
- `strategies/production/*`

6. **Execution evidence**
- `trading/logs/*`
- `trading/metrics/realtime/*`
- `trading/positions/*`

7. **Recent admin preferences**
- local memory preference files listed in section 7 should be copied or re-applied

8. **Cron/routing design**
- enabled jobs list
- channel ownership/bindings
- report timing rules (08:30 ET / 09:30 ET / 10:00 ET / intraday hourly)

## 12. Recommended restart/rebuild checklist

Before restart/rebuild:
1. preserve this file
2. preserve the redacted runtime snapshot JSON next to it
3. preserve `memory/preferences/*` directives
4. preserve repo `memory/`, `protocols/`, `knowledge/`, `strategies/`, `trading/`
5. note current branch and commit

After restart/rebuild, verify in this exact order:
1. gateway status healthy
2. Discord routing/bindings correct
3. paper account snapshot refresh working
4. research/opportunity artifacts refreshing again
5. Trader emitter active
6. Guardian risk loop active
7. production strategy set explicitly verified
8. one of:
   - new trade generation evidence
   - or fresh evidence that no trade is correct today for real reasons, not stale chain reasons

## 13. Current repo state reference

At handoff time:
- repo branch: `main`
- repo commit: `e60b301de86395a931ad36b6f471c73687e1be20`

## 14. Sensitive data intentionally excluded

This document intentionally does **not** include:
- API keys
- gateway auth tokens
- Discord tokens
- Telegram tokens
- broker secrets
- raw environment secret values

If the system is rebuilt, those should be reattached from secure secret storage, not copied from a project markdown file.

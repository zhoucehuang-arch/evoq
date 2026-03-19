# Multi-Instrument Trading Audit And Pre-VPS Plan

## 1. Purpose

This document closes a dangerous ambiguity in the current system state.

The codebase already has a governed trading skeleton, but the owner's target is broader:

- equities
- options
- leveraged long exposure
- short exposure
- durable autonomous operation
- Discord-first natural-language control
- VPS deployment that remains governable by a non-technical owner

The goal of this document is to separate:

- what the system truly supports today
- what only looks present in schema fields
- what must be completed before the first real VPS deployment

## 2. Current Verdict

Short version:

- The current system has a usable governed trading skeleton for equity-style order flow.
- It does not yet have real options trading support.
- It has only partial short-selling support.
- It does not yet have real leveraged or margin-aware trading support.
- Therefore it is not yet ready for the owner's target trading surface.

## 3. What Exists Today

The system already has real progress in the following areas:

- durable allocation policy
- durable order intents
- durable broker order records
- durable position records
- readiness checks
- paper adapter execution
- external-style broker sync, cancel, replace, and restart recovery scaffolding
- reconciliation-triggered halts
- dashboard visibility for current execution state

This means the project is beyond a mockup.

However, the current implementation is still mostly equity-centric.

## 4. Code-Level Audit Findings

### 4.1 Domain model is not yet instrument-complete

Current contracts show the gap clearly:

- `allow_short` exists as a policy flag
- `asset_type` exists as a string field
- order side is still only `buy | sell`

That means the schema can label an order as an option, but it does not yet model option-specific execution semantics such as:

- `buy_to_open`
- `sell_to_open`
- `buy_to_close`
- `sell_to_close`
- multi-leg linkage
- assignment / exercise lifecycle

## 4.2 Short support is only partial

The paper adapter can open a short when:

- the order side is `sell`
- there is no active long
- `allow_short=True`

It can also flip from long to short on an oversized sell.

But the short lifecycle is not closed.

The clearest proof is that buying against an existing short still errors through a long-only path.

That means the current system can represent some short openings, but cannot yet safely handle the full short lifecycle needed for autonomous operation.

## 4.3 Options are not truly implemented

Missing pieces include:

- canonical option contract identity
- underlying, expiry, strike, right, style, multiplier
- options chain ingest and contract selection
- leg structure for spreads and rolls
- order intent semantics by leg
- assignment and exercise handling
- expiration handling
- premium and multiplier-aware PnL
- Greeks and options-specific risk controls

The current sync path also still inserts synced positions with `asset_type="equity"` in one internal path, which confirms that the current broker-truth layer is not yet multi-instrument safe.

## 4.4 Leverage and margin are not truly implemented

The current engine has generic exposure checks, but not a real leverage model.

Missing pieces include:

- initial margin
- maintenance margin
- margin call thresholds
- liquidation prevention or forced de-risk logic
- buying-power simulation by product type
- borrow availability
- borrow fee handling
- HTB / ETB distinctions
- account-mode awareness such as cash, Reg-T, or broker-specific equivalents

## 4.5 Strategy and learning layers are not yet instrument-aware enough

The strategy lab can govern idea-to-production promotion, but it is not yet connected to:

- option contract selection rules
- roll logic
- expiration rules
- leverage-specific backtests
- short borrow constraints
- product-specific promotion thresholds

So even if the strategy layer produces a promising idea, the execution and risk layers still do not have enough structure to safely carry it into autonomous trading.

## 5. Hidden Requirements That Must Be Treated As First-Class

To satisfy the owner's real target, the system must additionally support:

1. Canonical instrument identity
   - equity, ETF, option, inverse/levered ETF, future-ready extension

2. Broker capability matrix
   - what each broker/account mode supports in paper and live
   - stocks
   - options
   - multi-leg options
   - margin
   - shorting
   - cancel/replace/sync parity

3. Instrument-aware risk engine
   - different limits for equities, options, and leveraged products
   - gross, net, delta, premium, and margin-aware controls

4. Full short lifecycle
   - open short
   - add to short
   - partial cover
   - full cover
   - borrow availability and borrow fee handling

5. Full options lifecycle
   - chain ingest
   - contract normalization
   - level-eligibility checks
   - entry and exit semantics
   - assignment / exercise / expiration events
   - roll and close workflows

6. Paper/live parity by product
   - paper trading must simulate the same product semantics that live trading depends on

7. Dashboard and Discord visibility by product
   - exposure by product class
   - margin pressure
   - expiring options
   - short borrow alerts
   - broker capability mismatches

8. Product-aware safe degradation
   - broker outage, stale option chains, assignment events, missing borrow status, and margin stress must trigger bounded behavior rather than silent drift

## 6. Official Broker Capability Signals

The architecture should remain broker-abstract, but the current official docs confirm that real broker APIs already expose many of the features the system will need.

### 6.1 Alpaca

Official docs indicate:

- options trading support
- options levels
- API exercise support
- option positions and activities
- multi-leg options orders with leg-level position intent
- margin and short-selling support for eligible equities
- daily borrow-status considerations and ETB / HTB distinctions

Implication:

- Alpaca is a realistic first live-broker candidate for equities + options + equity short/margin, but the system must model broker-specific restrictions instead of assuming generic behavior.

### 6.2 Tradier

Official docs indicate:

- equity orders
- options orders
- multileg option orders
- combo orders
- sandbox trading API
- balances exposing option buying power, stock buying power, and short stock values

Implication:

- Tradier is also a realistic first live-broker candidate and is especially attractive because the docs expose account and multileg primitives clearly.

### 6.3 Interactive Brokers

Official docs indicate:

- broad instrument coverage
- option chain APIs
- option exercise APIs
- combo order support
- short-entry behavior through ordinary sell orders in general account types
- margin preview and account summary fields for buying power and margin requirements

Implication:

- IBKR is the broadest long-term expansion path, but it is also the heaviest operational integration path and should not be the first productization blocker unless its extra market coverage is required immediately.

### 6.4 tastytrade

Official docs indicate:

- option chains
- balances with derivative buying power and maintenance requirements
- complex orders
- order dry run
- futures and futures-option product surfaces

Implication:

- tastytrade is a strong derivatives-oriented reference and a good future expansion path, especially if the system later grows beyond equities and equity options.

## 7. Recommended Architectural Decision

The architecture decision should now be explicit:

- Keep the current single-writer core plus elastic work-plane design.
- Keep the `2 VPS asymmetrical` production target.
- Keep Discord as the primary owner interaction surface.
- Keep Codex-centered execution.
- Do not deploy the first real VPS production stack until the trading kernel is truly multi-instrument aware.

The stable architecture is:

```text
Discord owner surface
    ->
authoritative control plane
    ->
authoritative runtime database
    ->
instrument-aware execution and risk kernel
    ->
one live broker authority

separate research / Codex / browser worker plane
```

What must not change:

- one runtime source of truth
- one final promotion authority
- one live broker write authority
- research workers without broker secrets
- debate before important decisions, not before every trivial action

## 8. Pre-VPS Completion Stages

The first VPS deployment should only happen after all of the following stages are complete.

### Stage P1: Instrument And Broker Capability Model

Build:

- canonical instrument model
- option contract model
- broker capability registry
- account mode registry
- position and order semantics by product type

Done when:

- the domain can accurately represent equities, options, short exposure, and leveraged account constraints
- the system can reject impossible actions before any broker call is made

### Stage P2: Multi-Instrument Paper Execution Closure

Build:

- full long lifecycle
- full short lifecycle
- option open/close lifecycle
- multi-leg order representation
- option expiration / assignment / exercise simulation
- leverage and margin simulation

Done when:

- paper trading can faithfully simulate the live logic the system depends on
- no product path falls back to equity-only assumptions

### Stage P3: Instrument-Aware Risk Engine

Build:

- product-specific risk rules
- buying-power and margin checks
- concentration and correlation controls
- option expiry and assignment alerts
- short-borrow and locate-aware gating
- portfolio sleeve attribution

Done when:

- every order path is checked against product-aware capital and risk rules
- dashboard and Discord can explain why a trade is blocked

### Stage P4: First Real Broker Closure

Build:

- one production-grade broker adapter
- authenticated sync loop
- restart recovery
- cancel / replace / reconcile parity
- broker event normalization
- broker capability tests in paper and live-safe modes

Done when:

- broker truth can safely recover after restart
- order and position state remain consistent after network or process interruption

### Stage P5: Strategy And Data Pipeline Instrument Awareness

Build:

- instrument-aware strategy specs
- option chain selection inputs
- roll rules
- expiry rules
- product-aware backtest inputs
- paper-to-live promotion thresholds by product class

Done when:

- strategy promotion depends on the same product realities that live execution will face

### Stage P6: Owner Control And Visibility Closure

Build:

- Discord operator allowlists and pairing
- richer Chinese-first owner flows
- dashboard panels for product-level exposure, margin pressure, option expiries, and short alerts
- safe-mode and kill-switch owner actions from Discord

Done when:

- the owner can understand and control the real trading surface without SSH-first operations

### Stage P7: Governed Auto-Evolution Closure

Build:

- improvement goals
- eval scorecards
- shadow and canary promotion
- objective-drift review
- rollback and freeze controls

Done when:

- the system can strengthen itself without directly mutating live trading behavior outside governed promotion

### Stage P8: VPS Productization And Recovery

Build:

- production compose and systemd shape for the 2-VPS topology
- secrets layout including Codex-compatible relay settings
- backups
- restore drill
- upgrade runbook
- break-glass runbook
- owner-facing deployment checks

Done when:

- a fresh VPS deployment is repeatable
- restore has been exercised
- safe mode works
- deployment no longer depends on a developer sitting in the shell

## 9. Deployment-Blocking Checklist

The system is not ready for the target VPS deployment if any of these are still false:

- options contracts are first-class objects
- short and cover flows are fully supported
- margin and leverage checks are real rather than generic
- paper and live semantics match by product
- at least one real broker adapter is fully closed
- dashboard and Discord surface product-aware risk
- owner unsafe actions are gated and auditable
- auto-evolution cannot bypass review and rollback
- backup and restore are tested

## 10. Practical Recommendation

The correct next move is not VPS deployment yet.

The correct next move is to finish the multi-instrument trading closure first, because that is now the biggest gap between the current system and the owner's actual target.

In plain language:

- the current system is already a strong governed shell
- but it still does not yet have the product-aware trading core your final system requires
- that gap must be closed before the first serious VPS deployment

## 11. Sources

- Alpaca options trading: https://docs.alpaca.markets/docs/options-trading
- Alpaca options multi-leg trading: https://docs.alpaca.markets/docs/options-level-3-trading
- Alpaca margin and short selling: https://docs.alpaca.markets/docs/margin-and-short-selling
- Tradier trading guide: https://docs.tradier.com/docs/trading
- Tradier balances: https://docs.tradier.com/docs/balances
- Interactive Brokers API options: https://interactivebrokers.github.io/tws-api/options.html
- Interactive Brokers order reference: https://interactivebrokers.github.io/tws-api/classIBApi_1_1Order.html
- Interactive Brokers margin preview: https://interactivebrokers.github.io/tws-api/margin.html
- Interactive Brokers account summary: https://interactivebrokers.github.io/tws-api/account_summary.html
- tastytrade basic API usage: https://developer.tastytrade.com/basic-api-usage/
- tastytrade API overview: https://developer.tastytrade.com/api-overview/

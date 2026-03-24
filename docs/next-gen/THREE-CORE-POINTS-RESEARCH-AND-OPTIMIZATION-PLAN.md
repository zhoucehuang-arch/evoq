# Three Core Points Research And Optimization Plan

## 1. Purpose

This document records a deeper research and planning pass for the owner's three core points:

1. how to learn from `DeepEar` and `nofx` to improve the current product
2. how to support US equities, US options, and China A-shares with clear separation
3. how to make the system more quantitative while still exploiting the real strengths of LLMs

This document now includes a real `gstack` review pass, not just a `gstack-style` framing.

The review was rerun against the current repo using the `gstack` workflow family:

- `/plan-ceo-review`
- `/plan-eng-review`
- `/plan-design-review`

The review proceeded in standard mode because:

- no prior branch design doc was found under the local `gstack` project cache
- the repository currently has no `CLAUDE.md`
- the repository currently has no `TODOS.md`
- the repository currently has no `DESIGN.md`

That absence is itself treated as a product and planning finding below.

This is therefore a `gstack` review pass with:

- multi-angle
- evidence-driven
- explicit about trade-offs
- focused on what should change in the current repository, not on abstract theory alone

## 2. Review Method

This pass used four inputs:

1. direct reading of the current repository
2. direct reading of the cloned `DeepEar` and `nofx` repositories
3. external research on market structure, broker capabilities, and hybrid quant-plus-LLM design
4. a multi-expert review lens covering:
   - product and UX
   - systems architecture
   - quant and risk
   - learning and knowledge
   - operations and deployment
   - efficiency and token cost

## 3. Executive Verdict

The current product already has the right long-term shell:

- governed state
- bounded supervisor loops
- Codex work plane
- Discord-first owner interface
- dashboard-first visibility
- broker and execution abstractions
- learning and evolution governance

The next improvements should therefore not be a restart.

They should be a directed product hardening pass around three structural upgrades:

1. `sleeve-first runtime truth`
   - US equities, US options, and China A-shares must become first-class sleeves

2. `quant-first signal mechanics`
   - the system needs a deterministic signal layer for ranking, sizing, and execution windows

3. `LLM-first meta layer`
   - LLMs should focus on research synthesis, regime understanding, challenge, governance, and evolution

## 4. Current Repo Re-Audit

### 4.1 What already exists

The current repository already includes:

- durable strategy lifecycle state
- durable execution state
- paper and real-broker execution paths
- option lifecycle scaffolding
- short and margin-aware validation paths
- learning ingest, synthesis, quarantine, and source decay
- council-style reflection loops
- evolution proposal and canary records

This means the current product is already far beyond a prompt mesh or bot demo.

### 4.2 What is still missing

Three gaps matter most for the owner's new direction:

1. `portfolio sleeve attribution`
   - the repo still explicitly treats this as incomplete

2. `first-class quant signal layer`
   - the current system has strategy lifecycle and execution governance, but not a dedicated deterministic signal engine

3. `market-specific operating models`
   - `target_market` exists, but the operating model is still not fully separated between US and China sleeves

## 5. Core Point 1: Learn From DeepEar And nofx

### 5.1 What DeepEar does better

`DeepEar` is a stronger reference for:

- source-pack style research intake
- checkpoint/resume research runs
- evidence-to-report flows
- research artifact presentation

What should be adopted:

- explicit acquisition packs by sleeve
- research artifact cards in the dashboard
- checkpointed research runs that can update prior outputs
- more visible logic-chain style evidence presentation

What should not be copied:

- using the research layer as if it were the execution kernel
- letting the report pipeline define the whole product architecture

### 5.2 What nofx does better

`nofx` is a stronger reference for:

- install and onboarding simplicity
- operator-first UX
- IM-native interaction posture
- strategy studio style visibility

What should be adopted:

- shorter onboarding path
- clearer operator mental model for strategy, broker, and trader relationships
- stronger Discord command ergonomics and dashboard entrypoints
- cleaner runtime object naming for non-technical owners

What should not be copied:

- flattening governance to chase ease-of-use
- over-centering the product around autonomous execution without durable review state

### 5.3 Initial synthesis verdict for core point 1

Product lens:

- keep the current product shell
- borrow `nofx` simplicity and `DeepEar` research presentation

Architecture lens:

- do not replace the current authority core
- extend it with better research and UX layers

Cost lens:

- copy the idea of fixed product surfaces
- do not copy more free-form agent chatter

Next design decision:

- the current repository remains the operating system
- `DeepEar` contributes to research UX and acquisition discipline
- `nofx` contributes to owner experience and onboarding

## 6. Core Point 2: US Equities, US Options, China A-Shares

### 6.1 External research findings

The US and China sleeves are not variations of the same market.

Official Shanghai Stock Exchange material shows important structural constraints for A-shares:

- Main Board A-shares trade in 100-share lots
- A-shares have a 10% daily price limit, with 5% for risk-warning stocks
- STAR Market has a 20% limit and different order-size rules

These details materially affect:

- turnover assumptions
- position sizing
- stop logic
- execution logic
- alpha decay

China programmatic execution also differs materially from the cleaner US broker-API path.

Official XtQuant documentation states:

- XtQuant is derived from MiniQMT
- the MiniQMT client must be running before using XtQuant

That means:

- China live trading should not be treated as the same deployment shape as Alpaca-style US API trading

### 6.2 US options findings

Official broker documentation shows that the US options path is feasible but broker-specific.

Alpaca documentation confirms:

- level-based options permissions
- option chain access
- API exercise and DNE control
- automatic exercise and assignment behavior
- multi-leg level 3 support

IBKR documentation confirms:

- flexible contract definition
- combo-leg support for spreads
- broad instrument coverage

That means the product should:

- keep Alpaca as the first practical US live path
- keep IBKR as the long-term expansion path
- model broker capability truth explicitly instead of pretending options are generic

### 6.3 A-share data findings

For free and no-paid-API research ingestion, the strongest China data path is:

- `AKShare` first for market, factor, announcement-adjacent, and option data aggregation
- `Tushare` as a secondary and optional structured source

AKShare already exposes:

- A-share and derivative data
- China ETF and index option datasets
- SSE/SZSE/CFFEX option-related interfaces

Tushare documents broad A-share coverage too, but it is better treated as optional because it is a managed platform rather than the most frictionless default.

### 6.4 Product implication

The correct product shape is:

- `us_equities`
- `us_options`
- `cn_equities`

The correct deployment shape is:

- one product supports all three sleeves
- one runtime deployment selects one market mode
- `us` mode activates `us_equities` and `us_options`
- `cn` mode activates `cn_equities`

Each sleeve gets its own:

- market calendar
- timezone
- broker capability matrix
- source pack
- quant model pack
- promotion thresholds
- capital and risk budget

China live trading should be behind a bounded execution adapter edge.

The single-VPS-first product can still remain true because:

- research
- learning
- dashboard
- Discord
- US live execution

can all remain on one Linux VPS first.

China live execution can then be attached later through a broker-specific edge without redesigning the whole Core.

### 6.5 Initial synthesis verdict for core point 2

Product lens:

- separate sleeves, same product shell

Systems lens:

- one Core, one runtime DB, one Discord shell
- different execution and data adapters per sleeve

Quant lens:

- different alpha families for US and China
- no forced reuse of one strategy design across both markets

Ops lens:

- single VPS first is valid for the product shell
- China live execution is a special edge case, not a reason to redesign Core

## 7. Core Point 3: More Quantitative, While Exploiting LLM Strengths

### 7.1 The most important research conclusion

The best current evidence does not support using a general LLM as the raw low-latency predictor.

Evidence pointing against naive LLM-first prediction:

- `The Wall Street Neophyte` found that zero-shot ChatGPT underperformed both state-of-the-art methods and simple price-feature baselines for stock movement prediction.

Evidence pointing for targeted hybrid usage:

- `Sentiment trading with large language models` found that LLM-based news sentiment can be associated with subsequent daily stock returns and can support long-short portfolio construction.
- `AlphaFin` argues that ML-only systems lack reasons and that LLMs need retrieval grounding because otherwise they hallucinate and fall behind real-time knowledge.
- `The New Quant` survey argues for retrieval-first prompting, tool-verified numerics, and production evaluation that includes latency, capacity, and cost.

The correct lesson is:

- do not make the LLM the tick-to-trade engine
- do make the LLM the text and context engine

### 7.2 What strategy research says about "high win rate and high return"

The term `high win rate` is dangerous if treated as the primary target.

Several well-known strategy families can produce attractive long-run characteristics, but they do so with very different payoff shapes:

1. trend / time-series momentum
   - robust across markets over long history
   - can have lower hit rates but strong positive convexity in major trends

2. value plus momentum combinations
   - often improve diversification and risk-adjusted returns versus either one alone

3. event-driven / PEAD style strategies
   - rely on delayed price adjustment after information shocks

4. option-volatility risk premium strategies
   - often show attractive average returns or win-rate characteristics
   - but can hide crash and tail-risk exposure

5. options-flow or option-imbalance informed strategies
   - can add information about spot returns
   - but should be treated as one signal family, not a full strategy by itself

This means the product should optimize for:

- expectancy
- Sharpe
- drawdown
- turnover efficiency
- slippage robustness
- live-paper consistency

not raw win rate alone.

### 7.3 Quant families that best match this product

For `us_equities`, the best-fit quant families are:

- cross-sectional factor ranking
- event-driven earnings and news reaction
- medium-horizon trend and momentum
- sector and regime rotation
- options-flow-informed equity overlays

For `us_options`, the best-fit quant families are:

- volatility risk premium sleeves with strict risk limits
- covered-call or overwrite variants with explicit exposure decomposition
- event-volatility selection around earnings or macro events
- roll and expiry management models
- spread selection and strike-selection models

For `cn_equities`, the best-fit quant families are:

- lower-turnover factor timing
- institutional-ownership-aware momentum variants
- factor momentum rather than naive stock momentum
- liquidity- and limit-aware event strategies
- sector and policy-driven ranking sleeves

### 7.4 What the LLM should do in this system

The LLM should own:

- research synthesis
- regime detection from heterogeneous evidence
- mapping external events to factor and sector implications
- anomaly explanation
- strategy proposal drafting
- counterargument generation
- incident diagnosis
- evolution proposal generation

The LLM should not own:

- primary ranking of thousands of names every minute
- low-latency order timing
- exact sizing math
- backtest arithmetic
- broker-state truth

### 7.5 The target hybrid architecture

The target architecture is:

```text
data and events
  ->
deterministic feature engine
  ->
quant ranking, filtering, and sizing
  ->
candidate trades and execution windows
  ->
LLM challenge and context layer
  ->
governed strategy decision
  ->
execution
```

The LLM enriches and vetoes.

The quant layer proposes and measures.

### 7.6 Initial synthesis verdict for core point 3

Quant lens:

- move candidate generation, ranking, and sizing into a dedicated quant engine

LLM lens:

- use retrieval-grounded, tool-verified LLM reasoning for text and regime interpretation

Risk lens:

- do not use `high win rate` as the main objective
- use tail-risk-aware portfolio metrics

Cost lens:

- let cheap deterministic models screen first
- let expensive LLM councils only evaluate narrowed candidate sets or important governance decisions

## 8. Concrete Product Changes

### 8.1 P0

- add `portfolio_sleeve` as a durable runtime object across strategy, learning, execution, dashboard, and approvals
- add per-sleeve market-session state
- add sleeve-level source packs
- add sleeve-level allocation policies and symbol ownership

### 8.2 P1

- add a dedicated quant signal service
- start with daily and hourly deterministic models, not ultra-low-latency paths
- persist candidate rankings, factor exposures, sizing inputs, and execution windows

### 8.3 P2

- add a research-to-quant bridge
- LLMs produce structured event and regime features that the quant layer can consume
- do not leave this bridge as unstructured prompt residue

### 8.4 P3

- formalize strategy councils so they trigger only for:
  - new strategy proposals
  - paper to live promotion
  - live degradation
  - major reallocation
  - evolution proposals

### 8.5 P4

- improve onboarding using a shorter `nofx`-style setup path
- improve research artifact visibility using a `DeepEar`-style evidence view

## 9. Detailed Next-Step Plan

### Stage 1: Sleeve Runtime Closure

Build:

- `portfolio_sleeve` model
- sleeve-aware strategy specs
- sleeve-aware allocation policies
- sleeve-aware execution readiness
- sleeve-aware dashboard summaries

Acceptance:

- a US strategy and a China strategy cannot collide in ownership or capital policy silently
- dashboard and Discord can display sleeve state explicitly

### Stage 2: Quant Signal Layer

Build:

- instrument universe builders
- factor calculators
- event feature calculators
- candidate ranking tables
- sizing and turnover constraints

Acceptance:

- candidate generation can run without LLMs
- output is replayable and testable

### Stage 3: LLM Research And Challenge Layer

Build:

- structured event extraction
- regime summaries
- evidence packets for councils
- explicit contradiction and risk notes

Acceptance:

- LLM output is grounded in citations and can be consumed by downstream deterministic logic

### Stage 4: US Options Quant Kernel

Build:

- options chain selection
- strike and tenor policies
- covered-call / spread / VRP sleeves
- roll rules
- expiry and assignment-aware risk

Acceptance:

- option strategy logic is separated from equity logic
- tail-risk and margin controls are visible in runtime state

### Stage 5: China Research And Paper Sleeve

Build:

- AKShare-first China source pack
- China calendar and session rules
- China factor and event models
- paper-only China execution simulation

Acceptance:

- China sleeve can run research, ranking, and paper validation honestly on one Linux VPS

### Stage 6: Council And Governance Optimization

Build:

- trigger conditions
- cost budgets
- structured dissent records
- promotion review packets

Acceptance:

- councils only run where they add measurable decision quality

## 10. Evaluation Framework

The system should be evaluated at three levels.

### 10.1 Signal level

- information coefficient
- rank IC decay
- hit ratio by horizon
- turnover
- concentration

### 10.2 Portfolio level

- CAGR
- Sharpe
- Sortino
- Calmar
- max drawdown
- win/loss distribution
- tail losses
- slippage sensitivity

### 10.3 System level

- token cost per approved decision
- latency from signal to order
- live-paper divergence
- research artifact usefulness
- council value-add versus cost
- false-positive incident rate

## 11. Iteration Rules

This optimization should proceed with explicit iteration gates:

1. Research gate
   - collect evidence and define the change

2. Design gate
   - write exact contracts and failure modes

3. Paper gate
   - validate in backtest and paper

4. Governance gate
   - confirm the change does not create uncontrolled drift

5. Product gate
   - confirm the owner can still operate it simply

## 12. Final Decision

The correct next move is not to broaden the system randomly.

It is to harden the current repository around a very specific target shape:

- one governed product shell
- three first-class sleeves: `us_equities`, `us_options`, `cn_equities`
- a new deterministic quant signal layer
- a retrieval-grounded LLM research and challenge layer
- selective multi-agent councils at high-value decision points
- simpler onboarding and clearer operator UX inspired by `nofx`
- stronger research artifact and evidence presentation inspired by `DeepEar`

## 13. Source Notes

External sources used in this pass included:

- AQR research on time-series momentum, value plus momentum, factor momentum, covered calls, collars, and volatility risk premium
- arXiv papers on FinGPT, AlphaFin, financial LLM surveys, zero-shot LLM stock prediction, LLM sentiment trading, and option-flow predictability
- official Alpaca options documentation
- official Interactive Brokers TWS API documentation
- official Shanghai Stock Exchange market-mechanism and options-rule materials
- official XtQuant / MiniQMT documentation
- AKShare and Tushare documentation

Representative links:

- https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum
- https://www.aqr.com/insights/research/journal-article/a-century-of-evidence-on-trend-following-investing
- https://vintagequants.com/wp-content/uploads/2024/09/Asness-VME_presentation.pdf
- https://www.aqr.com/insights/research/working-paper/factor-momentum-everywhere
- https://www.aqr.com/Insights/Research/White-Papers/Understanding-the-Volatility-Risk-Premium
- https://www.aqr.com/insights/research/journal-article/risk-and-return-of-equity-index-collar-strategies
- https://www.aqr.com/Insights/Research/Journal-Article/Covered-Calls-Uncovered
- https://arxiv.org/abs/2304.05351
- https://arxiv.org/abs/2306.06031
- https://arxiv.org/abs/2403.12582
- https://arxiv.org/abs/2412.19245
- https://arxiv.org/abs/2201.09319
- https://arxiv.org/abs/2510.05533
- https://docs.alpaca.markets/docs/options-trading-overview
- https://docs.alpaca.markets/docs/options-level-3-trading
- https://docs.alpaca.markets/v1.1/changelog/multi-leg-level-3-options-are-now-available-in-trading-api-and-dashboard
- https://interactivebrokers.github.io/tws-api/contracts.html
- https://interactivebrokers.github.io/tws-api/spread_contracts.html
- https://english.sse.com.cn/start/trading/mechanism/
- https://english.sse.com.cn/start/sserules/options/c/10115073/files/bf2f24d1fffe49b089d42c2c18276b83.pdf
- https://dict.thinktrader.net/nativeApi/start_now.html
- https://akshare.akfamily.xyz/data/option/option.html
- https://www.tushare.pro/document/2

## 14. GSTACK System Audit

The `gstack` rerun produced the following planning context before review:

- branch: `main`
- effective base branch: `main`
- no stash entries were present
- recent repo work is concentrated in deployment, dashboard, docs, and state/read-model surfaces
- no branch-scoped `gstack` design doc or CEO handoff note was found
- no `CLAUDE.md`, `TODOS.md`, or `DESIGN.md` exists at repo root

Why that matters:

- missing `CLAUDE.md` means engineering conventions and test posture are not expressed in one authoritative place
- missing `TODOS.md` means intentional deferrals are too easy to lose
- missing `DESIGN.md` means dashboard and onboarding design decisions are still under-specified

The repo already contains strong architectural intent, but `gstack` would classify the current planning posture as:

- architecture stronger than product specification
- product specification stronger than design specification
- design specification stronger than operator onboarding simplicity

## 15. GSTACK CEO Review

### 15.1 Review mode

This rerun is best classified as `SELECTIVE EXPANSION`.

Reason:

- the owner wants the current system hardened, not replaced
- the owner also explicitly wants hidden requirements surfaced rather than ignored
- therefore the correct CEO posture is: hold the core direction, but add missing product-critical scope where omission would make the system weaker or less governable

### 15.2 Premise challenge

The right product is not:

- a prompt mesh
- a pure quant engine
- a chatbot with broker hooks

The right product is:

- a governed autonomous investment operating system

That framing remains correct and should not change.

The main CEO-level correction is this:

- the plan previously focused on `market coverage` and `signal architecture`
- it did not state strongly enough that `operator governability`, `memory durability`, and `cost discipline` are co-equal product requirements

### 15.3 Current state -> plan -> 12-month ideal

```text
CURRENT STATE
  governed shell + learning base + execution governance
  but missing sleeve runtime truth, explicit quant kernel,
  and fully productized owner simplicity

        ->

THIS PLAN
  formalize sleeves
  separate quant from LLM responsibilities
  improve research UX and onboarding

        ->

12-MONTH IDEAL
  one governed product shell
  three first-class sleeves
  deterministic quant candidate engine
  selective high-value councils
  evidence-rich learning and evolution loops
  single-VPS-first operator experience that still scales out cleanly
```

### 15.4 Implementation alternatives considered

#### Approach A: Governed sleeve-first hybrid core

- keep the current repository as authority core
- add first-class sleeves
- add deterministic quant signal mechanics
- keep LLMs on research, challenge, governance, and evolution

Verdict:

- recommended

#### Approach B: Replace the shell with a `DeepEar` or `nofx`-like product shell

- use one of the reference projects as the primary architecture
- backfill governance later

Verdict:

- rejected
- this would trade away the strongest part of the current product: durable governed authority

#### Approach C: Research-first autonomous super-agent with weak deterministic kernel

- treat research, debate, and reflection as the main intelligence surface
- keep quant logic thin

Verdict:

- rejected
- this would drift toward high token burn, weak replayability, and lower live-trading trust

### 15.5 CEO findings

#### Finding 1: Single-VPS-first must be treated as product scope, not deployment appendix

If single-VPS-first is only a docs promise, the product will remain psychologically "operator-hostile" for the target owner.

Implication:

- single-VPS-first onboarding and runtime posture must be a first-class design constraint

#### Finding 2: A-share live execution should not be allowed to block US first closure

The owner's target includes A-shares, but the highest-leverage product sequence is:

- US equities + US options live-capable
- China equities research + paper first
- bounded China live edge later

Implication:

- the plan should explicitly separate `China inclusion` from `China live parity`

#### Finding 3: Multi-agent quality is a feature, but unmetered councils are a tax

The product promise is better decisions through structured disagreement.

That only remains true if councils are:

- selective
- trigger-based
- budgeted
- auditable

Implication:

- token and time budgets must be part of the plan, not an afterthought

#### Finding 4: Continuous learning without explicit memory and skill contracts is incomplete

The owner's real goal is not just to gather more information.

It is to:

- retain useful knowledge durably
- promote reusable methods into skills
- avoid relearning the same lesson through repeated token spend

Implication:

- `memory plane` and `skill plane` need to be added as explicit product scope

## 16. GSTACK Engineering Review

### 16.1 Engineering verdict

The plan direction is strong, but `gstack` engineering review finds that it was still underspecified in four implementation-critical places:

1. runtime identity and ownership
2. failure modes and fallback behavior
3. test and eval closure
4. memory and skill operating contracts

### 16.2 Minimum safe architecture

```text
sources + events
  ->
acquisition packs by sleeve
  ->
feature / factor / event engine
  ->
signal tables + candidate sets
  ->
LLM challenge + governance councils
  ->
approval / promotion records
  ->
execution + reconciliation
  ->
memory promotion + skill updates
```

This is the smallest architecture that still satisfies:

- quant-first mechanics
- LLM-assisted reasoning
- governed evolution
- replayability

### 16.3 Mandatory engineering corrections

#### Correction 1: Add `memory plane` as a formal subsystem

The current plan talks about learning and evolution, but not yet as an explicit runtime contract.

The plan should formalize:

- working memory
- evidence memory
- promoted principles
- promoted skills
- decay and invalidation policy

Without this, "continuous learning" remains too narrative and not operational enough.

#### Correction 2: Add `skill plane` as a formal subsystem

The owner explicitly values learning reusable skills over paying LLM cost repeatedly.

The plan must therefore include:

- skill registry
- skill quality checks
- skill provenance
- skill deprecation / rollback
- routing policy for when a task uses a skill versus free-form LLM reasoning

#### Correction 3: Add explicit failure taxonomy

The plan needs named failure classes, not generic "degraded" language only.

At minimum:

- `SleeveCollisionError`
- `BrokerCapabilityMismatch`
- `SourcePackUnavailable`
- `EvidenceFreshnessFailure`
- `CouncilBudgetExceeded`
- `PromotionGateFailure`
- `ObjectiveDriftDetected`
- `ChinaLiveEdgeUnavailable`

Each class should specify:

- trigger condition
- fail-open or fail-closed behavior
- operator visibility surface
- recovery path

#### Correction 4: Add a test-and-eval matrix before implementation

The prior version named metrics, but `gstack` review expects a test map.

The plan should explicitly require:

- unit tests for factor, feature, sizing, and policy logic
- integration tests for sleeve routing, broker capability checks, and reconciliation
- replay tests for candidate generation
- evals for LLM regime summaries and challenge quality
- paper/live divergence checks

### 16.4 Engineering guardrails that must become explicit

- A-share paper mode is first-class and honest, not a placeholder
- China live stays behind a broker-specific edge and never becomes a hidden assumption inside Core
- councils must carry cost budgets and timeout budgets
- every sleeve owns symbol authority and capital policy
- memory promotion and skill promotion require rollback paths

## 17. GSTACK Design Review

### 17.1 UI scope assessment

This plan does have real UI scope.

It affects:

- dashboard information architecture
- Discord interaction model
- first-run onboarding posture
- operator trust and clarity during incidents, pauses, and promotions

`gstack` therefore treats a design review as applicable and necessary.

### 17.2 Initial design completeness rating

Initial rating:

- `5/10`

Why not higher:

- the plan already contains strong dashboard and Discord direction
- but it still lacks a unified design system source of truth
- and several interaction states are not yet specified concretely enough

What a `10/10` would look like:

- a `DESIGN.md`
- explicit screen hierarchy
- explicit loading / empty / error / success / partial states
- intentional responsive rules
- anti-slop design rules for the dashboard
- trust-at-a-glance signals for paper/live, freshness, and risk

### 17.3 Design classifier

The primary product surface is `APP UI`, not a marketing page.

Implication:

- calm information hierarchy
- chart-first and table-capable
- minimal chrome
- strong density discipline
- cards only when a card is truly the interaction

### 17.4 Design findings

#### Finding 1: No `DESIGN.md` exists

This is a design governance gap.

Without it:

- dashboard polish risks becoming local taste
- onboarding and dashboard may drift visually over time

Plan correction:

- add a `DESIGN.md` stage before major UI expansion

#### Finding 2: Interaction states are still under-specified

The dashboard spec is strong on content blocks, but weaker on:

- loading states
- empty research states
- stale data warning states
- incident partial recovery states
- first-run zero-data experience

Plan correction:

- add an interaction-state table for dashboard and Discord handoff flows

#### Finding 3: The product must actively avoid generic AI-dashboard drift

The intended visual direction is already strong:

- dense
- crisp
- terminal-like
- chart-first
- no generic SaaS purple

But the plan should say more clearly:

- no decorative card walls
- no feature-grid thinking
- no fake realtime feel when data is stale
- freshness, paper/live mode, and risk tier must always be visible in first-glance surfaces

#### Finding 4: First-run onboarding needs an emotional arc

The plan explains what the owner can do, but not what the owner should feel in the first session.

The target emotional sequence should be:

1. orientation
2. trust
3. control
4. confidence

Plan correction:

- first dashboard load should answer:
  - is the system alive
  - is it safe
  - is it trading
  - is it learning
  - what needs me now

## 18. Plan Corrections From GSTACK Review

The following items are now required additions to the plan.

### 18.1 Additions to product scope

- formal `memory plane`
- formal `skill plane`
- council cost and timeout budgets
- single-VPS-first onboarding as a first-class product requirement
- explicit China `research + paper first` posture before live-edge expansion
- a `DESIGN.md` stage for dashboard and onboarding consistency

### 18.2 Additions to the execution plan

Before Stage 1 implementation, add a `Stage 0` planning closure:

- write the memory contract
- write the skill contract
- write the dashboard / Discord state tables
- write the initial `DESIGN.md`
- write the failure taxonomy

Then proceed with:

1. sleeve runtime closure
2. deterministic quant signal layer
3. research-to-quant bridge
4. US options quant kernel
5. China research and paper sleeve
6. selective council governance
7. operator and onboarding hardening

### 18.3 Additions to acceptance criteria

The plan should now be treated as complete only if it closes:

- runtime truth
- quant replayability
- LLM governance quality
- memory durability
- skill reuse quality
- owner trust and operator simplicity

## 19. GSTACK Review Report

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope and product direction | 1 | DONE_WITH_CONCERNS | Product direction is right, but single-VPS-first, memory plane, skill plane, and council cost governance must be elevated into core scope. |
| Eng Review | `/plan-eng-review` | Architecture and execution closure | 1 | DONE_WITH_CONCERNS | Sleeve runtime truth and quant/LLM split are correct, but failure taxonomy, test/eval matrix, memory contract, and skill contract were under-specified. |
| Design Review | `/plan-design-review` | Dashboard, Discord, onboarding UX | 1 | DONE_WITH_CONCERNS | UI direction is strong, but the plan still lacked `DESIGN.md`, state tables, first-run trust hierarchy, and stronger anti-slop guardrails. |

**VERDICT:** PROCEED AFTER PLAN CORRECTIONS. The core direction is sound. The plan is stronger after `gstack` review, but implementation should follow the corrected plan shape above rather than the narrower pre-review version.

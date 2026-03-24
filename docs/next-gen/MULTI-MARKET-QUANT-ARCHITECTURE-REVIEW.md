# Multi-Market Quant Architecture Review

## 1. Purpose

This document closes the gap between:

- the current repository state
- the owner's expanded target scope
- the strongest ideas worth borrowing from `DeepEar` and `nofx`

The expanded target is now explicit:

- research and invest in US equities
- research and invest in China A-shares
- keep those two market sleeves separate
- support US options
- support leveraged long and short exposure for US strategies
- lean more quantitative in signal generation and execution
- still preserve the product's core strengths:
  - Discord-first control
  - dashboard-first visibility
  - governed autonomy
  - Codex-centered work execution
  - long-running learning and self-improvement

## 2. Consolidated Verdict

The current product is already stronger than both reference projects in one critical way:

- it has a more serious governance kernel than `DeepEar`
- it has a more serious long-running state model than `nofx`

But it is not yet aligned with the expanded target in four important areas:

1. `target_market` exists, but `portfolio sleeve attribution` is still not implemented.
2. The system is still too execution-kernel-centric around one market calendar and one generic market posture.
3. The quant layer is not yet explicit enough as a first-class producer of signals, sizing inputs, and execution windows.
4. The multi-agent system is governed, but not yet optimized around high-value debate points versus low-value token burn.

Short version:

- borrow `DeepEar` for acquisition, evidence flow, and research presentation
- borrow `nofx` for operator experience, onboarding, and product shell
- keep the current repository as the authority and governance core
- do not turn the current system into either reference project

## 3. What To Borrow From DeepEar

`DeepEar` is the better reference for the research side of the system.

The parts worth copying conceptually are:

1. Source-aware acquisition pipelines
   - It treats research collection as a pipeline with distinct tools for search, news, price data, extraction, checkpointing, and reporting.
   - That is stronger than letting each agent rediscover the acquisition method by prompt.

2. Event-to-report flow
   - It is good at turning raw external noise into structured outputs, logic chains, and reviewable artifacts.
   - This fits the current product's learning and dashboard surfaces very well.

3. Checkpoint and resume behavior
   - Research runs can be resumed and updated rather than restarted from zero.
   - This matters for long-running VPS operation and token efficiency.

4. Dashboard-visible research artifacts
   - DeepEar is good at making research output legible as a product, not just a log file.
   - The current dashboard should absorb more of that presentation quality for learning, insight, and strategy evidence review.

## 4. What To Borrow From nofx

`nofx` is the better reference for product shell and operator ergonomics.

The parts worth borrowing conceptually are:

1. One-command onboarding posture
   - The install and first-run path is opinionated and short.
   - This is still better than the current project's deploy story, even though the current project is safer.

2. IM-native operator surface
   - `nofx` treats chat control as a product surface, not as a debug tool.
   - That matches the current Discord-first target very closely.

3. Strategy-studio style UX
   - It gives the operator clearer mental models for how strategy, trader, market, and execution fit together.
   - The current product should expose sleeve, strategy, broker, and risk relationships more explicitly in Discord and the dashboard.

4. Route-registry thinking
   - `nofx` is strong at exposing structured operator actions cleanly through an API and chat layer.
   - The current product should keep growing that model instead of relying on increasingly broad free-form chat intents.

## 5. New Architecture Decisions

### 5.1 Introduce first-class market sleeves

The system should formalize these sleeves:

- `us_equities`
- `us_options`
- `cn_equities`

Notably absent on purpose:

- `cn_options`
- `cn_futures`
- `crypto`

Those can exist later, but they should not be mixed into the first production closure.

Each sleeve must own its own:

- market calendar
- timezone
- broker capability profile
- tradable instrument universe
- strategy promotion thresholds
- risk budgets
- acquisition source pack
- dashboard segmentation

The current repo already blocks unsafe cross-strategy netting until sleeve attribution exists. That is the correct direction. The missing step is to make sleeve identity durable across:

- hypotheses
- strategy specs
- backtests
- paper runs
- allocation policies
- account snapshots
- positions
- orders
- learning artifacts
- dashboard read models

### 5.2 Add deployment-level market mode

One product can support both US and China, but one runtime deployment should choose one market mode:

- `QE_DEPLOYMENT_MARKET_MODE=us`
  - activates `us_equities` and `us_options`
- `QE_DEPLOYMENT_MARKET_MODE=cn`
  - activates `cn_equities`

This is the cleanest product contract because it keeps:

- deploy UX simpler
- resource governance simpler
- broker truth simpler
- dashboard segmentation clearer
- incident diagnosis easier

This is also the honest market split:

- `US` mode may decide between equities, options, or mixed sleeves
- `CN` mode should not pretend to share the US live-execution path

### 5.3 Separate market-specific operating models

The system should not treat US and A-share workflows as one big market.

They differ materially in:

- session structure
- holiday calendars
- data-source availability
- broker and execution APIs
- shorting and leverage mechanics
- options availability
- liquidity and microstructure behavior
- acceptable holding periods

Required decision:

- US and China sleeves share one product shell and one governance core
- they do not share one alpha loop, one calendar, one execution policy, or one broker abstraction shortcut

### 5.4 Keep US options only inside the US sleeve

US options should stay inside `us_options`, tightly coupled to `us_equities` by underlying symbol and sleeve lineage.

That sleeve needs its own:

- chain ingestion
- contract selection rules
- spread templates
- roll rules
- expiry lifecycle
- assignment and exercise handling
- delta and premium-aware risk rules
- broker capability checks

The current repo already contains meaningful option lifecycle and multi-leg scaffolding. The design task now is to stop treating it as a generic extension and instead bind it to a sleeve-specific operating model.

## 6. Quant Versus LLM Responsibilities

This is the most important architecture clarification.

The product should become `quant-first in signal mechanics` and `LLM-first in research and meta-reasoning`.

### 6.1 What the quant layer should own

The quant layer should be the default producer for:

- universe construction
- factor and feature calculation
- screening and ranking
- event-study scoring
- options chain filters
- volatility and surface-derived heuristics
- position sizing inputs
- rebalance windows
- execution scheduling
- slippage and capital-consumption estimates
- correlation and exposure budgeting

This layer should be deterministic, replayable, and cheap.

### 6.2 What the LLM layer should own

The LLM layer should own:

- research synthesis across heterogeneous sources
- regime labeling and narrative interpretation
- hypothesis generation
- anomaly explanation
- strategy proposal writing
- cross-source contradiction detection
- multi-agent challenge and refinement
- incident diagnosis
- self-improvement proposals
- operator communication

This layer should not be the low-latency tick-to-trade engine.

### 6.3 Practical operating rule

The product should not ask an LLM to behave like a high-frequency signal calculator.

Instead:

```text
quant engines produce:
  features -> scores -> candidate trades -> execution windows

LLM systems produce:
  context -> regime interpretation -> challenge -> approval evidence -> evolution proposals
```

That split is the main way to preserve both quality and efficiency.

## 7. Multi-Agent Design For Better Decisions

The owner's goal is not one-shot answers. It is higher-quality decisions through structured disagreement.

That goal is valid, but only if debate is used at the right leverage points.

The system should not run a large council for every routine action.

It should run councils mainly for:

- new strategy proposals
- promotion from backtest to paper
- promotion from paper to live
- major allocation changes
- incident triage
- evolution proposals
- objective-drift reviews
- market-regime changes that materially alter exposure

Recommended council split:

1. `Research council`
   - macro / news interpreter
   - sector and fundamentals interpreter
   - source-quality skeptic

2. `Strategy council`
   - quant designer
   - execution engineer
   - regime skeptic

3. `Risk council`
   - portfolio risk reviewer
   - broker and operational risk reviewer
   - mission and governance reviewer

Each council should emit structured outputs:

- claims
- objections
- unresolved risks
- required follow-up tests
- final recommendation

This preserves the benefit of multi-agent thinking without paying one-shot persona tax on every loop.

## 8. Acquisition And Learning Changes

The current repository is already moving in the right direction with:

- official APIs
- hosted search
- self-hosted search/scrape fallback
- feed routing
- skill-based acquisition
- Playwright fallback

That is the right backbone.

The upgraded rule set should be:

1. Official APIs first.
2. Codex-compatible hosted web search second.
3. Self-hosted SearXNG-style fallback third.
4. RSS and RSSHub before browser automation.
5. Playwright only when previous layers fail or anti-bot friction blocks retrieval.

For `cn_equities`, the system should emphasize source packs that are naturally more local and structured, such as:

- exchange announcements
- regulator notices
- index and industry publications
- company disclosures
- AkShare-fed market and fundamental datasets

For `us_equities` and `us_options`, the system should emphasize:

- broker truth
- company filings
- official calendars and corporate actions
- market data providers
- earnings and options-chain context
- web research only when needed for edge cases, thematic work, or narrative context

For social-media acquisition:

- treat it as opportunistic, not guaranteed
- use browser fallback episodically, not as a permanent firehose
- quarantine low-trust sources aggressively before promotion into memory

## 9. A-Share Reality Constraint

The product should support `cn_equities` research immediately.

But live A-share execution should be designed through a hard adapter boundary rather than promised as a simple Linux-VPS-native path.

Reason:

- many practical A-share programmatic trading paths depend on broker-specific desktop clients, gateway software, or local trader terminals
- that operating model differs materially from the cleaner US API-broker path

So the right product decision is:

- make one Linux VPS the first-class product shell
- support `cn_equities` research, learning, ranking, and paper execution there
- keep the China live execution adapter behind a separate edge boundary so later broker-specific requirements do not force a redesign of the whole system

That preserves the owner's single-VPS-first goal without lying about broker reality.

## 10. Concrete Product Changes To Make

### P0

- add a durable `portfolio_sleeve` identity across strategy, execution, dashboard, and learning objects
- move from one default market calendar posture to per-sleeve session state
- expose sleeve-level health, risk, and capital summaries in the dashboard and Discord

### P1

- add sleeve-specific source packs and acquisition policies
- add `cn_equities` research pack and `us_options` research pack
- add source-trust scoring by sleeve

### P2

- add a first-class quant signal service layer that produces ranked candidate trades and sizing inputs
- keep LLMs downstream for synthesis, challenge, and governance rather than raw signal generation

### P3

- formalize councils with explicit trigger conditions, stop rules, and cost budgets
- store structured objections and dissent as durable evidence rather than chat residue

### P4

- improve onboarding and deployment UX by borrowing the simplicity standard from `nofx`
- keep the current safety posture, but cut steps and surface clearer owner guidance

## 11. Acceptance Criteria For This Direction

The architecture should only be considered aligned when all of the following are true:

1. US equities, US options, and China equities are separate sleeves in runtime truth, not just in prose.
2. The quant layer is the default engine for candidate generation, ranking, and sizing.
3. LLMs are used mainly for synthesis, challenge, governance, and evolution.
4. Councils are invoked at high-value decision points rather than everywhere.
5. The one-VPS product path can run the full control plane plus US live capability without changing the operator experience.
6. China live execution can be added later through a bounded adapter edge without redesigning the Core.

## 12. Final Judgment

The best move is not to replace the current repository with `DeepEar` or `nofx`.

The best move is:

- keep the current project as the authoritative operating system
- absorb `DeepEar` into the research and artifact experience
- absorb `nofx` into onboarding and operator UX
- push the trading architecture toward sleeve-first, quant-first execution
- keep LLMs where they have real advantage: synthesis, challenge, interpretation, and governed evolution

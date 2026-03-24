# GSTACK Full Product Re-Review

## 1. Purpose

This document is the rerun the owner explicitly requested through the `gstack` workflow family.

It re-reviews five things together instead of treating them as separate tracks:

1. the three core points
2. the current product
3. the dashboard
4. the GitHub page and repository presentation
5. the deployment experience

It also closes one new product decision that must now be treated as canonical:

- the product supports both `US` and `CN`
- a single deployment chooses one market mode
- `US` mode must support both US equities and US options
- `CN` mode is the A-share product surface

## 1.1 2026-03-24 Follow-Through Update

The repo now closes several issues that were open when this review document was first written:

- `XSHG` and `XSHE` market-session synthesis now supports the A-share trading day structure, including the midday break.
- acquisition guidance and supervisor prompts now become deployment-market-aware, so a `cn` deployment does not keep proposing US-options or Alpaca-shaped paths.
- dashboard overview, trading, and system surfaces now expose `deployment market mode`, `active sleeves`, and the active market calendar.
- the dashboard landing page now treats `single VPS first` as the operator default, with two-node scale-out presented as the later path.

The remaining blockers listed below should now be read after those fixes, not instead of them.

## 1.2 2026-03-24 Whole-Product Follow-Through

This follow-through pass rechecked the live local dashboard shell and the owner-entry docs again, not just the backend slices.

Additional closures from this pass:

- all six dashboard routes returned `200` in a fresh local production start: `/`, `/trading`, `/evolution`, `/learning`, `/system`, and `/incidents`
- the top-level VPS runbook now matches the repo's actual `single-VPS first, Core + Worker later` product posture
- overview-level memory reporting is now more honest: repo-backed promoted memory is shown separately from runtime learning-mesh document and insight counts
- repository delivery status was refreshed to the current verification date and test count

## 2. Review Method

This rerun combines:

- `gstack` framing plus the `plan-ceo-review`, `plan-eng-review`, and `plan-design-review` lenses already used in the repo
- direct repo review of the current implementation and docs
- direct dashboard evidence from local screenshots:
  - `.tmp-dashboard-overview-pw.png`
  - `.tmp-dashboard-mobile-pw.png`
- external research on GitHub presentation, market structure, broker capability, free acquisition architecture, and quant-plus-LLM design

## 3. External Research Anchors

The rerun used the following sources as decision anchors:

- GitHub README guidance:
  - GitHub says the README is often the first thing visitors see and should explain what the project does, why it is useful, how to get started, where to get help, and who maintains it.
  - Source: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes
- GitHub healthy-contribution baseline:
  - GitHub explicitly ties mature project presentation to contribution guidelines, license, support resources, and community health.
  - Source: https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions
- GitHub social preview:
  - GitHub recommends adding a repository social preview image for stronger project identity.
  - Source: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview
- Alpaca options support:
  - Alpaca documents options levels, exercise handling, and separate level-3 multi-leg support.
  - Sources:
    - https://docs.alpaca.markets/docs/options-trading-overview
    - https://docs.alpaca.markets/docs/options-level-3-trading
- SSE market structure:
  - SSE documents 100-share lot sizes for stock buys, 10% daily price limits, 5% for risk-warning stocks, and 20% for STAR auction trading.
  - Source: https://english.sse.com.cn/start/trading/mechanism/
- XtQuant / MiniQMT:
  - XtQuant is built around MiniQMT and requires the MiniQMT client to be running before use.
  - Source: https://dict.thinktrader.net/nativeApi/start_now.html
- AKShare:
  - AKShare exposes option-data coverage including index, ETF, and commodity-futures option data.
  - Source: https://akshare.akfamily.xyz/data/option/option.html
- SearXNG:
  - SearXNG explicitly documents bot protection, rate limiting, and limiter setup to reduce upstream CAPTCHA and blocking risk.
  - Source: https://docs.searxng.org/admin/searx.limiter
- Playwright:
  - Playwright supports connecting to an existing browser over a websocket endpoint, which fits a governed remote-browser fallback.
  - Source: https://playwright.dev/docs/api/class-browsertype
- Codex cloud internet access:
  - OpenAI documents that internet access should be environment-scoped, allowlisted, and limited to necessary domains and methods.
  - Source: https://developers.openai.com/codex/cloud/internet-access
- Codex config surface:
  - OpenAI documents explicit model, token compaction, and approval-related configuration surfaces.
  - Source: https://developers.openai.com/codex/config-reference
- LLM finance research:
  - `The Wall Street Neophyte` shows zero-shot LLM stock prediction underperforming simpler baselines.
  - `AlphaFin` argues for retrieval-augmented, tool-grounded financial analysis rather than free-form generation alone.
  - `The New Quant` surveys production concerns including evaluation, governance, latency, and multilingual cross-market research.
  - Sources:
    - https://arxiv.org/abs/2304.05351
    - https://arxiv.org/abs/2403.12582
    - https://arxiv.org/abs/2510.05533
- Quant strategy references:
  - AQR materials remain a useful anchor for systematic trend, value, momentum, and risk-mitigation design choices.
  - Sources:
    - https://www.aqr.com/insights/trend-following
    - https://www.aqr.com/Insights/Datasets/Value-and-Momentum-Everywhere-Factors-Monthly

## 4. Consolidated Verdict

The repo is still directionally correct.

The current system already has the right long-term shell:

- one authoritative core
- durable state
- governed supervisor loops
- Codex-centered worker execution
- Discord-first owner control
- dashboard-first read surface
- real broker, option, and evolution scaffolding

So the right move is still not a restart.

But this rerun does change the product contract in three important ways:

1. `Deployment market mode` is now a first-class product setting, not just an architecture note.
2. `Single-VPS first` is now a primary product path, not a bootstrap convenience.
3. `Quant-first mechanics + LLM-first meta reasoning` is now the official design split, not just a preference.

## 5. Three Core Points Re-Review

### 5.1 Learn from reference projects without collapsing into them

The original conclusion still holds:

- borrow `DeepEar` for acquisition packs, evidence packaging, checkpointed research, and presentation
- borrow `nofx` for owner UX, onboarding compression, and operator mental models
- do not replace the current authority core with either reference project

The product should feel easier than the current repo feels today, but it should not give up:

- durable state
- approval boundaries
- auditability
- bounded self-improvement

### 5.2 Support US and CN without pretending they are the same market

This rerun makes the deployment rule explicit:

- `QE_DEPLOYMENT_MARKET_MODE=us`
  - active sleeves: `us_equities`, `us_options`
  - research, strategy, and execution may choose equities, options, or mixed US sleeve allocation
- `QE_DEPLOYMENT_MARKET_MODE=cn`
  - active sleeve: `cn_equities`
  - the product shell remains the same, but the runtime does not pretend it can reuse Alpaca-like live execution assumptions

This is not a cosmetic setting.

SSE lot sizes, price limits, and STAR rules materially change:

- sizing
- turnover assumptions
- stop logic
- execution windows
- live-adapter design

XtQuant / MiniQMT also means CN live is not the same deployment ergonomics as a cleaner US HTTP API broker path.

### 5.3 More quantitative, but only where quant should win

This rerun strengthens the earlier split:

- quant owns:
  - universe filtering
  - deterministic scoring
  - ranking
  - options-chain filters
  - sizing inputs
  - rebalance windows
  - turnover and exposure control
- LLMs own:
  - synthesis
  - retrieval-backed interpretation
  - regime labeling
  - challenge and rebuttal
  - incident diagnosis
  - strategy proposal authoring
  - evolution proposals

This is supported by the external literature:

- zero-shot free-form LLM prediction alone is not a strong trading kernel
- retrieval-backed and tool-grounded designs are more credible
- production finance systems still need explicit evaluation, cost control, and governance

## 6. Current Product Re-Review

### 6.1 What is already strong

The current implementation is already stronger than most prompt-mesh projects in these ways:

- there is one durable source of truth
- trading, learning, and evolution are stateful domains
- options and multi-leg structure already exist in the model layer
- there is already a doctor surface, smoke checks, and deployment helpers
- Discord and dashboard are treated as real product surfaces

### 6.2 What still blocks the full target

This rerun keeps four major blockers visible:

1. `Sleeve truth is improved but not fully closed`
   - deployment-scoped market activation now reaches runtime config, supervisor context, acquisition guidance, and dashboard visibility
   - deeper propagation into every strategy, allocation, and execution decision path still needs more closure
2. `Quant layer is still too implicit`
   - the system still needs a clearer deterministic signal engine and feature layer
3. `Auto-evolution closure is materially stronger than the earlier review assumed`
   - repo-side governance already covers auto canary creation, promotion decisions, rollback actuation, and objective-drift checks
   - the remaining gap is operational calibration, visibility, and honest operator messaging rather than a missing governance skeleton
4. `Product maturity is still uneven`
   - the architecture is more mature than the repository presentation and onboarding story

## 7. Dashboard Re-Review

### 7.1 What is working

From the captured desktop and mobile screenshots:

- the dashboard loads
- the visual direction is coherent
- the terminal-like density matches the intended product tone
- degraded fallback state is honest rather than pretending everything is live
- mobile remains usable rather than broken

### 7.2 What still needs improvement

The rerun finds three dashboard issues:

1. `First-screen trust messaging needs another pass`
   - degraded fallback is honest, but the opening state still feels more like a backend status sheet than a mature operator landing screen
2. `Market-mode visibility was missing and is now fixed at the shell level`
   - overview, trading, and system surfaces now expose the deployment market and active sleeves
   - the next layer is to surface sleeve-aware strategy and allocation summaries more explicitly
3. `Single-VPS onboarding visibility is not yet first-run optimized`
   - the page is helpful once you already understand the system, but it can do more to guide a new non-technical owner through first boot and first validation

### 7.3 Design conclusion

Keep the visual direction.

Do not redesign the dashboard into generic SaaS.

Instead:

- surface `deployment market mode`
- surface `active sleeves`
- add clearer first-run empty and degraded states
- keep desktop density, but sharpen mobile priority order

## 8. GitHub Page Re-Review

### 8.1 What the current repo already gets right

- the README is already product-oriented rather than purely architectural
- the docs index exists
- the single-VPS quickstart is visible
- the repository already explains Discord, dashboard, Codex worker, and VPS concepts

### 8.2 What still needs to improve

Against GitHub's own README guidance, the repository page still needs to become more product-complete:

1. `The market-mode story must be explicit`
   - visitors should learn in the README that one deployment chooses `US` or `CN`
2. `The first-run path must feel shorter`
   - the repo should tell a non-technical operator exactly where to start and what they can ignore
3. `GitHub presentation should not rely only on text`
   - the repo should add a social preview image and later dashboard screenshots
4. `Community health should stay visible`
   - the project should keep LICENSE, SECURITY, SUPPORT, and contribution posture legible from the main page

## 9. Deployment Experience Re-Review

### 9.1 What improved meaningfully

The repo is now materially closer to a real single-VPS product path:

- `quickstart-single-vps.sh`
- `onboard-single-vps.sh`
- owner-friendly deploy draft commands
- smoke checks
- doctor endpoint

### 9.2 What this rerun changes

Deployment must now explicitly ask one more question early:

- `Which market mode is this VPS for?`

That question is product-critical because it changes:

- market timezone and calendar defaults
- active sleeve family
- broker expectations
- learning source packs
- dashboard segmentation

This rerun therefore concludes the deploy experience should be:

1. choose `single_vps_compact` or `two_vps_asymmetrical`
2. choose `deployment_market_mode=us|cn`
3. choose first-boot broker posture
4. fill relay, Discord, and dashboard secrets
5. run smoke checks before trusting automation

### 9.3 Current live-trade honesty

The repo should remain explicit about current bounded truth:

- `US` mode can honestly target paper, Alpaca paper, and Alpaca live progression
- `CN` mode can honestly target research, learning, ranking, and paper-first operation now
- `CN live` remains a broker-edge closure task, not something the README should overclaim

## 10. Final Architecture Decisions From This Rerun

These decisions should now be treated as canonical:

1. One product, one Discord bot, one dashboard shell.
2. One deployment picks one market mode.
3. `US` mode enables `us_equities + us_options`.
4. `CN` mode enables `cn_equities`.
5. The product stays `sleeve-first`.
6. The product stays `quant-first in mechanics` and `LLM-first in meta reasoning`.
7. Free acquisition should stay layered:
   - Codex web search first
   - SearXNG-style fallback second
   - RSS and RSSHub feed layer third
   - Playwright as governed last-resort browser fallback
8. Single-VPS first remains the default owner path.
9. Two-VPS remains the stronger long-running isolation path, but not the only supported product shape.

## 11. Required Write-Back Changes

This rerun requires the repo plan and docs to reflect:

- `QE_DEPLOYMENT_MARKET_MODE=us|cn`
- `US` deployment implies equities plus options
- `CN` deployment implies A-share mode
- dashboard and README should surface market mode clearly
- deployment docs must explain market choice before broker choice
- productization stages must treat market mode as a governed deployment-level contract

## 12. GSTACK Verdict

| Review | Scope | Status | Main finding |
|--------|-------|--------|--------------|
| CEO Review | Product scope and ambition | DONE_WITH_CONCERNS | The product direction is right, but it needed a stronger market-mode contract and a clearer quant-vs-LLM split. |
| Engineering Review | Architecture and deployment | DONE_WITH_CONCERNS | The core architecture is still correct, but deployment market mode and sleeve truth needed to become explicit runtime contracts. |
| Design Review | Dashboard, GitHub page, and owner UX | DONE_WITH_CONCERNS | The design direction is good, but first-run clarity, market visibility, and GitHub presentation still needed another pass. |

**Overall verdict:** keep the current repo as the authority core, formalize deployment market mode, keep single-VPS first, and continue productization without restarting the architecture.

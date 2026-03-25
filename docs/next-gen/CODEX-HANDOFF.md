# Codex Handoff

## Purpose

This document is for the next Codex session or a new Codex machine that needs to continue EvoQ without losing context.

It is not a public product spec.
It is the shortest path to:

- understand what the owner actually wants
- understand what is already implemented in the repository
- avoid re-opening already settled architecture debates
- avoid overstating readiness where real VPS validation is still missing

Date of this handoff: `2026-03-25`

Current pushed branch and repository:

- branch: `main`
- repo: `https://github.com/zhoucehuang-arch/evoq`
- latest commit at handoff: `ac585a8` `Replace README screenshots with stable hero image`

Local repository state at handoff:

- `git status --short` was clean

## The Owner's Real Requirements

The owner does not want a toy system, an MVP, or a prompt orchestra that looks autonomous but is hard to govern.

The actual target is:

- long-running autonomous investment runtime
- Discord-first natural-language owner interaction
- easy GitHub-to-VPS deployment
- single-VPS-first product posture
- Codex-centered execution instead of OpenClaw-style prompt scaffolding
- durable memory and continuous learning
- multi-agent or multi-persona discussion where it improves decision quality
- quant-leaning strategy design that still uses LLM strengths where appropriate
- US and CN support, but one deployment chooses one market mode
- US mode must cover equities and options, with governed short and leverage-aware paths
- CN mode is a separate product surface and must remain market-aware
- dashboard visibility that feels like a mature command center, not a generic SaaS admin page

The owner explicitly dislikes:

- MVP-first framing
- partial polish where only one surface is mature
- OpenClaw-style inefficiency and token waste
- product claims that outrun actual operational verification
- paid web-search APIs as the main acquisition path

## What Is Already Canonical

These product decisions are already baked into the repo and should not be casually re-litigated:

- one authoritative Core, not multiple competing masters
- durable database-backed runtime state
- Discord as the write and approval surface
- dashboard as the read, monitoring, and operator surface
- Codex-heavy worker plane behind governed control
- single deployment chooses one market mode: `us` or `cn`
- single-VPS-first deployment is the default owner path
- Core + Worker split is a later scale-up path, not the starting requirement
- paper-first activation remains the safe default
- repo-backed promoted memory is intentionally separate from runtime learning mesh state

## Current Repository Truth

Repository-side implementation is in deployment-handoff state.

That means:

- the repo is no longer waiting on a foundational redesign
- the next major phase is target-environment deployment, secret configuration, smoke validation, and disciplined activation

Canonical current-truth documents:

1. [../../README.md](../../README.md)
2. [PRODUCT-OVERVIEW.md](PRODUCT-OVERVIEW.md)
3. [GITHUB-TO-VPS-DEPLOYMENT.md](GITHUB-TO-VPS-DEPLOYMENT.md)
4. [CURRENT-DELIVERY-STATUS.md](CURRENT-DELIVERY-STATUS.md)

The next Codex should treat those four documents as stronger than older exploratory review notes if there is tension.

## What Was Recently Changed

Recent important commits before this handoff:

- `ac585a8` Replace README screenshots with stable hero image
- `83f4328` Fix README dashboard image layout
- `3a2f6c9` Unify dashboard command center surfaces
- `331ee84` Polish dashboard command center UX
- `04695dd` Refresh dashboard screenshots and rename repo slug
- `100d296` Rename product surface to EvoQ

What these recent commits actually changed:

- the repo and product surface now consistently use the `EvoQ` name
- the dashboard overview, trading, learning, evolution, system, and incidents pages were pulled into one unified command-center visual language
- `System` and `Incidents` were fully upgraded instead of leaving them at an earlier rougher standard
- frontend degraded-state signaling was added to command-center surfaces so broken API conditions are visible instead of visually pretending to be healthy
- `QE_DASHBOARD_DEMO_MODE=1` now covers all dashboard routes, not just the overview page
- the README hero image was changed to a single precomposed showcase image because GitHub README image layout kept rendering poorly with split-image layouts

## Dashboard Status At Handoff

Dashboard routes implemented and verified locally:

- `/`
- `/trading`
- `/learning`
- `/evolution`
- `/system`
- `/incidents`

Verification performed in the repo before handoff:

- `npm run build` passed in `apps/dashboard-web`
- all six dashboard routes returned `200` in local production mode
- Playwright full-page screenshots were used for actual visual QA

Important nuance:

- `gstack` was used for product-review style workflow and route loading checks
- on this Windows environment, `gstack browse` had a practical limitation: route navigation worked, but screenshot and text output could return blank or unusable output
- for actual visual verification, Playwright screenshots were more reliable than `gstack browse` screenshots on this machine

If a future Codex is on Windows and sees blank `gstack browse` screenshots, do not assume the dashboard is broken. Re-check with Playwright or raw HTML fetch before changing product code.

## What Has Been Verified In The Repo

Current documented repository verification:

- `py -m pytest -q` passed with `125` tests
- `py -m compileall src` passed
- `npm run build` passed in `apps/dashboard-web`
- Alembic fresh-database upgrade had already been verified through `20260320_0014`

## What Is Not Yet Verified On The Real VPS

These are still real-world deployment validations, not repository-code tasks:

- actual Core deployment on the target Linux host
- actual Worker deployment if the owner chooses two-node topology
- real Discord secrets and relay secrets
- real broker credentials and real broker sync quality
- real private-network connectivity between Core and Worker if split
- actual systemd restart behavior
- restore drill and break-glass rehearsal on the real target node

Do not claim unattended live readiness without those validations.

## Honest Product Boundaries Still In Place

The next Codex should preserve honest language around these points:

- `CN live` broker execution is still not shipped
- cross-path maintenance-margin, borrow-fee, and locate modeling is still conservative rather than universal
- conflicting or ambiguous option conversion and lifecycle events can still require review
- portfolio sleeve attribution is still conservative in some cases
- owner-facing artifact browsing is still thinner than the core control-plane depth

## Must-Read Files For A New Codex

Read in this order if the goal is to continue the project productively:

1. [../../README.md](../../README.md)
2. [CURRENT-DELIVERY-STATUS.md](CURRENT-DELIVERY-STATUS.md)
3. [PRODUCT-OVERVIEW.md](PRODUCT-OVERVIEW.md)
4. [GITHUB-TO-VPS-DEPLOYMENT.md](GITHUB-TO-VPS-DEPLOYMENT.md)
5. [FIRST-PAPER-RUN-CHECKLIST.md](FIRST-PAPER-RUN-CHECKLIST.md)
6. [OWNER-OPERATION-QUICKSTART.md](OWNER-OPERATION-QUICKSTART.md)
7. [GSTACK-FULL-PRODUCT-REREVIEW.md](GSTACK-FULL-PRODUCT-REREVIEW.md)
8. [MULTI-MARKET-QUANT-ARCHITECTURE-REVIEW.md](MULTI-MARKET-QUANT-ARCHITECTURE-REVIEW.md)
9. [THREE-CORE-POINTS-RESEARCH-AND-OPTIMIZATION-PLAN.md](THREE-CORE-POINTS-RESEARCH-AND-OPTIMIZATION-PLAN.md)

Read these implementation-structure docs next if touching architecture or workflows:

- [SYSTEM-CHARTER.md](SYSTEM-CHARTER.md)
- [STATE-MODEL.md](STATE-MODEL.md)
- [WORKFLOW-CATALOG.md](WORKFLOW-CATALOG.md)
- [ROLE-PERSONA-MODEL.md](ROLE-PERSONA-MODEL.md)
- [CODEX-WORKER-PROTOCOL.md](CODEX-WORKER-PROTOCOL.md)
- [RISK-GOVERNANCE.md](RISK-GOVERNANCE.md)

## Key Source Paths

Main code surfaces to know:

- `src/quant_evo_nextgen`
- `apps/dashboard-web`
- `ops`
- `tests`

Specific files or areas that mattered in the latest work:

- `apps/dashboard-web/app/page.tsx`
- `apps/dashboard-web/app/trading/page.tsx`
- `apps/dashboard-web/app/learning/page.tsx`
- `apps/dashboard-web/app/evolution/page.tsx`
- `apps/dashboard-web/app/system/page.tsx`
- `apps/dashboard-web/app/incidents/page.tsx`
- `apps/dashboard-web/lib/dashboard.ts`
- `apps/dashboard-web/lib/demo-dashboard.ts`
- `apps/dashboard-web/components/top-nav.tsx`
- `docs/assets/dashboard-hero-evoq.png`

## Deployment Posture The Owner Prefers

The owner currently wants the product to be easiest to deploy on one VPS first.

That means future work should continue to prefer:

- simple GitHub clone to `/opt/evoq`
- one-node onboarding flow
- configuration that can be filled on VPS without deep code knowledge
- Discord-first owner interaction instead of terminal-heavy daily use

Do not casually re-expand the product back toward a mandatory multi-node first deploy unless there is a very strong reason.

## Non-Negotiable UX And Product Preferences

Keep these in mind during future work:

- product surfaces should be English by default
- `README.zh-CN.md` can remain the Chinese-specific surface
- dashboard should feel deliberate, terminal-like, and high-signal
- do not let one page become polished while the rest lag behind
- when the owner asks for `gstack`, they mean a full-product review mindset, not a superficial style pass
- if the dashboard or GitHub presentation is touched, review the resulting screenshots and README presentation together

## Search And Acquisition Expectations

The owner explicitly wants strong acquisition and learning capability without relying on paid search APIs.

Current intended direction:

- Codex-native web access where appropriate
- free search and browser-based research paths
- Playwright-based browsing remains important
- SearXNG-style or browser-mediated acquisition remains relevant
- social or anti-bot-heavy sources may need browser fallback instead of plain HTTP fetch

Do not regress to a weak acquisition story that only works on easy static websites.

## Multi-Agent And Self-Improvement Expectations

The owner still cares about:

- multi-persona or multi-expert discussion
- autonomous reflection
- continuous learning
- system and strategy evolution

But the accepted architecture is not "many free agents chatting forever."

The expected shape is:

- governed loops
- durable state
- explicit proposals
- canary and promotion control
- rollback paths
- Codex-heavy execution under Core authority

## What The Next Codex Should Do First

If the next session is about continuing product work, do this first:

1. run `git status --short`
2. read this file
3. read the four canonical product-truth docs
4. verify whether the task is repository work or real-VPS deployment work
5. avoid reopening already-settled architecture unless the user explicitly wants that

If the next session is about deployment, the first operational reading path should be:

1. [GITHUB-TO-VPS-DEPLOYMENT.md](GITHUB-TO-VPS-DEPLOYMENT.md)
2. [FIRST-PAPER-RUN-CHECKLIST.md](FIRST-PAPER-RUN-CHECKLIST.md)
3. [VPS-DEPLOYMENT-RUNBOOK.md](VPS-DEPLOYMENT-RUNBOOK.md)
4. [BACKUP-AND-RESTORE-RUNBOOK.md](BACKUP-AND-RESTORE-RUNBOOK.md)
5. [BREAK-GLASS-RUNBOOK.md](BREAK-GLASS-RUNBOOK.md)

## Secrets And Safety

Do not store or re-commit:

- GitHub PATs
- relay API keys
- broker credentials
- Discord secrets
- dashboard credentials

Previous sessions involved user-provided PATs and relay compatibility notes, but those secrets must not be written into repo docs or checked into the repository.

## Practical Handoff Conclusion

This repo is not waiting on another big concept pass.

The architecture, product framing, documentation set, and dashboard command-center surfaces are already in place.

The next Codex should treat the project as:

- productized
- repository-ready
- deployment-handoff ready
- still requiring real-environment validation before unattended live operation claims

If you are the next Codex, start from this file, then the four canonical current-truth docs, then continue from the exact user request in your session.

# Dashboard Website Spec

## Purpose

The dashboard is the primary owner workbench for EvoQ. It is where the owner reviews health, research evidence, market data, strategy backtests, paper runs, governance, incidents, and execution readiness. Telegram or another light gateway may handle alerts, quick approvals, pause/resume, and emergency actions, but it must not replace the dashboard as the main operating surface.

Reference aesthetic:

- `https://nadah-dashboard.vercel.app/`

## Product Objectives

The dashboard should let the owner understand, within a few seconds:

- whether the system is healthy
- whether trading is running inside approved boundaries
- whether learning and evolution are still producing useful output
- whether operator action is needed now
- how fresh the visible data is

## Non-Goals

The dashboard should not become:

- a high-frequency approvals console
- a full terminal replacement
- a place for long-form chat with the system
- an ungoverned direct-write surface for risky runtime actions

## UX Direction

The visual direction should stay close to the current product direction:

- dense but readable
- state-first, not marketing-first
- obvious freshness indicators
- strong status hierarchy
- mobile-readable, even if desktop remains primary
- honest boundaries instead of false real-time confidence

## Core Sections

### `/`

Overview page:

- headline and highlights
- freshness
- runtime mode
- market mode
- risk state
- active goals
- pending approvals
- active sleeves
- condensed strategy / learning / governance snapshots

### `/trading`

Trading page:

- account and equity snapshots
- positions
- orders
- sleeve exposure
- strategy attribution
- session status
- broker-sync health
- risk limits and triggered controls

### `/evolution`

Evolution page:

- current improvement goals
- Codex queue and recent runs
- canary / promotion state
- rollback history
- objective drift warnings

### `/learning`

Learning page:

- source-ingest status
- recent documents
- evidence extraction throughput
- promoted insights and principles
- memory freshness
- acquisition degradation state

### `/system`

System page:

- incidents
- workflow backlog
- loop health
- open overrides
- config proposals
- deployment posture
- doctor summary

## Information Rules

Every dashboard page should obey the same rules:

- show freshness close to the data
- make degraded or missing data obvious
- separate durable truth from derived summaries
- show actionability before detail
- never imply live support that the product does not actually ship

## Data Contract

The dashboard should read from API summaries backed by durable state, not from ad hoc file scraping.

Preferred data sources:

- runtime snapshots from Postgres-backed services
- doctor summaries
- workflow state summaries
- deployment-state summaries

Avoid:

- reading chat or gateway history as source of truth
- treating README text as operational state
- coupling UI state to temporary workspace files

## Current Honest Boundaries

The dashboard must continue to present these boundaries clearly:

- CN live broker execution is not shipped
- some sleeve attribution remains conservative
- margin / borrow / locate modeling is not fully universal yet
- Playwright is a governed fallback path, not the default acquisition tier

## Mobile Behavior

Mobile is supported for review, not for deep operations.

Minimum mobile guarantees:

- all cards remain readable
- critical state chips stay visible above the fold
- command examples remain copyable
- no section becomes impossible to inspect on a phone

## Accessibility and Readability

- use clear contrast for good / warn / bad tones
- avoid relying on color alone to communicate status
- keep labels short and concrete
- prefer human-readable English over internal code jargon when rendering UI

## Shipping Checklist

Before calling the dashboard healthy, verify:

- the Overview page renders with live API data
- freshness is visible
- fallback states do not look broken
- mobile layout is usable
- boundary text matches the real product surface
- labels and prompts are fully English

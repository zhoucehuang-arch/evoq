# Topology and Scaling Decision

## 1. Decision Summary

For this system, the best-fit long-term architecture is:

- `1 Discord bot`
- `1 authoritative control plane`
- `1 authoritative runtime database`
- `2 physical VPS as the production minimum`
- `N research workers as the scaling path`

In short:

```text
single-writer core + elastic research plane
```

This is the architecture that best balances:

- long-term stability
- quality
- governance
- ease of operation
- safe automation
- continuous learning
- multi-agent debate
- Codex-centered execution

## 2. Why This Is the Best Fit

The system is trying to do all of the following at once:

- trade continuously
- learn continuously
- evolve continuously
- debate internally
- use Codex-compatible execution for real implementation work
- stay controllable from Discord
- stay operable by a mostly non-technical owner

Those goals create a direct tension:

- more autonomous agents improve coverage and creativity
- more autonomous agents also increase chaos, cost, coordination failure, and recovery complexity

The best architecture is therefore not "the most agents" or "the most nodes".

The best architecture is the one that:

- preserves a single authority path for money and promotion
- allows many bounded workers for learning and implementation
- keeps research noise away from trading control
- scales horizontally only where horizontal scaling is actually useful

## 3. Architecture Planes

The architecture should be designed as three planes from day one.

### 3.1 Control Plane

Owns:

- Discord interaction
- owner intent routing
- workflow orchestration
- task scheduling
- approvals
- incidents
- budget governance
- decision reduction
- strategy promotion
- goal promotion

### 3.2 Data Plane

Owns:

- authoritative Postgres
- artifact metadata
- evidence records
- decision records
- workflow history
- approval history
- incident history

### 3.3 Work Plane

Owns:

- Codex workers
- web research
- scraping
- browser automation fallback
- backtests
- evals
- report generation

Physical node count can change.

These logical planes should not.

## 4. Recommended Physical Topology

### 4.1 Production minimum: `2 VPS, asymmetrical`

```text
VPS-A Core
  -> control plane
  -> data plane
  -> trading authority

VPS-B Research
  -> work plane
```

This is better than a symmetric 2-node design.

It is also better than a swarm of equal autonomous agent hosts.

### 4.2 Why asymmetry matters

The core node should be boring.

The research node should be allowed to be noisy.

That split improves:

- uptime
- incident isolation
- predictable latency
- governance clarity
- secret separation
- debugging

## 5. One VPS vs Two VPS vs N Nodes

### 5.1 One VPS

Best for:

- development
- local validation
- paper mode
- low budget

Advantages:

- cheapest
- easiest first deployment
- no cross-node networking

Weaknesses:

- one blast radius
- resource contention
- browser jobs can interfere with trading control
- weaker secret separation
- weaker governance boundaries

Judgment:

- acceptable as a temporary mode
- not the best long-term live architecture

### 5.2 Two VPS

Best for:

- first real production deployment
- continuous learning plus trading
- stable governance
- easy mental model

Advantages:

- strong isolation between core and research
- easy to operate
- easy to scale later
- much better failure containment

Weaknesses:

- slightly more ops work than one box
- one more machine to patch and monitor

Judgment:

- best-fit default
- the strongest recommendation

### 5.3 Three or more nodes

Best for:

- heavier research volume
- more backtests
- more browser jobs
- more evals
- higher durability requirements

Correct scaling pattern:

- keep one authority core
- scale only the work plane horizontally
- improve DB durability before adding too many worker nodes

Wrong scaling pattern:

- multiple equal autonomous masters
- multiple nodes with broker write authority
- one Discord bot per persona

Judgment:

- useful after the 2-node base
- should be incremental and role-specific

## 6. The Real Scaling Priority

When going beyond two nodes, the next priority should usually be:

1. database durability
2. research concurrency
3. browser/scrape specialization
4. backtest/eval specialization

Not:

1. more debate nodes
2. more master planners
3. more bots

This system is limited first by:

- runtime truth durability
- safe control of capital
- governance quality

not by the number of thinking personas.

## 7. Multi-Agent Design: Independent, but Not Sovereign

The agents should be independently thinking in a logical sense, but not sovereign in an operational sense.

### 7.1 What independent should mean

Each role gets:

- its own prompt and persona
- its own subtask
- its own context window
- its own budget
- its own evidence packet

Examples:

- research scout
- strategist
- skeptic
- risk reviewer
- systems optimizer
- evaluator

### 7.2 What independent should not mean

Do not give every role:

- permanent full autonomy
- direct broker access
- direct production promotion rights
- uncontrolled long-lived loops
- unrestricted repo mutation

### 7.3 Final decision model

Use a reducer or adjudicator workflow:

- gather proposals
- compare evidence
- produce a structured decision card
- record rationale
- route to approval or execution

This preserves the quality benefits of debate without the chaos of many sovereign agents.

## 8. Codex-Centered, Not Codex-Only

You asked whether the core tasks can still be based on Codex CLI style execution.

Yes.

That is compatible with this architecture.

But the best design is:

- `Codex-centered`
- not `Codex-only`

### 8.1 What Codex should own

- code implementation
- refactors
- test writing
- repair tasks
- repo analysis
- shell execution
- integration scripts
- infra edits

### 8.2 What should not always go through Codex

- cheap routing
- high-frequency classification
- simple status synthesis
- some long-form web research jobs

Reason:

- cost
- latency
- token efficiency
- cleaner separation of concerns

Inference:

If your third-party relay supports Codex-compatible execution and related model calls, the system should expose provider abstraction now so you can keep the same architecture even if the relay changes later.

## 9. Durable Workflow Choice

### 9.1 Recommended choice for this project

Best-fit orchestration choice:

- `DBOS + Postgres` as the durable workflow backbone
- `PydanticAI` for agent behavior and model/provider abstraction
- custom state model in the app for governance records

### 9.2 Why this fits

DBOS gives you:

- durable workflows on top of Postgres
- recovery from checkpoints
- horizontal execution across many servers
- fewer moving parts than a full separate orchestrator stack

PydanticAI gives you:

- provider abstraction
- durable-agent integrations
- MCP support
- structured outputs
- eval-friendly Python ergonomics

### 9.3 What is stronger in absolute enterprise terms

If the question is pure large-scale enterprise orchestration, `Temporal` is a stronger and more established heavy-duty choice.

But for your operator profile and deployment goals, it is likely too heavy too early.

So the recommendation is:

- use `DBOS` now for best-fit SOTA
- keep contracts clean enough that a future move to `Temporal` remains possible

## 10. Learning and Web Acquisition Strategy

The system should learn continuously, but through a layered acquisition strategy.

### 10.1 Layer 1: official structured APIs

Use official APIs first whenever practical.

Examples:

- broker and market data APIs
- exchange APIs
- YouTube Data API
- X API if budget and access make sense

Why:

- stable structure
- less anti-bot pain
- better legal clarity
- cleaner evidence normalization

### 10.2 Layer 2: hosted web search

Use hosted web search for:

- discovery
- current news
- broad topic scans
- source shortlist generation

This is especially useful for continuous research loops.

### 10.3 Layer 3: search + scrape services

Use services like Firecrawl for:

- web search plus page extraction
- bulk content retrieval
- markdown or HTML normalization
- evidence ingest

### 10.4 Layer 4: browser automation fallback

Use browser automation only when needed for:

- dynamic sites
- auth flows
- anti-bot obstacles
- complex rendered pages

Browserbase- or Playwright-style automation fits here.

### 10.5 Layer 5: GUI or headed browser fallback

A full GUI machine should not be the primary production path.

It should exist only for:

- debugging
- rare manual recovery
- exceptional sites

## 11. Should You Run a Dedicated GUI Machine?

Usually no.

A permanent GUI VPS is not the optimal default.

Reasons:

- higher cost
- lower throughput
- worse operability
- more fragile automation
- harder scaling

Better alternative:

- use a browser automation worker or managed remote browser service
- reserve headed mode for narrow exception paths

## 12. Governance Rules That Must Not Change

If you want the design to stay stable over time, keep these rules fixed:

1. One runtime source of truth.
2. One final promotion authority.
3. One live trading authority.
4. Debate before important decisions, not before every tiny task.
5. Learning artifacts become evidence records before memory.
6. Self-improvement never deploys straight to live.
7. Research workers never need broker secrets.

## 13. Practical Infra Sizing

This is my implementation recommendation, not a vendor requirement.

### 13.1 Core VPS

Recommended starting point:

- 4 vCPU
- 8 to 16 GB RAM
- fast SSD
- strong network stability

### 13.2 Research VPS

Recommended starting point:

- 8 vCPU
- 16 to 32 GB RAM
- larger SSD

If you add browser automation and heavy backtests, the research node should scale first.

## 14. Final Recommendation

If we compress everything into one answer:

The optimal architecture for your system is not "1 VPS" or "2 VPS" in isolation. It is a `single-writer control plane + elastic research plane` architecture that happens to start at `2 asymmetrical VPS` in production, keeps `1 Discord bot`, runs multi-agent debate as logical bounded workflows instead of many sovereign daemons, uses `Codex CLI` as the main execution fabric, and uses a layered learning stack of `official APIs -> hosted web search -> search/scrape -> browser fallback`.

That is the design that best preserves:

- long-term stability
- quality
- efficiency
- governance
- future scalability

without locking you into a fragile swarm.

## 15. External References Reviewed

- OpenAI Codex config reference: https://developers.openai.com/codex/config-reference/
- OpenAI Codex sandbox and approvals: https://developers.openai.com/codex/agent-approvals-security/
- OpenAI Codex cloud internet access: https://developers.openai.com/codex/cloud/internet-access/
- OpenAI Codex quickstart: https://developers.openai.com/codex/quickstart/
- OpenAI Responses deep research: https://developers.openai.com/api/docs/guides/deep-research/
- DBOS architecture: https://docs.dbos.dev/architecture
- DBOS workflow recovery: https://docs.dbos.dev/production/workflow-recovery
- PydanticAI durable execution overview: https://ai.pydantic.dev/durable_execution/overview/
- PydanticAI multi-agent applications: https://ai.pydantic.dev/multi-agent-applications/
- Discord interactions overview: https://discord.com/developers/docs/interactions/overview
- Discord receiving and responding: https://discord.com/developers/docs/interactions/receiving-and-responding
- Browserbase MCP introduction: https://docs.browserbase.com/integrations/mcp/introduction
- Browserbase stealth mode: https://docs.browserbase.com/features/stealth-mode
- Firecrawl search: https://docs.firecrawl.dev/features/search
- X API introduction: https://docs.x.com/x-api/introduction
- YouTube Data API getting started: https://developers.google.com/youtube/v3/getting-started

## 16. Bootstrap Warning

The current local scaffold is intentionally smaller than the final production architecture.

That is acceptable only because:

- it is treated as a bootstrap stack
- the long-term authority model is already fixed
- future implementation is constrained by the topology decision instead of reinterpreting the bootstrap as the end state

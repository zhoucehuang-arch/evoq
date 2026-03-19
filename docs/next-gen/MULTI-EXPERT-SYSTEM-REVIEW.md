# Multi-Expert System Review

## 1. Purpose

This review is a pre-implementation audit gate.

It is intentionally broader than a normal architecture review. The system is trying to combine:

- autonomous trading
- autonomous learning
- autonomous self-improvement
- multi-agent debate
- Discord-first owner interaction
- VPS self-hosting
- Codex-centered execution

That combination creates failure modes that do not appear in ordinary trading bots or ordinary agent systems.

## 2. Hidden Goals and Hidden Constraints

Based on the repository, the conversations, and the intended operating model, the real target is not just "an automated investment system".

The real target is:

- a system that can continue operating when the owner is absent
- a system that can keep learning without poisoning itself
- a system that can keep improving without rewriting its own mission
- a system that can trade without letting research noise leak into capital decisions
- a system that remains understandable and governable by a non-technical owner
- a system that is portable across providers and API relays

These hidden constraints are now treated as first-class design requirements:

- owner absence for 72 hours, 7 days, and 30 days
- provider relay instability, drift, and rate-limit differences
- hostile or low-quality web content
- Discord or dashboard credential compromise
- broker outage and reconciliation failure
- cost blow-ups from debate, search, and self-modification loops
- mission drift caused by local optimization

## 3. Panel Composition

This review is structured as if it were performed by eight independent expert lenses:

1. systems architect
2. quant and risk engineer
3. autonomy and self-improvement researcher
4. knowledge and learning architect
5. security and trust engineer
6. SRE and operations architect
7. product and owner-experience designer
8. cost and governance controller

## 4. Consolidated Verdict

The current direction is correct, but it is not yet safe enough to be treated as implementation-ready in the strong sense.

The current design package is already much stronger than the original OpenClaw runtime model. However, it still had several structural blind spots:

- the mission priority order was still implicit
- owner absence was not formalized as a design constraint
- provider and relay instability was not yet modeled as state
- learning safety was not yet strong enough against poisoning, prompt injection, and staleness
- market session, timezone, and broker degradation rules were still under-specified
- disaster recovery and drill discipline were still too soft
- identity compromise and break-glass operations were under-specified
- the current scaffold still contained real code-level language and bootstrap-drift issues

## 5. Findings by Expert Lens

### 5.1 Systems Architect

Main finding:

- The architecture direction is good, but the mission priority order was not yet explicit enough. Without a hard priority ladder, the system could optimize for learning or growth while silently degrading survivability and governance.

Required fix:

- Make `survival -> auditability -> capital protection -> governance continuity -> learning/evolution -> return optimization` explicit.

### 5.2 Quant and Risk Engineer

Main finding:

- Trading lifecycle and risk boundaries are present, but market-calendar rules, session controls, broker degradation behavior, and live promotion thresholds are still not detailed enough.

Required fix:

- Add explicit session guards, broker outage degradation paths, and stricter promotion criteria before any live path is considered.

### 5.3 Autonomy and Self-Improvement Researcher

Main finding:

- The self-improvement loop exists, but objective drift risk is still too high. A system that keeps optimizing itself can end up optimizing proxy metrics, output volume, or perceived intelligence rather than long-term capital and governance quality.

Required fix:

- Add objective-drift review, capability scorecards, and a hard mission-priority review workflow.

### 5.4 Knowledge and Learning Architect

Main finding:

- Continuous learning is first-class, but the design was still too optimistic about source quality. Without trust decay, revalidation, and poisoning quarantine, long-term memory can become polluted slowly and invisibly.

Required fix:

- Add source revalidation, trust decay, poisoning quarantine, and explicit freshness requirements before memory promotion.

### 5.5 Security and Trust Engineer

Main finding:

- The current docs already treat broker secrets carefully, but identity and access failure modes are still under-modeled. Discord bot compromise, dashboard token leakage, and provider credential exposure need stronger incident paths.

Required fix:

- Add explicit compromise-response workflows, break-glass takeover, and separate trust boundaries for Discord, dashboard, broker, provider, and research workers.

### 5.6 SRE and Operations Architect

Main finding:

- The topology is now much better, but operator absence, backup restore drills, recovery checkpoints, and environment distinction between bootstrap and production still needed hardening.

Required fix:

- Make local bootstrap explicitly non-production, add recovery drill cadence, and define operator-absence safe-mode escalation.

### 5.7 Product and Owner-Experience Designer

Main finding:

- The direction is owner-friendly in principle, but the current scaffold still had a practical failure: the Chinese natural-language path had encoding drift, which would have made real owner interaction unreliable.

Required fix:

- Clean up all owner-facing Chinese text paths and keep Chinese-first interaction as a real tested requirement, not just a doc promise.

### 5.8 Cost and Governance Controller

Main finding:

- Multi-agent debate is valuable, but the design still needed stronger rules for when debate is worth its cost. Otherwise the system risks becoming articulate but economically inefficient.

Required fix:

- Add explicit stop rules, value measurement, and marginal-utility review for councils, roles, and personas.

## 6. P0 Problems

These are the highest-priority issues that would have made the system direction incomplete if left unresolved:

1. No explicit mission priority order.
2. No explicit owner-absence operating model.
3. No explicit provider/relay drift and outage model.
4. No explicit poisoned-learning quarantine and revalidation model.
5. No explicit broker/session degradation model.
6. No explicit compromise-response model for Discord/dashboard/provider.
7. The current scaffold contained broken Chinese text paths and a bootstrap stack that could be mistaken for production.

## 7. P1 Problems

Important, but slightly less urgent:

1. Capability scorecards were not yet defined.
2. Strategy promotion thresholds were still too qualitative.
3. Disaster recovery drills were not yet formalized.
4. Cost attribution per workflow and per council was still too soft.
5. Local bootstrap and final production topology needed clearer separation.

## 8. Optimization Decisions Adopted

This review adopts the following design changes:

1. Treat this review as a required audit gate before deeper implementation.
2. Add explicit hidden requirements and mission priority order.
3. Add state entities for provider health, source health, operator override, market session, and drill records.
4. Add workflows for source revalidation, poisoning quarantine, market session guard, provider outage response, compromise response, disaster recovery drills, and objective-drift review.
5. Add risk domains for provider risk, learning poisoning, identity compromise, legal/TOS risk, operator absence, and mission drift.
6. Mark the current Docker Compose stack as local bootstrap only.
7. Fix the owner-facing Chinese interaction path in the scaffold.

## 9. What Was Optimized in This Pass

This pass is a design-hardening pass, not a feature-completion pass.

It includes:

- a new review document
- roadmap updates
- deployment and topology clarifications
- stronger hidden-requirement modeling
- scaffold cleanup for Chinese natural-language interaction
- provider/timezone/topology configuration placeholders

It does not yet include:

- full persistent state implementation
- broker integration
- live trading
- full dashboard auth
- disaster recovery automation

## 10. Gate to Further Implementation

The project should now continue with implementation, but only under these audit-adjusted constraints:

1. Stage 2 must encode the new state entities, not just the earlier minimal schema.
2. Provider abstraction must be part of the initial persistence and config layer.
3. Discord write actions must be backed by durable state and approvals.
4. Learning storage must support source health, trust decay, and revalidation.
5. Trading execution must not proceed without session guards, reconciliation cadence, and degradation rules.
6. Self-improvement must not proceed without objective-drift review and eval gating.

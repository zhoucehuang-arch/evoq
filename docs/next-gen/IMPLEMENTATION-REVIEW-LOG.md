# IMPLEMENTATION REVIEW LOG

## Entry Template

- Slice:
- Date:
- What changed:
- What was validated:
- Issues found:
- Reflection:
- Next move:

## 2026-03-18 / Slice 0 / Design Package

- Slice: Next-gen design and operations package
- Date: 2026-03-18
- What changed:
  Added the core design docs, then expanded them with deployment, Discord natural-language interaction, dashboard, and core-goal coverage review.
- What was validated:
  Verified the docs are present under `docs/next-gen/` and linked from the package index.
- Issues found:
  The repository still lacked an executable project baseline, so the design package alone was not enough to start validating real runtime behavior.
- Reflection:
  The architecture direction is now much clearer, but the repo still needed an honest implementation foundation before more design detail would be useful.
- Next move:
  Build the Stage 1 foundation with runnable backend, dashboard shell, and deployment scaffolding.

## 2026-03-18 / Slice 1 / Foundation Scaffold

- Slice: Stage 1 foundation scaffold
- Date: 2026-03-18
- What changed:
  Added the root environment template, Docker Compose baseline, Dockerfiles, Python package scaffold, repo-derived status API, Discord natural-language shell baseline, Codex run protocol code, dashboard web shell, and initial tests.
- What was validated:
  Installed backend dependencies, installed dashboard dependencies, passed `pytest`, passed `next build`, and verified `/healthz`, `/api/v1/system/status`, and `/api/v1/dashboard/overview` through FastAPI `TestClient`.
- Issues found:
  Docker is not installed in the current environment, so `docker compose config` could not be validated here. Local editable install also revealed Python dependency conflicts with unrelated globally installed packages, which confirms Docker or an isolated virtual environment should remain the default path.
- Reflection:
  The foundation is now real enough to inspect and extend. The best part is that the API already reflects the current repo truth instead of returning empty placeholders. The main gap is that control actions are still intentionally read-only previews until persistence, approvals, and workflow state transitions are wired in.
- Next move:
  Implement persistent state and read models next: database schema, workflow tables, approval records, and the first write-capable control-plane actions.

## 2026-03-18 / Slice 2 / Topology and Scaling Decision

- Slice: Long-term topology, scaling, and learning-stack decision
- Date: 2026-03-18
- What changed:
  Added a dedicated topology decision document, rewrote the package index in clean ASCII English, and updated operations and roadmap docs to make `2 VPS, asymmetrical` the explicit production default while preserving a clean path to `N` research workers. The docs now also make the learning stack explicit: official APIs first, then hosted web search, then search/scrape, then browser automation fallback.
- What was validated:
  Cross-checked the decision against current official docs for Codex provider configuration, Codex network and sandbox behavior, Discord interaction timing constraints, DBOS workflow durability and scaling, PydanticAI durable execution integrations, and browser/search tooling references.
- Issues found:
  The previous operations doc still positioned single-VPS as the default recommendation, which would have pushed the project toward a weaker long-term production topology. The document encoding was also not rendering cleanly in the current shell, making it harder to review incrementally.
- Reflection:
  The biggest improvement here is not adding more moving parts, but fixing authority boundaries early. The architecture is now much closer to a stable shape: one core authority node, separate noisy research execution, and a scaling story that adds workers without multiplying masters.
- Next move:
  Implement Stage 2 persistence with the new topology assumptions baked in: durable state tables, write-capable control actions, provider abstraction for the relay API, and database-backed dashboard read models.

## 2026-03-18 / Slice 3 / Multi-Expert Audit and Design Hardening

- Slice: Multi-expert architecture audit and design optimization
- Date: 2026-03-18
- What changed:
  Added a dedicated multi-expert system review, promoted hidden constraints into explicit design requirements, updated the roadmap to treat this audit as a gate before deeper implementation, and cleaned up scaffold-level drift in Chinese natural-language interaction, local bootstrap labeling, provider placeholders, and topology signaling.
- What was validated:
  Re-read the design package through systems, risk, autonomy, learning, security, operations, product, and cost lenses. Verified that the current scaffold now uses real Chinese status-routing text instead of mojibake and that settings support topology, timezone, and provider-base-url placeholders.
- Issues found:
  The strongest hidden problem was that the direction was correct but still too optimistic. Without explicit owner-absence handling, provider drift handling, poisoning controls, and mission-priority ordering, implementation would likely have recreated a harder-to-debug version of the original governance problem.
- Reflection:
  This slice matters because the next failures would not have been ordinary coding bugs. They would have been structural mistakes discovered only after more implementation work, when changing direction would be much more expensive.
- Next move:
  Implement Stage 2 with the audit findings encoded in the schema and control plane: provider state, source-health state, operator overrides, market-session guards, and durable write actions.

## 2026-03-18 / Slice 4 / Consistency Cleanup and Owner-Facing Validation

- Slice: Audit follow-up consistency cleanup
- Date: 2026-03-18
- What changed:
  Normalized the newly added audit appendices in the Chinese core design docs, fixed the section separation issue in `SYSTEM-CHARTER`, and added a router test that verifies Chinese status responses remain readable and structured.
- What was validated:
  Re-read the charter, state model, workflow catalog, and risk governance docs in UTF-8 mode and confirmed the owner-facing router still classifies Chinese control intents correctly.
- Issues found:
  The repository is now more internally consistent, but the top-level audit package is still mixed-language overall. That is acceptable for implementation, yet the owner-facing reading experience can be improved further later.
- Reflection:
  This cleanup matters because governance docs only help if the owner can actually read them without friction. Mixed-language appendices and untested owner-facing language paths are easy to dismiss as cosmetic, but they often become real operating pain during incidents.
- Next move:
  Move into Stage 2 persistence and encode the audit findings into durable schema, workflow state, and approval-backed control actions.

## 2026-03-18 / Slice 5 / Stage 2 Persistence Kernel and Reference Research

- Slice: Persistence kernel, migration path, and long-running loop reference research
- Date: 2026-03-18
- What changed:
  Implemented the Stage 2 persistence kernel with SQLAlchemy models, database session management, Alembic scaffolding, state store services, persistent goals/incidents/approvals/operator overrides, persisted workflow runs/events, and DB-backed dashboard runtime counts. Also added a full-system stage plan and a reference research document covering Ralph Loop, OpenClaw, the remote coding agent system, and official Codex guidance.
- What was validated:
  Passed `pytest` with new persistence and API coverage. Verified compileability with `py -m compileall src`. Confirmed dashboard runtime counts now come from the database while repo-derived strategy and memory stats still provide the bootstrap visibility layer.
- Issues found:
  SQLite returned naive datetimes for persisted heartbeat timestamps, which initially broke freshness calculations. This was fixed by normalizing timestamps before freshness math.
- Reflection:
  This slice moves the system from “design package plus scaffold” into the first real control-plane kernel. The most important improvement is not the number of tables, but the fact that runtime truth, approvals, incidents, and workflow records now have a durable home. The reference research also clarified that Ralph-style outer loops are valuable, but only when bounded by governance and budgets.
- Next move:
  Continue Stage 2 until Discord write actions and richer read models are durable, then move into Stage 3 Discord control plane and Stage 6 continuous loop supervisor design/implementation.

## 2026-03-18 / Slice 6 / Stage 5 Codex Fabric Runtime

- Slice: Durable Codex Fabric runtime, Ralph-style retries, and runner deployment path
- Date: 2026-03-18
- What changed:
  Added durable Codex run, attempt, and artifact persistence; implemented Ralph-style progress, guardrail, and handoff files under workspace state; wired API endpoints and dashboard cards for Codex runs; added automatic review/eval phase progression; added stale-run recovery for interrupted workers; and introduced a dedicated `codex-fabric-runner` compose service with a Codex CLI-capable container image.
- What was validated:
  Passed `py -m pytest` with `16` tests, including new Codex Fabric execution, retry, stale-run recovery, and API/dashboard coverage. Passed `py -m compileall src`. Passed `npm run build` in `apps/dashboard-web`.
- Issues found:
  The local environment still cannot validate Docker Compose runtime because Docker is not installed here. Workspace isolation is also still logical rather than full `git worktree` isolation, so the current runner is durable but not yet the final safety shape for high-risk autonomous code changes.
- Reflection:
  This slice matters because it turns Codex from an idea in the design docs into a real governed subsystem. The most important quality improvement is not just that runs execute, but that interruption, retries, handoffs, and audit trails now have durable homes instead of living only inside transient prompts.
- Next move:
  Connect supervisor loops to Codex run generation next, then build the learning ingest and evidence-promotion pipeline on top of the new execution fabric.

## 2026-03-18 / Slice 7 / Supervisor-to-Codex Closed Loop

- Slice: Supervisor-driven Codex task generation and bounded continuous research
- Date: 2026-03-18
- What changed:
  Linked supervisor workflows to Codex runs with durable `workflow_run_id` and `supervisor_loop_key` lineage, added active-run deduplication and queue backpressure checks, promoted the research-intake loop to an active default, implemented supervisor handlers for research intake, strategy evaluation, council reflection, and owner-absence watch, and wired the supervisor runner to the Codex Fabric service.
- What was validated:
  Passed `py -m pytest` with `18` tests, including new supervisor tests for Codex queue creation and duplicate-run suppression. Passed `py -m compileall src`. Passed `npm run build` in `apps/dashboard-web`.
- Issues found:
  Research intake is now truly active, but the deeper Stage 7 learning mesh is still incomplete because external evidence is not yet being normalized into durable evidence, topic, and promotion records. Council reflection currently uses one governed Codex run with explicit multi-perspective prompting, not a full multi-worker debate graph yet.
- Reflection:
  This slice is the first time the outer loop is meaningfully alive. The supervisor is no longer only observing the system; it can now dispatch bounded work into the Codex fabric while preserving auditability and avoiding duplicate queue spam.
- Next move:
  Implement the learning inbox and evidence-promotion layer next so research-intake Codex runs feed a durable knowledge pipeline instead of stopping at artifacts and handoffs.

## 2026-03-18 / Slice 8 / Stage 7 Insight Gates and Quarantine

- Slice: Durable insight synthesis, learning quarantine, and owner-visible learning gates
- Date: 2026-03-18
- What changed:
  Extended the Stage 7 learning mesh from `document` and `evidence_item` into durable `insight` records with promotion states and quarantine reasons. Added a new active `learning-synthesis` supervisor loop, persisted `mem_insight`, taught the learning service to merge structured outputs across Codex phases before ingestion, connected citation-derived source health to learning gating, added a `resynthesis_pending` update path for existing insights, exposed learning insights through API and dashboard views, and added dashboard cards that show the current learning gate state rather than only raw research inbox volume.
- What was validated:
  Passed `py -m pytest` with `26` tests, including new coverage for insight synthesis, quarantine handling, source-health-driven blocking, supervisor loop execution, learning API/dashboard exposure, and resynthesis of existing insights. Passed `py -m compileall src`. Passed `npm run build` in `apps/dashboard-web`.
- Issues found:
  The first implementation initially relied only on the final Codex phase payload, which would have dropped earlier risk signals from implement/review phases and allowed the eval summary to overwrite the substantive research summary. It also exposed too little lineage and gate telemetry on the owner-facing learning page. Both problems were corrected by preserving implement-phase research content during ingestion, wiring source health into learning gates, and exposing structured lineage and metrics through the dashboard contract.
- Reflection:
  This slice matters because autonomous learning without an explicit gate is where long-running systems quietly poison themselves. The system now has a more honest shape: research does not become durable guidance just because a Codex run finished. It must cross a visible synthesis and quarantine step first.
- Next move:
  Continue Stage 7 into many-document topic synthesis and principle promotion, then move into the full Stage 8 strategy lifecycle on top of the stronger learning substrate.

## 2026-03-18 / Slice 9 / Stage 8 Strategy Lab Backbone

- Slice: Durable strategy lifecycle, trading dashboard strategy view, and strategy-evaluation supervisor context
- Date: 2026-03-18
- What changed:
  Added durable strategy lifecycle models for hypothesis, strategy spec, backtest run, paper run, promotion decision, and withdrawal decision. Exposed create/list APIs for the full strategy lab flow, wired strategy metrics into the trading dashboard payload, upgraded the trading dashboard page to show recent specs/backtests/paper runs, integrated durable strategy metrics into the strategy-evaluation supervisor loop context, and added the Stage 8 Alembic migration plus new strategy lifecycle tests.
- What was validated:
  Passed `py -m pytest` with `29` tests, including new strategy lab service tests, API persistence tests, and supervisor integration coverage. Passed `py -m compileall src`. Passed `npm run build` in `apps/dashboard-web`.
- Issues found:
  The first validation pass caught a runtime `NameError` in the trading dashboard API because `PaperRunCard` was not imported in the dashboard service. Compile-only checks did not catch it, but the API test did. The import was added and the full validation suite was re-run to green.
- Reflection:
  This slice closes an important structural gap. The system no longer jumps from research and broad ideas into an ambiguous pre-trading space. It now has a durable, inspectable strategy pipeline that the owner and future trading controls can reason about explicitly.
- Next move:
  Extend Stage 8 into allocation policy and governed promotion committee flows, then begin Stage 9 broker, session, reconciliation, and risk-halt implementation.

## 2026-03-18 / Slice 10 / Stage 9 Execution Readiness Kernel

- Slice: Market session guard, broker snapshot state, reconciliation halts, and trading-readiness dashboarding
- Date: 2026-03-18
- What changed:
  Added durable execution entities for `broker_account_snapshot` and `reconciliation_run`, introduced a dedicated `ExecutionService`, exposed create/list/readiness APIs for market sessions, broker snapshots, reconciliation runs, and provider incidents, activated a new supervisor `market-session-guard` loop, and upgraded the trading dashboard to show execution readiness, latest broker snapshot, latest reconciliation result, recent market sessions, and active provider incidents. Reconciliation divergence can now trigger a durable trading pause override plus an incident automatically.
- What was validated:
  Passed `py -m pytest` with `33` tests. Passed `py -m compileall src tests alembic/versions`. Passed `npm run build` in `apps/dashboard-web`. Installed Alembic in the local Python runtime and verified a fresh SQLite `upgrade head` through `20260319_0008`.
- Issues found:
  The first readiness implementation treated SQLite-returned naive timestamps as timezone-aware, which broke broker snapshot age calculations during tests. The readiness path was corrected by normalizing persisted timestamps to UTC before age math. Another hidden validation problem was that local Alembic usage had been blocked both by the package being absent and by repository naming overlap around `alembic`; fresh-upgrade validation was completed by installing Alembic and running it from a config that avoids the local path ambiguity.
- Reflection:
  This slice is important because it moves trading closer to an honest control surface. The system still does not have a full broker order path, but it can now say why autonomous trading is blocked, why it is degraded, and when reconciliation should force a halt. That is a much safer foundation than making session or broker assumptions implicitly.
- Next move:
  Continue Stage 9 into broker adapter abstraction, order intents, order records, position records, and portfolio-allocation guardrails, then connect those order-path controls back to strategy promotion policy.

## 2026-03-18 / Slice 11 / Stage 9 Governed Order Path

- Slice: Allocation policy, durable order path, paper broker adapter, and trading dashboard order visibility
- Date: 2026-03-18
- What changed:
  Added durable execution entities for `allocation_policy`, `order_intent`, `order_record`, and `position_record`, extended the execution service with governed order-intent submission and policy validation, introduced a paper broker adapter with immediate simulated fills, exposed allocation-policy/order/position APIs, and upgraded the trading dashboard to show allocation policy, recent order intents, recent order records, and active positions alongside the earlier readiness data. Bootstrap now creates a default paper allocation policy, and deployment env examples now include default broker/account/policy settings.
- What was validated:
  Passed `py -m pytest` with `36` tests. Passed `py -m compileall src tests alembic/versions`. Passed `npm run build` in `apps/dashboard-web`. Verified fresh SQLite Alembic `upgrade head` through `20260319_0009`.
- Issues found:
  The first order-path test failed because the default allocation policy was actually enforcing the intended 5% single-strategy notional cap, which surfaced that the original test order size was above policy. The test was corrected to stay inside the cap. A second hidden issue came from transaction timing: the projected broker snapshot was being recorded before newly created position rows were flushed, so the first snapshot incorrectly showed zero positions. That was fixed with an explicit flush before portfolio aggregation. A further realism gap was that projected paper snapshots were leaving cash and buying power unchanged after fills; the projection now recomputes those values from equity and active exposure so the dashboard tells a more honest story.
- Reflection:
  This slice matters because it turns Stage 9 from a safety perimeter into an actual governed execution lane. It is still paper-mode and still not a full external-broker integration, but the system can now accept a bounded order request, explain why it was rejected, persist the intent if it was accepted, record the resulting broker order, update durable position state, and show that whole chain to the owner.
- Next move:
  Continue Stage 9 into real broker adapters, cancel/replace flows, broker-order sync, and restart recovery for external execution state. Then connect broader portfolio policy and cross-strategy capital governance back into strategy-stage promotion rules.

## 2026-03-18 / Slice 12 / Stage 9 External Sync And Order Recovery

- Slice: External-style broker sync, cancel/replace lineage, restart recovery, and shared-account symbol guard
- Date: 2026-03-18
- What changed:
  Extended the broker abstraction so adapters can now submit, sync, cancel, and replace orders rather than only instant-fill them. Added durable `broker_sync_run` state, order-record lineage for `client_order_id`, `parent_order_record_id`, and `last_sync_run_id`, plus position sync lineage. Implemented execution-service methods and API endpoints for broker sync runs, cancel, and replace. Upgraded the trading dashboard to show the latest broker sync run and richer order lineage. Added a governance guard that rejects new orders when another strategy already holds the same symbol in the same broker account, preventing unsafe cross-strategy netting before sleeve attribution exists.
- What was validated:
  Passed targeted execution/API tests for async external-style order submission, restart recovery via broker sync, cancel, replace, dashboard exposure, and cross-strategy symbol-collision blocking. Passed full `py -m pytest -q` with `40` tests. Passed `py -m compileall src tests alembic/versions`. Passed `npm run build` in `apps/dashboard-web`. Passed fresh SQLite Alembic `upgrade head` through `20260320_0010`.
- Issues found:
  The first implementation had two subtle but important integrity problems. Replacement orders were initially reusing the prior client order id, which would have broken remote-to-local mapping on later sync. Also, broker sync notes were initially being appended in place on a JSON list, which SQLAlchemy would not reliably persist without mutable tracking. Both were fixed by issuing a fresh client order id per replacement intent and by collecting sync notes in a local list before assigning them back to the model.
- Reflection:
  This slice matters because real unattended trading does not fail only when an API call throws. It fails when a process restarts mid-flight, when an order is modified and history is lost, or when multiple strategies silently collide through one broker-level net position. The system now has a much stronger external-execution kernel: not yet a real broker adapter, but an honest recovery and governance shape that can support one safely.
- Next move:
  Implement one or more real broker adapters on top of the new sync/cancel/replace contract, add authenticated sync supervision loops, and connect broader portfolio ownership and sleeve attribution back into strategy promotion and capital policy.

## 2026-03-19 / Slice 13 / Stage 3 Owner Control Plane And Runtime Config Registry

- Slice: Durable runtime config registry, proposal/approval/revision flow, and Discord natural-language config control
- Date: 2026-03-19
- What changed:
  Added a durable runtime config registry that surfaces system policies, owner preferences, and supervisor loops as owner-visible configuration objects. Added runtime config proposals, approval-linked high-risk config changes, revision history, rollback proposal support, dashboard system-page cards for effective config and config history, new API endpoints for listing/proposing/applying config changes, and Discord natural-language routing for owner config reads and writes. Also cleaned up the owner-facing Chinese router/control-plane path so the most visible interaction layer is readable again.
- What was validated:
  Passed full `py -m pytest` with `45` tests. Passed `py -m compileall src`. Passed `npm run build` in `apps/dashboard-web`. Passed fresh SQLite Alembic `upgrade head` through `20260320_0011`.
- Issues found:
  The main hidden risk in this slice was fake configurability: it would have been easy to add config forms and proposal tables without wiring them into durable authority state. That was avoided by making supervisor-loop changes actually mutate the runtime loop records, by recording config revisions durably, and by forcing risky config changes through the existing approval system instead of inventing a second ungoverned bypass. Another practical issue was owner-facing text quality: earlier mojibake in the Chinese interaction path would have made the control plane feel broken even if the logic was right, so the router and control-plane strings were normalized while implementing the new flows.
- Reflection:
  This slice is product work, not just backend work. The system already had strong internal bones, but it still lacked a believable owner control surface. With a runtime config registry, approval-backed config changes, and dashboard-visible config history, the system is much closer to something a non-technical owner can actually govern from Discord and the dashboard.
- Next move:
  Finish the rest of Stage 3 and Stage 11 productization by adding Discord operator security defaults, richer approval ergonomics, onboarding/doctor-style checks, backup and restore flows, and VPS deployment runbooks. Then continue into real broker adapters and governed auto-evolution completion.

## 2026-03-19 / Slice 14 / Stage 11 Productization Doctor Surface

- Slice: Deployment-time doctor checks for VPS readiness and operator troubleshooting
- Date: 2026-03-19
- What changed:
  Added a new `DoctorService`, a `python -m quant_evo_nextgen.runner.doctor` CLI entrypoint, and an `/api/v1/system/doctor` API endpoint. The doctor surface now checks runtime database reachability, Alembic head revision visibility, workspace writability, Discord configuration, Codex/relay configuration, and runtime registry readability. This gives the system a first real productization self-check rather than requiring the owner to infer health from scattered logs.
- What was validated:
  Passed the full `py -m pytest` suite with `48` tests including new doctor coverage and API-level doctor validation. Passed `py -m compileall src`. Passed `npm run build` in `apps/dashboard-web`. Confirmed Alembic `upgrade head` through `20260320_0011`. Confirmed the doctor CLI returns a fully green JSON report under a seeded local SQLite runtime with relay and Discord settings present.
- Issues found:
  The first version assumed `alembic_version` would always exist, but local `create_schema()` bootstrap paths do not record migration lineage. The doctor now reports missing revision lineage as a warning rather than a false hard failure, while still requiring the expected head revision for a truly green status.
- Reflection:
  This slice is small compared with trading or Codex, but it is exactly the kind of productization detail that determines whether a non-technical operator can actually run the system on a VPS. A system that cannot explain why it is unhealthy is much harder to own than a system that lacks one more experimental feature.
- Next move:
  Continue Stage 11 with backup/restore, deployment runbooks, and safer Discord operator security defaults so the productization layer catches up with the runtime core.

## 2026-03-20 / Slice 15 / Stage 9 Multi-Instrument Domain Foundation

- Slice: Canonical instrument registry, broker capability registry, and product-aware order semantics foundation
- Date: 2026-03-20
- What changed:
  Added durable `instrument_definition` and `broker_capability` execution entities, plus new service and API flows for upserting and listing them. Extended order intents, order records, and position records with canonical instrument lineage and `position_effect`. Taught the execution service to auto-register equity-like instruments, require canonical option instruments, and reject unsupported product paths before calling the broker adapter. Fixed broker sync so recovered positions no longer default silently to `equity`, and added bootstrap broker capability seeding for the default paper broker path.
- What was validated:
  Passed targeted `py -m pytest tests/test_execution_service.py tests/test_doctor.py tests/test_api_persistence.py -q` with `22` tests. Passed full `py -m pytest -q` with `52` tests. Passed `py -m compileall src tests alembic/versions`. Passed `npm run build` in `apps/dashboard-web`. Passed fresh SQLite Alembic `upgrade head` through `20260320_0012`.
- Issues found:
  A hidden SQL semantics bug surfaced during the capability work: the earlier fallback pattern using `IN (..., NULL)` does not actually match `NULL` rows reliably, which would have broken provider/account-scoped fallback for global policy and capability records. The execution service was corrected to use explicit `column == value OR column IS NULL` fallback logic instead. Another integrity gap was that the old sync path hardcoded new synced positions as `equity`; that was corrected by carrying asset type through `PositionState`.
- Reflection:
  This slice does not complete options, short, or leverage trading, but it removes a major structural blocker. The system can now describe what an instrument is, what a broker/account can really do, and when an order is invalid because the product semantics do not line up. That is the necessary foundation for honest multi-instrument execution rather than a collection of misleading string fields.
- Next move:
  Continue Stage 9 into full multi-instrument paper execution and the first instrument-aware risk engine, then connect that richer trading substrate back into strategy promotion policy and Discord/dashboard operator visibility.

## 2026-03-20 / Slice 16 / Stage 9 Paper Short Lifecycle Closure

- Slice: Paper-mode short open, cover, and flip lifecycle closure
- Date: 2026-03-20
- What changed:
  Extended the paper broker adapter so `buy` orders against active short positions now perform partial cover, full cover, and overshoot flip-to-long behavior instead of failing through a long-only averaging branch. Tightened execution validation so short increases require both allocation-policy permission and broker-capability permission, and corrected gross-exposure projection for buy-to-cover flows. Added a new execution-service regression test that walks the whole short -> partial cover -> flip to long lifecycle.
- What was validated:
  Passed targeted `py -m pytest tests/test_execution_service.py -q` with `11` tests. Passed full `py -m pytest -q` with `53` tests. Passed `py -m compileall src tests`.
- Issues found:
  The hidden issue here was not only adapter logic but portfolio math. Without fixing projected gross exposure for buy-to-cover flows, the policy layer would have continued to treat some de-risking buys as risk increases. That projection logic was corrected alongside the adapter.
- Reflection:
  This slice still does not make live short trading production-ready because borrow availability and broker-specific short mechanics are missing. But it does remove a misleading gap in paper mode: the governed execution path can now actually test a closed short lifecycle instead of only opening shorts and then getting stuck on the way out.
- Next move:
  Continue the multi-instrument paper closure into option lifecycle simulation and the first margin-aware risk controls, then carry those new semantics into real broker adapter selection and strategy-stage promotion rules.

## 2026-03-20 / Slice 17 / Stage 9 Single-Leg Option Paper Closure

- Slice: Single-leg long option paper execution, multiplier-aware notional, and first leverage-aware sizing logic
- Date: 2026-03-20
- What changed:
  Extended the paper execution path to support single-leg long option `buy/open` and `sell/close` flows. Added contract-multiplier-aware notional calculation, position market value calculation, and unrealized/realized PnL accounting. Tightened option validation so option orders require explicit position effect and reject unsupported short-option paths. Adjusted sizing logic so strategy caps and projected exposure become leverage-aware for leveraged ETF style instruments while still using actual premium notional for single-leg options. Corrected the cap logic so close/reduce orders are not falsely blocked by open-position sizing limits, and added a broker buying-power check that only applies to exposure-increasing flows.
- What was validated:
  Passed targeted `py -m pytest tests/test_execution_service.py -q` with `13` tests. Passed full `py -m pytest -q` with `55` tests. Passed `py -m compileall src tests alembic/versions`. Passed `npm run build` in `apps/dashboard-web`.
- Issues found:
  Two hidden issues surfaced during the option pass. First, naive sizing checks were incorrectly treating closing trades like new exposure, which would have blocked profitable option exits; that was corrected by separating exposure-increasing orders from reduce/close orders. Second, option premium notional and PnL had initially still been equity-shaped, which would have undercounted risk and returns by the contract multiplier; multiplier-aware helpers were added across execution and paper position updates.
- Reflection:
  This slice still does not make options production-complete, because there is no multi-leg structure, expiry lifecycle, assignment, or exercise handling yet. But it does change the system materially: options are no longer just labeled strings that get rejected. The governed paper path can now open and close a real single-leg long option position and account for it honestly.
- Next move:
  Continue Stage 9 into multi-leg option structure, expiry and assignment handling, and the first real margin-mode risk rules before moving into a production-grade broker adapter.

## 2026-03-20 / Slice 18 / Stage 9 First Margin-Mode And Leverage-Aware Risk Pass

- Slice: Cash-vs-margin buying-power checks and leverage-aware strategy sizing
- Date: 2026-03-20
- What changed:
  Deepened the first instrument-aware risk pass so non-margin accounts now validate exposure increases against available cash, while margin-capable modes validate against broker buying power. Short openings and short increases now explicitly require margin-capable broker/account configuration in addition to short permission. Leveraged ETF style instruments now consume strategy-cap space more conservatively through leverage-aware notional weighting. Added a regression test for leverage-weighted strategy caps and updated the option buying-power regression to assert the non-margin cash path.
- What was validated:
  Passed targeted `py -m pytest tests/test_execution_service.py -q` with `14` tests. Passed full `py -m pytest -q` with `56` tests. Passed `py -m compileall src tests alembic/versions`.
- Issues found:
  The hidden issue in this pass was that earlier buying-power validation treated all accounts as if buying power were the only scarce resource, which is not true for cash-style option paths. That would have made paper and future live behavior diverge in subtle ways. The validation now distinguishes account mode more honestly, even though full maintenance-margin modeling is still pending.
- Reflection:
  This is still not a complete margin engine, because maintenance margin, liquidation thresholds, borrow fees, and locate availability are not yet modeled. But it does move the system away from generic equity-era checks toward product-aware and account-aware capital validation.
- Next move:
  Continue into multi-leg option structure, expiry and assignment handling, and richer short/margin state before selecting and closing the first real broker adapter.

## 2026-03-20 / Slice 19 / Stage 9 Order-Leg And Option-Lifecycle Foundation

- Slice: Durable order-leg structure, durable option lifecycle events, expiration application, and option-aware dashboard visibility
- Date: 2026-03-20
- What changed:
  Added a new durable `exec_order_leg` model so governed orders can retain explicit per-leg structure rather than flattening every product into one symbol/side pair. Extended order intent and order record summaries to expose leg counts and nested leg detail. Added a new durable `exec_option_lifecycle_event` model plus service and API flows for recording and listing option expiration, exercise, and assignment events. Implemented automatic expiration application for active option positions so expired contracts now close durably and realize premium loss instead of remaining silently active. Added review-required handling for non-expiration option events, including incident creation so unsupported assignment/exercise paths become visible risk rather than invisible drift. Extended the trading dashboard and frontend to surface expiring option positions, recent option lifecycle events, and richer product metadata on orders and positions.
- What was validated:
  Passed targeted `py -m pytest tests/test_execution_service.py tests/test_api_persistence.py tests/test_doctor.py -q` with `29` tests. Passed full `py -m pytest -q` with `59` tests. Passed `py -m compileall src tests alembic/versions`. Passed `npm run build` in `apps/dashboard-web`. Passed fresh SQLite Alembic `upgrade head` through `20260320_0013`.
- Issues found:
  The first hidden regression was that `replace_order()` still called the old validation signature, which would have broken external-style order management after the new order-leg-aware validation was introduced; replacement flows were updated to synthesize and persist leg structure too. Another hidden design trap was pretending assignment and exercise were fully automated before the engine could honestly transform those events into underlying positions. Instead of faking completeness, the system now records those events durably, marks them `review_required`, and opens an incident so governance can see that the event happened and that automation still has a gap there.
- Reflection:
  This slice matters because deployability is not just about whether the engine can place a trade. It is also about whether the owner can see complex structure and lifecycle risk before live deployment. Durable legs and option lifecycle events turn previously implicit product semantics into auditable state, which is the prerequisite for closing real broker parity and long-running autonomous governance.
- Next move:
  Continue Stage 9 into true multi-leg execution semantics, automatic assignment/exercise state application, richer short-borrow and maintenance-margin modeling, and then use those foundations to close the first real broker adapter.

## 2026-03-20 / Slice 20 / Stage 3 Discord Access Hardening

- Slice: Trusted-operator allowlists, channel-boundary enforcement, and clean Chinese owner interaction
- Date: 2026-03-20
- What changed:
  Added a new Discord access policy layer that enforces trusted operator user allowlists and separates control-channel actions from approval-channel actions. Extended settings and `.env.example` with Discord channel IDs and trusted user allowlist inputs, bootstrapped a new `discord_access` owner preference snapshot, and updated the Discord doctor check so a configured bot without an allowlist is no longer reported as fully green. Rewrote the Discord shell and control-plane owner-facing Chinese strings to remove mojibake and make the owner interaction surface readable again.
- What was validated:
  Passed targeted `py -m pytest tests/test_control_plane.py tests/test_discord_access.py tests/test_doctor.py tests/test_api_persistence.py -q` with `19` tests. Passed full `py -m pytest -q` with `62` tests. Passed `py -m compileall src tests`. Passed `npm run build` in `apps/dashboard-web`.
- Issues found:
  The hidden risk here was false green health: the earlier doctor would mark Discord as healthy as soon as token and channel names existed, even though an unbounded bot surface is not safe enough for unattended deployment. Another practical issue was owner trust. The interaction path still had visible Chinese text corruption, which would have made the IM layer feel broken and hard to manage even if the persistence logic underneath was correct.
- Reflection:
  This slice is small compared with broker execution, but it matters for real ownership. A system meant to run unattended on VPS still needs a bounded human control plane, especially for a non-technical owner. Trusted-user allowlists and clear owner-facing language are part of product safety, not just polish.
- Next move:
  Continue Stage 3 and Stage 11 into richer approval ergonomics, pairing/onboarding flows, backup and restore drills, and VPS runbooks, while Stage 9 continues toward real broker closure and full multi-instrument execution parity.

## 2026-03-20 / Slice 21 / Stage 9 First Real Broker Closure

- Slice: First real Alpaca adapter, authenticated broker sync, capability seeding, and supervised broker-truth refresh
- Date: 2026-03-20
- What changed:
  Added a first real `alpaca` broker adapter that supports authenticated submit, sync, cancel, and replace flows through the existing broker abstraction. Added conservative request guards so unsupported option-short or product paths are rejected explicitly rather than being half-normalized. Added Alpaca account capability seeding so durable broker capability records can now reflect actual short, margin, and option permissions derived from broker account truth. Added a new active `broker-state-sync` supervisor loop so external broker truth can refresh automatically instead of depending on manual sync calls.
- What was validated:
  Passed targeted `py -m pytest tests/test_alpaca_broker.py tests/test_doctor.py tests/test_supervisor.py tests/test_state_store.py -q` with `15` tests. Passed full `py -m pytest -q` with `70` tests. Passed `py -m compileall src tests alembic/versions`. Passed `npm run build` in `apps/dashboard-web`.
- Issues found:
  The main hidden integrity risk was not HTTP wiring but durable-state corruption. Alpaca position payloads do not carry the same realized-PnL semantics as the internal position model, and broker asset-class values do not distinguish ETFs from single-name equities precisely enough for the existing internal taxonomy. The sync path was therefore hardened to preserve locally known ETF-like asset types when broker classification is generic and to avoid overwriting realized PnL when the broker payload cannot honestly provide it.
- Reflection:
  This slice closes an important honesty gap. The system is no longer only simulating what a real external broker contract might look like. It now has an actual authenticated broker path plus an automatic sync loop, while still refusing to pretend that multi-leg options, assignment, exercise, or full margin semantics are already solved.
- Next move:
  Continue Stage 9 into multi-leg execution, automatic assignment/exercise application, roll handling, and richer short-borrow plus maintenance-margin modeling.

## 2026-03-20 / Slice 22 / Stage 11 VPS Productization Assets

- Slice: Production compose stacks, migration-ready backend image, backup/restore scripts, systemd units, and VPS runbook
- Date: 2026-03-20
- What changed:
  Added production `2 VPS` compose stacks under `ops/production/core` and `ops/production/worker`, plus Core and Worker env templates. Added `ops/bin` scripts for Core bring-up, shutdown, smoke checks, backup, and restore. Added Linux systemd units for the Core and Worker roles. Updated the backend Docker image to include Alembic configuration and migration files so production deployment can run `alembic upgrade head` inside the application image. Added a concrete `docs/next-gen/VPS-DEPLOYMENT-RUNBOOK.md` so deployment, backup, restore, and break-glass steps live in one place.
- What was validated:
  Passed full `py -m pytest -q` with `70` tests. Passed `py -m compileall src tests alembic/versions`. Passed `npm run build` in `apps/dashboard-web`. Passed fresh Alembic `upgrade head` through `20260320_0013`. Confirmed the backend image definition now includes Alembic assets required by the new bring-up script.
- Issues found:
  The important hidden issue here was migration realism. The earlier backend image could run the API but not Alembic, which would have made a scripted production upgrade path look complete while failing at the exact moment schema safety matters. That gap was closed by packaging Alembic into the image before writing the production bring-up scripts.
- Reflection:
  This slice moves the project materially closer to a real VPS deployment path. The system still needs an actual Linux deploy drill and restore drill before it can be called fully production-ready, but the repo now contains concrete operational assets rather than only architecture notes.
- Next move:
  Run the first real Core/Worker VPS drill, exercise backup and restore on Linux, then close the remaining high-risk trading semantics before any live-capital promotion path is enabled.

## 2026-03-20 / Slice 23 / Stage 9 Broker Hardening And Stage 11 Deployment Closure Pass

- Slice: Alpaca normalization hardening, deployment asset correction, and migration-aware VPS packaging
- Date: 2026-03-20
- What changed:
  Hardened the first real Alpaca adapter so sync now preserves option contract-multiplier semantics in durable normalization, preserves locally known ETF-like asset types when the broker payload is generic, and avoids overwriting realized PnL when the external payload cannot honestly provide it. Extended doctor coverage to fail fast when the default broker adapter is Alpaca without matching credentials, and added dedicated adapter plus supervisor regression tests. On the deployment side, packaged Alembic assets into the backend container, added `ops/production/core` and `ops/production/worker` compose stacks plus env templates, added migration-aware bring-up, smoke-check, backup, and restore scripts, and added Linux systemd service units plus owner-facing runbooks.
- What was validated:
  Passed targeted `py -m pytest -q tests/test_alpaca_broker.py tests/test_doctor.py tests/test_execution_service.py tests/test_supervisor.py tests/test_state_store.py` with `39` tests. Passed full `py -m pytest -q` with `70` tests. Passed `py -m compileall src tests alembic/versions`. Passed `npm run build` in `apps/dashboard-web`. Passed fresh Alembic `upgrade head` through `20260320_0013`.
- Issues found:
  The main hidden risks in this pass were assumption mismatches rather than syntax issues. Broker payloads can be more ambiguous than the internal model, so sync logic had to avoid clobbering locally known context with weaker broker classifications. On the deployment side, the important realism gap was migration packaging: an API image that cannot run Alembic would make a scripted VPS deploy look complete while failing at schema-upgrade time. The backend image and bring-up path were aligned to close that gap.
- Reflection:
  This pass did not add flashy new trading features, but it materially reduced the chance of operational self-deception. A system like this fails in production more often from mismatched assumptions than from obvious syntax errors. Tightening broker normalization, preserving honest durable state on sync, and aligning deployment assets with the actual repo layout all improve survivability and owner trust.
- Next move:
  Run a real Linux Core/Worker deploy drill, then continue Stage 9 into automatic assignment/exercise application, multi-leg execution, and deeper borrow plus maintenance-margin modeling before claiming true pre-live closure.

## 2026-03-20 / Slice 24 / Stage 11 Productization Correction And Operator Entry-Point Cleanup

- Slice: Corrected production asset layout, fixed compose env propagation, added node-boundary doctor checks, and replaced the misleading root README
- Date: 2026-03-20
- What changed:
  Added a concrete canonical production layout under `ops/production`, `ops/systemd`, and `ops/bin` for the recommended Core plus Worker `2 VPS` deployment shape. Added Core/Worker compose files, env templates, Linux systemd units, backup, restore, smoke-check, safe-mode, and upgrade scripts, plus concrete runbooks for deployment, backup/restore, break-glass, and owner quickstart. Fixed a high-risk deployment bug where Compose `--env-file` values would have been used only for CLI interpolation rather than being injected into the application containers, by explicitly wiring service-level `env_file` entries into the production compose stacks. Extended doctor again so a worker node carrying Alpaca broker secrets or an external broker adapter now fails fast instead of looking healthy. Replaced the root `README.md` so the repo now points operators at the next-gen runtime and runbooks instead of the archived OpenClaw bootstrap flow.
- What was validated:
  Passed full `py -m pytest -q` with `70` tests. Passed `py -m compileall src tests alembic/versions`. Passed `npm run build` in `apps/dashboard-web`. Confirmed new doctor boundary coverage through `tests/test_doctor.py`. Docker and Bash were not installed in the current workstation environment, so live `docker compose` execution and shell-script runtime execution could not be exercised here.
- Issues found:
  The most important hidden issue was configuration illusion. Without explicit Compose `env_file` entries, the production stacks would have looked correctly configured from the shell while the containers themselves still missed Discord, OpenAI, broker, and database settings. Another high-risk usability issue was the root README itself: it still described the legacy OpenClaw system, which would have sent a non-technical owner down the wrong deployment path even if the next-gen runtime underneath was correct.
- Reflection:
  Productization failures are often entry-point failures rather than algorithm failures. Correcting the repo entrypoint, wiring env propagation honestly, and making doctor enforce node-role trust boundaries does not finish the whole autonomous investing problem, but it does materially reduce the chance of an operator deploying the wrong thing or leaking the wrong secret onto the wrong box.
- Next move:
  Run a real Linux Core/Research deployment drill with the new `ops/` assets, execute a restore rehearsal, and then continue the trading-domain closure work around assignment, exercise, multi-leg options, and deeper margin/borrow semantics.

## 2026-03-20 / Slice 25 / Stage 9 Lifecycle Closure Pass And Stage 11 Canonical Ops Cleanup

- Slice: Automatic single-leg exercise and assignment application, canonical ops-path cleanup, and owner-facing deploy path consolidation
- Date: 2026-03-20
- What changed:
  Extended option lifecycle handling so capability-backed single-leg `exercise` and `assignment` events can now close the option position and transform durable state into the underlying equity position automatically when the broker capability allows it and the underlying symbol is not already controlled by another strategy. Preserved the conservative fallback by keeping unsupported or conflicting cases on the review-required path with incidents. On the operations side, removed the stale parallel deployment entrypoints, added a symmetric `worker-down.sh`, corrected the systemd templates to the canonical `/opt/quant-evo-nextgen` root, and rewrote the root README plus VPS, backup/restore, and break-glass runbooks so the repo now exposes one honest deployment path instead of multiple conflicting ones.
- What was validated:
  Passed targeted `py -m pytest -q tests/test_execution_service.py -k "exercise or assignment or expiration"` with `3` tests. Passed full `py -m pytest -q` with `72` tests. Passed `py -m compileall src tests alembic/versions`. Passed `npm run build` in `apps/dashboard-web`. Re-ran stale-reference searches so owner-facing docs and ops assets no longer point at the removed legacy deployment path.
- Issues found:
  Two hidden risks surfaced in this pass. The first was silent state corruption during option conversion: auto-applying assignment or exercise without checking strategy ownership of the underlying symbol could have bypassed the cross-strategy collision guard. The new conversion path now refuses those conflicted cases and falls back to review-required incidents instead of silently mutating another strategy's book. The second risk was productization drift: even with correct code, leaving an older parallel deployment path active in the repo would have made a non-technical owner follow the wrong deployment steps and believe incompatible assets were interchangeable.
- Reflection:
  This slice matters because survivability comes from both domain honesty and operator honesty. Automatic lifecycle handling improves the trading engine only if it does not break portfolio ownership semantics, and deployment assets help only if there is one path the owner can actually trust. Tightening both sides together makes the system meaningfully closer to a credible VPS-ready paper or controlled-live posture.
- Next move:
  Run a real Linux Core plus Worker deployment drill, then continue Stage 9 into multi-leg options, broader short-option semantics, and deeper margin/borrow closure before claiming a truly pre-live-complete system.

## 2026-03-19 / Slice 26 / Stage 10 Governance Closure And IM-Layer Repair

- Slice: Closed the Stage 10 schema and API gap, and repaired owner-facing Chinese IM interaction quality
- Date: 2026-03-19
- What changed:
  Added durable evolution-governance coverage end to end: new Alembic revision `20260320_0014`, new proposal/canary/promotion persistence tests, new service-level evolution tests, and dashboard/API validation for recent proposals, canary runs, promotion decisions, and aggregate metrics. Repaired the Discord/control-plane Chinese text layer by rewriting the router, control-plane responses, and Discord slash-command descriptions into clean UTF-8 Chinese. Added router regression tests so Chinese status, approval, config-change, and config-rollback commands are parsed intentionally instead of only incidentally.
- What was validated:
  Passed targeted `py -m pytest -q tests/test_router.py tests/test_control_plane.py tests/test_api_persistence.py tests/test_evolution_service.py tests/test_doctor.py` with `27` tests. Passed `py -m compileall src tests alembic/versions`. Passed fresh SQLite Alembic `upgrade head` through `20260320_0014`. Passed full `py -m pytest -q` with `85` tests. Passed `npm run build` in `apps/dashboard-web`.
- Issues found:
  The main hidden risk was false closure. Stage 10 had UI and contract scaffolding, but without migration lineage and persistence coverage it could not honestly be treated as deploy-ready. A second hidden issue was owner trust: the IM layer still contained mojibake text, which would have made the Discord-first operating model feel broken even when the backend state machine was working.
- Reflection:
  This slice improved both governance honesty and owner usability. Durable self-improvement records matter because they make promotion and rollback discussable and auditable. Clean Chinese owner interaction matters because a Discord-first control surface is part of the safety boundary for a non-technical operator, not just product polish.
- Next move:
  Continue the remaining non-deploy closure work where the honest blockers still are: multi-leg and broader short-option execution semantics, deeper borrow plus margin modeling, richer owner onboarding flows, and automatic bounded evolution actuation rather than only durable governance records.

## 2026-03-19 / Slice 27 / Stage 10 Proposal Sync And Active Strategy Evaluation

- Slice: Activated governed strategy-evaluation by default and added supervisor-driven Codex-to-evolution proposal sync
- Date: 2026-03-19
- What changed:
  Promoted `strategy-evaluation` into an active default supervisor loop with bounded Codex budget controls. Added a new active `evolution-governance-sync` supervisor loop that scans completed `strategy-evaluation` and `council-reflection` Codex runs, deduplicates by `codex_run_id`, and materializes durable evolution proposals automatically with review-ready metadata, canary plans, rollback plans, and objective-drift checks. Extended the evolution service with `find_proposal_by_codex_run_id`, wired the supervisor runner to construct `EvolutionService`, and added supervisor regression coverage for automatic proposal creation.
- What was validated:
  Passed targeted `py -m pytest -q tests/test_supervisor.py tests/test_evolution_service.py tests/test_router.py tests/test_control_plane.py` with `14` tests. Passed `py -m compileall src tests alembic/versions`. Passed fresh SQLite Alembic `upgrade head` through `20260320_0014`. Passed full `py -m pytest -q` with `86` tests. Passed `npm run build` in `apps/dashboard-web`.
- Issues found:
  The key hidden risk was that Stage 10 could still look active while depending on manual record creation. Without an ingestion path from bounded Codex loops into governed proposal records, auto-evolution would remain mostly cosmetic. Another hidden risk was unbounded token churn, so the newly active strategy-evaluation loop was given conservative duration, iteration, token, and queue-pressure budgets instead of being turned loose at the same settings as research intake.
- Reflection:
  This slice does not finish autonomous self-improvement, but it changes the shape of the system in an important way: completed bounded reflection can now become explicit governed work items automatically. That is a more honest foundation for unattended evolution than a dashboard page that only waits for manual proposal entry.
- Next move:
  Keep pushing the same chain deeper: automatic proposal generation is now present, but automatic canary actuation, rollback execution, promotion gating, and objective-drift enforcement still need to be closed before Stage 10 can be called complete.

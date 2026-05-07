# DAILY_SCAN_RESULT - explorer

- timestamp_utc: 2026-03-03T16:12:00Z
- cadence: daily + intraday updates
- search_provider: searxng (policy default; this cycle used local-evidence continuity due no fresh external fetch requirement)
- query_scope: strategy + stock_selection + domain_news + openclaw_capability

## new_findings
1. **Strategy**: In the latest adaptive fast-mutation set, `variant_mr_pullback` is the only positive quick result; momentum/event variants are negative and require threshold relaxation.
2. **Stock_selection**: For same-day paper execution, preference remains liquid mega-caps aligned with MR logic (`AAPL`, `AMZN`, `META`) until breakout/event variants recover edge.
3. **Domain_news**: Patch-based time-series modeling (PatchTST) remains a practical feature-engineering direction for short-horizon signal quality under noisy regimes.
4. **OpenClaw_capability**: QMD default memory backend rollout is in place, enabling continuity-first retrieval before synthesis.

## actionable_signal
- Execute paper-only priority ladder:
  - Tier-1: MR pullback logic on `AAPL/AMZN/META` (reduced size, strict stop).
  - Tier-2: Keep momo/event variants in observe mode (no promotion to execution basket yet).
- Entry profile (MR): pullback to MA + low RSI + mild volume confirmation.

## risk_note
- No blind overreaction: keep global hard-limits unchanged.
- Current 5d quick validations have low trade counts; treat confidence as provisional.
- For intraday rollout, enforce reduced sizing and require live confirmation before any expansion.

## next_experiment
1. Run 20d fast backtests for the same 3 variants to increase sample size and stabilize Sharpe/PF estimates.
2. Relax breakout/event thresholds incrementally to target `trade_count >= 20` while preserving MDD guard.
3. Add event-score as position-scaling (not hard filter) and compare against baseline MR basket.

## evidence
- strategy variants + metrics: `trading/logs/adaptive_basket_20260303_1451_variants.md`
- prior reflection delta: `memory/reflections/reflection_20260303_1022_learning_cycle.md`
- domain research anchor: `knowledge/papers/paper_20260302_patchtst_for_short_horizon_alpha.md`
- capability rollout anchor: `trading/logs/qmd_default_rollout_20260302.md`

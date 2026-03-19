# Evolver Behavior Rules

## Cycle Mode Selection

At the start of each micro-cycle, select the mode for this round:

### Mode A — Strategy Discovery (default, ~60% of cycles)
Standard flow: Explorer proposes new hypothesis → Critic challenges → Evolver adjudicates → backtest.

### Mode B — Strategy Optimization (~15% of cycles)
Triggered when any production/staging strategy has:
- Rolling 30d Sharpe < 0.5, OR
- 3+ consecutive losing days, OR
- Significant regime change detected (VIX spike, correlation breakdown)

Flow: Explorer diagnoses underperforming strategy → proposes improvement → Critic evaluates regression risk → Evolver A/B tests improved vs original.

### Mode C — Capability Evolution (~25% of cycles, minimum 3 per day)
The system improves its own abilities — not limited to trading.

Flow: Explorer freely chooses a self-improvement direction → researches via web search → proposes improvement → Critic evaluates → Evolver decides whether to adopt.

**Mode selection logic:**
1. If any production strategy triggers Mode B conditions → next cycle is Mode B
2. Else if fewer than 3 Mode C cycles have run today → next cycle is Mode C
3. Else → Mode A

Post the selected mode in `CYCLE_TRIGGER`:
```json
{
  "type": "CYCLE_TRIGGER",
  "mode": "strategy_discovery | strategy_optimization | capability_evolution",
  "cycle_id": "cycle_YYYYMMDD_HHMM",
  "context": { ... }
}
```

---

## Micro-Cycle (Every 2 Hours)

### Mode A & B: Strategy Cycles

#### 1. Adjudication Phase (T+45~65min)
Read the debate in `#a-arena`, produce verdict to `#a-verdict`:

```json
{
  "hypothesis_id": "hyp_YYYYMMDD_HHMM",
  "verdict": "APPROVE | REJECT | REVISE",
  "confidence": 0.0-1.0,
  "reasoning": "Detailed reasoning citing key arguments from both sides",
  "alpha_argument_score": 0.0-1.0,
  "risk_argument_score": 0.0-1.0,
  "conditions": ["If APPROVE, attached conditions"],
  "next_action": "backtest | archive | revise"
}
```

Adjudication principles:
- confidence < 0.6 -> force REVISE
- When both sides are evenly matched -> lean toward Critic (conservative)
- Consider Feature Map diversity contribution (bonus for filling blank regions)
- Mode B only: improved version must beat original on at least 2 of 3 metrics (Sharpe, DD, Win Rate)

#### 2. Backtest Phase (T+65~80min, when APPROVE)
- Convert the strategy hypothesis into executable code
- Run backtest: most recent 30 days of intraday data (standard) or 1 year of event data (event-driven/alt-data)
- Evaluate: Sharpe, Max Drawdown, Win Rate, Profit Factor, Average Holding Period, Signal Decay Rate
- Mode B: run A/B comparison backtest (improved vs original, same period)

#### 3. Wrap-Up Phase (T+80~90min)
- Backtest passed: commit strategy to `strategies/candidates/`, update `evo/feature_map.json`
- Backtest failed: generate causal reflection to `memory/causal/`
- REJECT: record to `memory/reflections/`
- Publish cycle report to `#a-report`

### Mode C: Capability Evolution Cycle

#### 1. Evaluation Phase (T+45~65min)
Read Explorer's improvement proposal and Critic's assessment in `#a-arena`.

#### 2. Decision Phase (T+65~80min)
- If the improvement is testable (e.g., new search technique): design a quick validation test
- If it's a process change: approve for 1-day trial
- If it's a knowledge acquisition: evaluate whether the learned knowledge is actionable

#### 3. Adoption Phase (T+80~90min)
- Approved improvements: commit to `memory/architecture/capabilities/`
- Record what was learned, how it was validated, and expected impact
- If the improvement involves config changes, propose them for admin review
- Publish capability evolution report to `#a-report`

---

## Synthesis Cycle (Every 6 Hours)

Replaces the old "daily cycle." Runs 4 times per day.

1. Aggregate micro-cycle results from the past 6h
2. Analyze Feature Map coverage changes
3. Read System B performance (`trading/metrics/`)
4. **Cross-Strategy Signal Analysis**: Identify cases where multiple strategies fired on the same ticker. Log to `memory/principles/confluence/`
5. **Strategy Combination Discovery**: If two approved strategies have low correlation but complementary signals, propose a combined strategy for the next exploration cycle
6. **Principle Synthesis**: Read `memory/causal/` and `memory/reflections/` from the past 6h. Identify recurring patterns (≥2 similar failures = pattern). Synthesize into `memory/principles/`
7. Generate synthesis report to `#a-report`
8. Commit to `evo/cycles/synthesis-YYYY-MM-DD-HH.json`

---

## Evolution Cycle (Daily, ~22:00 EST)

Replaces the old "weekly cycle." Runs every day.

1. Aggregate all synthesis reports for the day
2. **Critic Threshold Review**: Count false-negatives and false-positives. If false-negative > 30%: suggest Critic lower thresholds. If false-positive > 40%: suggest Critic raise thresholds.
3. **Meta-Reflection**: Total debates, verdict distribution, debate quality, Explorer win rate, Critic override rate, Mode C adoption rate. Distinguish skill vs luck outcomes.
4. **Architecture Debate**: Trigger in `#a-arena` with `mode: "architecture"`. Scope: any system-level improvement (not limited to trading). Explorer proposes, Critic challenges, Evolver arbitrates. Output: `ARCHITECTURE_VERDICT` with prioritized actionable items.
5. **Capability Evolution Review**: Review all Mode C outcomes from today. Which improvements were adopted? Which failed? What should be explored tomorrow?
6. Generate daily evolution report to `#a-report`
7. Commit to `memory/architecture/`

---

## Trigger Next Round

After each cycle report, post `CYCLE_TRIGGER` to `#a-arena` with:
- Selected mode for next cycle
- Context (Feature Map gaps, underperforming strategies, capability evolution priorities)
- For Mode C: suggested exploration directions (but Explorer has full autonomy to choose differently)

---

## 2h Report Format

Note: Reports to admin should be written in Chinese (中文).

```
📊 微循环报告 #NNN | YYYY-MM-DD HH:MM | 模式: A/B/C

[模式A/B]
假设: [hypothesis_id]
裁决: APPROVE/REJECT/REVISE (confidence: 0.XX)
回测: Sharpe X.XX | MaxDD X.X% | WinRate XX%
Feature Map: 覆盖率 X.XX% (+X cells)

[模式C]
方向: [improvement direction]
结果: ADOPTED/REJECTED/TRIAL
学到: [one-sentence summary]

累计今日: N 轮完成 (A:X B:X C:X), M 策略通过, K 能力提升
```

---

## REVISE Workflow

When issuing a REVISE verdict:
1. Post `REVISE_REQUEST` to `#a-arena` with specific issues and suggested direction
2. Wait for Explorer's `REVISED_HYPOTHESIS` (10min timeout)
3. Wait for Critic's `RISK_ASSESSMENT (revision)` (8min timeout)
4. Issue `FINAL_VERDICT` (APPROVE or REJECT only — no second REVISE)
5. If total cycle time would exceed 2h, skip REVISE and force REJECT

## Extended Debate

If both `alpha_argument_score` and `risk_argument_score` are between 0.55-0.75:
- Post `EXTEND_DEBATE` to `#a-arena` with `extra_rounds: 1`
- Wait for one additional Explorer-Critic exchange
- Then issue verdict as normal
- Maximum total rounds: 3 (hard cap)

## Constraints
- A verdict must be produced every round; "pending" is not allowed
- Do not push strategies without running a backtest first
- Feature Map updates must be atomic (read-modify-write-commit)
- All reports must include quantifiable metrics
- Mode C cycles must produce at least one actionable insight (even if the proposal is rejected, document what was learned)

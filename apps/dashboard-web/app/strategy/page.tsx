import {
  createStrategySpecAction,
  recordBacktestAction,
  recordPaperRunAction,
  recordPromotionDecisionAction,
  runFactorReplayBacktestAction,
} from "@/app/actions";
import { fetchStrategyLifecycle } from "@/lib/dashboard";
import type { StrategyHypothesisCard, StrategySpecCard } from "@/lib/types";

type StrategyPageProps = {
  searchParams?: Promise<{
    strategy?: string;
    code?: string;
  }>;
};

function toneClass(value: string): string {
  if (value === "passed" || value === "approved") {
    return "tone-good";
  }
  if (value.includes("reject") || value === "failed") {
    return "tone-bad";
  }
  if (value.includes("pending") || value === "deferred" || value === "needs") {
    return "tone-warn";
  }
  return "";
}

function message(status?: string, code?: string): string | null {
  switch (status) {
    case "spec_created":
      return "Strategy spec created.";
    case "backtest_recorded":
      return "Backtest result recorded.";
    case "factor_backtest_recorded":
      return "Factor replay backtest recorded.";
    case "paper_recorded":
      return "Paper run recorded.";
    case "promotion_approved":
      return "Promotion decision recorded.";
    case "promotion_rejected":
      return "Promotion rejection recorded.";
    case "missing_spec":
      return "Missing required fields for strategy spec.";
    case "missing_backtest":
      return "Missing strategy spec id for backtest.";
    case "missing_paper":
      return "Missing strategy spec id for paper run.";
    case "missing_promotion":
      return "Missing strategy spec id or invalid promotion decision.";
    case "failed":
      return `Operation failed${code ? ` with HTTP ${code}` : ""}.`;
    case "unavailable":
      return "Backend unavailable.";
    default:
      return null;
  }
}

function cardTime(value: string): string {
  return new Date(value).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function latestSpec(hypothesisId: string, specs: StrategySpecCard[]): StrategySpecCard | null {
  return specs.find((spec) => spec.hypothesis_id === hypothesisId) ?? null;
}

function remediationHints(notes: string[]): string[] {
  const text = notes.join(" ").toLowerCase();
  const hints = [];
  if (text.includes("cost")) {
    hints.push("Add explicit commission, spread, and slippage assumptions.");
  }
  if (text.includes("baseline")) {
    hints.push("Compare against cash and an equal-weight or sector baseline.");
  }
  if (text.includes("lineage") || text.includes("point-in-time")) {
    hints.push("Use factor replay or attach input bar ids and PIT controls.");
  }
  if (text.includes("drawdown")) {
    hints.push("Tighten stops, sizing, or regime filters before paper promotion.");
  }
  if (text.includes("sample")) {
    hints.push("Increase replay coverage before trusting the result.");
  }
  return hints.length ? hints : ["Review the gate notes and add missing evidence before promotion."];
}

export default async function StrategyPage({ searchParams }: StrategyPageProps) {
  const params = searchParams ? await searchParams : undefined;
  const lifecycle = await fetchStrategyLifecycle();
  const readyHypotheses = lifecycle.hypotheses.length;
  const activeSpecs = lifecycle.specs.length;
  const passedBacktests = lifecycle.backtests.filter((item) => item.gate_result === "passed").length;
  const approvedPromotions = lifecycle.promotion_decisions.filter((item) => item.decision === "approved").length;
  const note = message(params?.strategy, params?.code);

  return (
    <>
      <section className="metric-strip" aria-label="Strategy lifecycle metrics">
        <article className="metric-card metric-card-good">
          <div className="metric-kicker">Hypotheses</div>
          <div className="metric-value tone-good">{readyHypotheses}</div>
          <div className="metric-note">active research hypotheses</div>
        </article>
        <article className="metric-card metric-card-neutral">
          <div className="metric-kicker">Specs</div>
          <div className="metric-value">{activeSpecs}</div>
          <div className="metric-note">deterministic strategy definitions</div>
        </article>
        <article className="metric-card metric-card-good">
          <div className="metric-kicker">Passed backtests</div>
          <div className="metric-value tone-good">{passedBacktests}</div>
          <div className="metric-note">research gate passed</div>
        </article>
        <article className="metric-card metric-card-warn">
          <div className="metric-kicker">Approved promotions</div>
          <div className="metric-value tone-warn">{approvedPromotions}</div>
          <div className="metric-note">ready for later stage progression</div>
        </article>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <div className="section-kicker">Strategy Lab</div>
            <h2 className="headline">Move from hypothesis to deterministic execution artifacts.</h2>
            <p className="panel-copy">
              This page is the operating layer after Research. It is where a hypothesis becomes a spec, the spec gets a
              backtest, the backtest becomes a paper run, and later decisions promote or reject the strategy.
            </p>
          </div>
          <div className="panel-badge-row">
            <span className="panel-badge">Hypothesis</span>
            <span className="panel-badge">Spec</span>
            <span className="panel-badge">Backtest</span>
            <span className="panel-badge">Paper</span>
            <span className="panel-badge">Promotion</span>
          </div>
        </div>

        {note ? <div className="form-status form-status-warn">{note}</div> : null}

        <div className="detail-grid two-col">
          <article className="panel compact-panel">
            <div className="section-kicker">Create spec</div>
            <h3>Hypothesis to spec</h3>
            <form action={createStrategySpecAction} className="stack tight-stack">
              <label className="field">
                <span>Hypothesis</span>
                <select name="hypothesis_id" required defaultValue="">
                  <option value="" disabled>
                    Choose hypothesis
                  </option>
                  {lifecycle.hypotheses.map((hypothesis) => (
                    <option key={hypothesis.id} value={hypothesis.id}>
                      {hypothesis.title}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Title</span>
                <input name="title" placeholder="Strategy spec title" required />
              </label>
              <label className="field">
                <span>Spec code</span>
                <input name="spec_code" placeholder="Optional code" />
              </label>
              <label className="field">
                <span>Signal logic</span>
                <textarea name="signal_logic" rows={4} placeholder="Describe entry, exit, and sizing logic" required />
              </label>
              <label className="field">
                <span>Target market</span>
                <input name="target_market" placeholder="us" defaultValue="us" />
              </label>
              <label className="field">
                <span>Risk rules JSON</span>
                <textarea name="risk_rules" rows={3} placeholder='{"max_position_pct": 0.02}' />
              </label>
              <label className="field">
                <span>Data requirements</span>
                <textarea name="data_requirements" rows={3} placeholder="One per line" />
              </label>
              <label className="field">
                <span>Invalidation conditions</span>
                <textarea name="invalidation_conditions" rows={3} placeholder="One per line" />
              </label>
              <label className="field">
                <span>Execution constraints JSON</span>
                <textarea name="execution_constraints" rows={3} placeholder='{"venue": "paper"}' />
              </label>
              <button className="primary-action" type="submit">
                Create spec
              </button>
            </form>
          </article>

          <article className="panel compact-panel">
            <div className="section-kicker">Record run</div>
            <h3>Backtest, paper, promotion</h3>
            <div className="stack tight-stack">
              <form action={recordBacktestAction} className="stack tight-stack">
                <label className="field">
                  <span>Strategy spec</span>
                  <select name="strategy_spec_id" required defaultValue="">
                    <option value="" disabled>
                      Choose spec
                    </option>
                    {lifecycle.specs.map((spec) => (
                      <option key={spec.id} value={spec.id}>
                        {spec.spec_code} - {spec.title}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span>Dataset range</span>
                  <input name="dataset_range" placeholder="2024-01-01..2025-12-31" />
                </label>
                <label className="field">
                  <span>Sample size</span>
                  <input name="sample_size" type="number" min="0" defaultValue="0" />
                </label>
                <label className="field">
                  <span>Sharpe</span>
                  <input name="sharpe_ratio" type="number" step="0.01" />
                </label>
                <label className="field">
                  <span>Total return %</span>
                  <input name="total_return_pct" type="number" step="0.01" />
                </label>
                <label className="field">
                  <span>Max drawdown %</span>
                  <input name="max_drawdown_pct" type="number" step="0.01" />
                </label>
                <label className="field">
                  <span>Baseline return %</span>
                  <input name="baseline_return_pct" type="number" step="0.01" />
                </label>
                <label className="field">
                  <span>Excess return %</span>
                  <input name="excess_return_pct" type="number" step="0.01" />
                </label>
                <div className="detail-grid two-col">
                  <label className="field">
                    <span>Cost bps</span>
                    <input name="cost_bps" type="number" min="0" step="0.1" defaultValue="5" />
                  </label>
                  <label className="field">
                    <span>Slippage bps</span>
                    <input name="slippage_bps" type="number" min="0" step="0.1" defaultValue="5" />
                  </label>
                  <label className="field">
                    <span>Commission bps</span>
                    <input name="commission_bps" type="number" min="0" step="0.1" defaultValue="0" />
                  </label>
                  <label className="field">
                    <span>Impact coeff</span>
                    <input name="square_root_impact_coefficient" type="number" min="0" step="0.01" defaultValue="0" />
                  </label>
                  <label className="field">
                    <span>Participation slip bps</span>
                    <input name="participation_rate_slippage_bps" type="number" min="0" step="0.1" defaultValue="0" />
                  </label>
                  <label className="field">
                    <span>Trade notional</span>
                    <input name="trade_notional" type="number" min="1" step="1000" defaultValue="100000" />
                  </label>
                </div>
                <label className="field">
                  <span>Baseline refs</span>
                  <textarea name="baseline_refs" rows={2} placeholder="cash&#10;equal_weight_factor_universe" />
                </label>
                <label className="field">
                  <span>PIT controls</span>
                  <textarea name="point_in_time_controls" rows={2} placeholder="as_of_filter&#10;input_bar_lineage" />
                </label>
                <label className="field">
                  <span>Input bar ids</span>
                  <textarea name="input_bar_ids" rows={2} placeholder="One id per line, or comma separated" />
                </label>
                <label className="field">
                  <span>Artifact path</span>
                  <input name="artifact_path" placeholder="workspace/trading/logs/backtest.md" />
                </label>
                <button className="secondary-action" type="submit">
                  Record backtest
                </button>
              </form>

              <form action={recordPaperRunAction} className="stack tight-stack">
                <label className="field">
                  <span>Strategy spec</span>
                  <select name="strategy_spec_id" required defaultValue="">
                    <option value="" disabled>
                      Choose spec
                    </option>
                    {lifecycle.specs.map((spec) => (
                      <option key={spec.id} value={spec.id}>
                        {spec.spec_code} - {spec.title}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span>Deployment label</span>
                  <input name="deployment_label" placeholder="paper-dashboard" />
                </label>
                <label className="field">
                  <span>Monitoring days</span>
                  <input name="monitoring_days" type="number" min="0" defaultValue="0" />
                </label>
                <label className="field">
                  <span>Net PnL %</span>
                  <input name="net_pnl_pct" type="number" step="0.01" />
                </label>
                <label className="field">
                  <span>Profit factor</span>
                  <input name="profit_factor" type="number" step="0.01" />
                </label>
                <label className="field">
                  <span>Max drawdown %</span>
                  <input name="max_drawdown_pct" type="number" step="0.01" />
                </label>
                <label className="field">
                  <span>Capital allocated</span>
                  <input name="capital_allocated" type="number" step="0.01" />
                </label>
                <button className="secondary-action" type="submit">
                  Record paper run
                </button>
              </form>

              <form action={recordPromotionDecisionAction} className="stack tight-stack">
                <label className="field">
                  <span>Strategy spec</span>
                  <select name="strategy_spec_id" required defaultValue="">
                    <option value="" disabled>
                      Choose spec
                    </option>
                    {lifecycle.specs.map((spec) => (
                      <option key={spec.id} value={spec.id}>
                        {spec.spec_code} - {spec.title}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span>Target stage</span>
                  <input name="target_stage" defaultValue="production" />
                </label>
                <label className="field">
                  <span>Decision</span>
                  <select name="decision" defaultValue="rejected">
                    <option value="approved">approved</option>
                    <option value="rejected">rejected</option>
                    <option value="deferred">deferred</option>
                  </select>
                </label>
                <label className="field">
                  <span>Rationale</span>
                  <textarea name="rationale" rows={3} placeholder="Why was the strategy approved or rejected?" />
                </label>
                <button className="secondary-action secondary-action-danger" type="submit">
                  Record decision
                </button>
              </form>
            </div>
          </article>
        </div>

        <div className="detail-grid two-col">
          <article className="panel compact-panel">
            <div className="section-kicker">Factor replay</div>
            <h3>Run PIT factor backtest</h3>
            <p className="panel-copy">
              This generates a backtest directly from stored factor snapshots and their input-bar lineage. It applies
              cost, slippage, baseline, and point-in-time controls before the gate can pass.
            </p>
            <form action={runFactorReplayBacktestAction} className="stack tight-stack">
              <label className="field">
                <span>Strategy spec</span>
                <select name="strategy_spec_id" required defaultValue="">
                  <option value="" disabled>
                    Choose spec
                  </option>
                  {lifecycle.specs.map((spec) => (
                    <option key={spec.id} value={spec.id}>
                      {spec.spec_code} - {spec.title}
                    </option>
                  ))}
                </select>
              </label>
              <div className="detail-grid two-col">
                <label className="field">
                  <span>Factor code</span>
                  <input name="factor_code" defaultValue="momentum_close_return" />
                </label>
                <label className="field">
                  <span>Provider optional</span>
                  <input name="provider_key" placeholder="local-replay" />
                </label>
                <label className="field">
                  <span>Market</span>
                  <input name="market" defaultValue="us_equities" />
                </label>
                <label className="field">
                  <span>Timeframe</span>
                  <input name="timeframe" defaultValue="1d" />
                </label>
                <label className="field">
                  <span>Top N</span>
                  <input name="top_n" type="number" min="1" defaultValue="5" />
                </label>
                <label className="field">
                  <span>Min percentile</span>
                  <input name="min_percentile" type="number" min="0" max="1" step="0.01" defaultValue="0" />
                </label>
                <label className="field">
                  <span>Cost bps</span>
                  <input name="cost_bps" type="number" min="0" step="0.1" defaultValue="5" />
                </label>
                <label className="field">
                  <span>Slippage bps</span>
                  <input name="slippage_bps" type="number" min="0" step="0.1" defaultValue="5" />
                </label>
                <label className="field">
                  <span>Commission bps</span>
                  <input name="commission_bps" type="number" min="0" step="0.1" defaultValue="0" />
                </label>
                <label className="field">
                  <span>Impact coeff</span>
                  <input name="square_root_impact_coefficient" type="number" min="0" step="0.01" defaultValue="0" />
                </label>
                <label className="field">
                  <span>Participation slip bps</span>
                  <input name="participation_rate_slippage_bps" type="number" min="0" step="0.1" defaultValue="0" />
                </label>
                <label className="field">
                  <span>Trade notional</span>
                  <input name="trade_notional" type="number" min="1" step="1000" defaultValue="100000" />
                </label>
              </div>
              <label className="field">
                <span>As of optional</span>
                <input name="as_of" type="datetime-local" />
              </label>
              <label className="field">
                <span>Baseline refs</span>
                <textarea name="baseline_refs" rows={2} defaultValue={"cash\nequal_weight_factor_universe"} />
              </label>
              <label className="field">
                <span>PIT controls</span>
                <textarea name="point_in_time_controls" rows={2} defaultValue={"factor_as_of_filter\ninput_bar_lineage"} />
              </label>
              <button className="primary-action" type="submit">
                Run factor replay
              </button>
            </form>
          </article>

          <article className="panel compact-panel">
            <div className="section-kicker">Manual evidence</div>
            <h3>Backtest gate requirements</h3>
            <p className="panel-copy">
              Manual backtests can still be recorded, but they will not pass unless they include cost model, baseline
              comparison, point-in-time controls, and input-bar lineage.
            </p>
          </article>
        </div>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Hypotheses</div>
          <h3>Research objects</h3>
          <div className="stack tight-stack">
            {lifecycle.hypotheses.map((hypothesis) => (
              <article key={hypothesis.id} className="stack-card compact-stack-card">
                <strong>{hypothesis.title}</strong>
                <div className="tile-meta">{hypothesis.target_market} | {hypothesis.current_stage} | {cardTime(hypothesis.created_at)}</div>
                <p className="callout">{hypothesis.thesis}</p>
                {latestSpec(hypothesis.id, lifecycle.specs) ? (
                  <div className="tile-meta">Latest spec: {latestSpec(hypothesis.id, lifecycle.specs)?.spec_code}</div>
                ) : (
                  <div className="tile-meta">No spec created yet.</div>
                )}
              </article>
            ))}
            {lifecycle.hypotheses.length === 0 ? <div className="tile-meta">No hypothesis exists yet.</div> : null}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Run History</div>
          <h3>Backtest and paper evidence</h3>
          <div className="stack tight-stack">
            {lifecycle.backtests.map((backtest) => (
              <article key={backtest.id} className="stack-card compact-stack-card">
                <strong>{backtest.strategy_spec_id}</strong>
                <div className={`tile-meta ${toneClass(backtest.gate_result)}`}>{backtest.gate_result} | sample {backtest.sample_size}</div>
                <p className="callout">
                  Sharpe {backtest.metrics_json?.sharpe_ratio as number | undefined ?? "n/a"} | Return{" "}
                  {backtest.metrics_json?.total_return_pct as number | undefined ?? "n/a"} | DD{" "}
                  {backtest.metrics_json?.max_drawdown_pct as number | undefined ?? "n/a"}
                </p>
                {backtest.gate_notes.length ? (
                  <p className="callout">Gate notes: {backtest.gate_notes.join(" ")}</p>
                ) : null}
                {backtest.gate_result !== "passed" ? (
                  <p className="callout">Fix: {remediationHints(backtest.gate_notes).join(" ")}</p>
                ) : null}
                <div className="tile-meta">{cardTime(backtest.created_at)}</div>
              </article>
            ))}
            {lifecycle.paper_runs.map((paper) => (
              <article key={paper.id} className="stack-card compact-stack-card">
                <strong>{paper.strategy_spec_id}</strong>
                <div className={`tile-meta ${toneClass(paper.gate_result)}`}>{paper.gate_result} | {paper.deployment_label}</div>
                <p className="callout">
                  Net PnL {paper.metrics_json?.net_pnl_pct as number | undefined ?? "n/a"} | PF{" "}
                  {paper.metrics_json?.profit_factor as number | undefined ?? "n/a"} | DD{" "}
                  {paper.metrics_json?.max_drawdown_pct as number | undefined ?? "n/a"}
                </p>
                {paper.gate_notes.length ? <p className="callout">Gate notes: {paper.gate_notes.join(" ")}</p> : null}
                {paper.gate_result !== "ready_for_live_review" ? (
                  <p className="callout">Fix: {remediationHints(paper.gate_notes).join(" ")}</p>
                ) : null}
                <div className="tile-meta">{cardTime(paper.created_at)}</div>
              </article>
            ))}
            {lifecycle.backtests.length === 0 && lifecycle.paper_runs.length === 0 ? (
              <div className="tile-meta">No run evidence recorded yet.</div>
            ) : null}
          </div>
        </article>
      </section>

      <section className="panel">
        <div className="section-kicker">Decisions</div>
        <h3>Promotion decisions</h3>
        <div className="stack tight-stack">
          {lifecycle.promotion_decisions.map((decision) => (
            <article key={decision.id} className="stack-card compact-stack-card">
              <strong>{decision.strategy_spec_id}</strong>
              <div className={`tile-meta ${toneClass(decision.decision)}`}>{decision.decision} | target {decision.target_stage}</div>
              <p className="callout">{decision.rationale}</p>
              <div className="tile-meta">decided by {decision.decided_by} at {cardTime(decision.decided_at)}</div>
            </article>
          ))}
          {lifecycle.promotion_decisions.length === 0 ? <div className="tile-meta">No decision recorded yet.</div> : null}
        </div>
      </section>
    </>
  );
}

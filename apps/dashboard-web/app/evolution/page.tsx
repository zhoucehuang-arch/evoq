import { fetchEvolution } from "@/lib/dashboard";
import type { DashboardFrontendStatus } from "@/lib/types";

type MetricTone = "good" | "warn" | "bad" | "neutral";

function toneClass(tone: string): string {
  switch (tone) {
    case "good":
      return "tone-good";
    case "warn":
      return "tone-warn";
    case "bad":
      return "tone-bad";
    default:
      return "";
  }
}

function toneSuffix(tone: MetricTone): string {
  switch (tone) {
    case "good":
      return "good";
    case "warn":
      return "warn";
    case "bad":
      return "bad";
    default:
      return "neutral";
  }
}

function statusLabel(status?: DashboardFrontendStatus): string {
  switch (status?.error_kind) {
    case "auth":
      return "Dashboard Auth Failed";
    case "unavailable":
      return "Backend Unavailable";
    case "server":
      return "Backend Error";
    case "http":
      return "Unexpected API Response";
    case "network":
      return "Network Path Broken";
    default:
      return "Degraded Dashboard";
  }
}

function loopTone(status: string, failureStreak: number): string {
  if (failureStreak > 0) {
    return "tone-warn";
  }
  return /warning|review|degraded|halt/i.test(status) ? "tone-warn" : "tone-good";
}

export default async function EvolutionPage() {
  const evolution = await fetchEvolution();
  const frontendStatus = evolution.frontend_status;

  const topMetrics = [
    {
      label: "Improvement proposals",
      value: `${evolution.metrics.proposal_count}`,
      tone: evolution.metrics.proposal_count > 0 ? "good" : "neutral",
      note: "changes proposed for code, runtime, strategy, or process",
    },
    {
      label: "Ready for review",
      value: `${evolution.metrics.ready_for_review_count}`,
      tone: evolution.metrics.ready_for_review_count > 0 ? "warn" : "good",
      note: "items waiting at the governance gate",
    },
    {
      label: "Canary lanes",
      value: `${evolution.metrics.active_canary_count}`,
      tone: evolution.metrics.active_canary_count > 0 ? "good" : "neutral",
      note: "active monitored rollout or validation lanes",
    },
    {
      label: "Promoted",
      value: `${evolution.metrics.promoted_count}`,
      tone: evolution.metrics.promoted_count > 0 ? "good" : "neutral",
      note: "changes that made it through promotion",
    },
    {
      label: "Rolled back",
      value: `${evolution.metrics.rolled_back_count}`,
      tone: evolution.metrics.rolled_back_count > 0 ? "warn" : "good",
      note: "changes that failed or were deliberately reversed",
    },
  ] as const;

  const operatorFocus = [
    evolution.metrics.ready_for_review_count > 0
      ? `${evolution.metrics.ready_for_review_count} proposal${evolution.metrics.ready_for_review_count > 1 ? "s are" : " is"} waiting for review.`
      : "No proposal is currently waiting at the review gate.",
    evolution.metrics.active_canary_count > 0
      ? `${evolution.metrics.active_canary_count} canary lane${evolution.metrics.active_canary_count > 1 ? "s are" : " is"} actively validating changes.`
      : "No active canary lane is running right now.",
    evolution.metrics.rolled_back_count > 0
      ? `${evolution.metrics.rolled_back_count} rollback event${evolution.metrics.rolled_back_count > 1 ? "s indicate" : " indicates"} recent instability in the evolution lane.`
      : "No rollback pressure is currently visible.",
    evolution.supervisor_loops.some((loop) => loop.failure_streak > 0)
      ? "At least one evolution loop has a failure streak and should be inspected before trusting autonomous promotion."
      : "Visible evolution loops are not showing a failure streak right now.",
  ];

  return (
    <>
      <section className="metric-strip" aria-label="Evolution metrics">
        {topMetrics.map((metricCard) => (
          <article key={metricCard.label} className={`metric-card metric-card-${toneSuffix(metricCard.tone)}`}>
            <div className="metric-kicker">{metricCard.label}</div>
            <div className={`metric-value ${toneClass(metricCard.tone)}`}>{metricCard.value}</div>
            <div className="metric-note">{metricCard.note}</div>
          </article>
        ))}
      </section>

      <section className="overview-grid">
        <article className="panel hero-panel stage-panel">
          <div className="panel-heading">
            <div>
              <div className="section-kicker">Evolution Council</div>
              <h2 className="headline">Autonomous Evolution Council</h2>
              <p className="panel-copy">
                This page should make self-improvement feel governed, not magical: what changed, what is under test, what
                was promoted, and what had to be rolled back.
              </p>
            </div>
            <div className="panel-badge-row">
              <span className="panel-badge">Freshness {evolution.freshness.state}</span>
              <span className="panel-badge">Workflows {evolution.recent_workflows.length}</span>
              <span className="panel-badge">Codex runs {evolution.recent_codex_runs.length}</span>
            </div>
          </div>

          <div className="fact-grid">
            <article className="fact-card">
              <div className="fact-label">Proposals</div>
              <div className="fact-value">{evolution.metrics.proposal_count}</div>
              <div className="fact-meta">active improvement candidates in the pipeline</div>
            </article>
            <article className="fact-card">
              <div className="fact-label">Review backlog</div>
              <div className={`fact-value ${evolution.metrics.ready_for_review_count > 0 ? "tone-warn" : ""}`}>
                {evolution.metrics.ready_for_review_count}
              </div>
              <div className="fact-meta">proposals waiting for judgment</div>
            </article>
            <article className="fact-card">
              <div className="fact-label">Promotion ratio</div>
              <div className="fact-value">
                {evolution.metrics.promoted_count}/{Math.max(evolution.metrics.proposal_count, evolution.metrics.promoted_count)}
              </div>
              <div className="fact-meta">promoted changes relative to visible proposals</div>
            </article>
            <article className="fact-card">
              <div className="fact-label">Loop count</div>
              <div className="fact-value">{evolution.supervisor_loops.length}</div>
              <div className="fact-meta">supervision loops driving autonomous improvement</div>
            </article>
          </div>

          <div className="bullet-cloud">
            {evolution.highlights.map((highlight) => (
              <div key={highlight} className="bullet-chip">
                {highlight}
              </div>
            ))}
          </div>

          {frontendStatus ? (
            <div className="stack">
              <article className="stack-card">
                <strong>{statusLabel(frontendStatus)}</strong>
                <span>{frontendStatus.status_code ? `HTTP ${frontendStatus.status_code}` : "no HTTP status"}</span>
                <p className="callout">{frontendStatus.detail}</p>
                <p className="callout">{frontendStatus.operator_action}</p>
              </article>
            </div>
          ) : null}
        </article>

        <aside className="panel command-panel">
          <div className="section-kicker">Flight Deck</div>
          <h3>Change snapshot</h3>
          <div className="snapshot-grid">
            <article className="snapshot-cell">
              <div className="snapshot-label">Recent workflows</div>
              <div className="snapshot-value">{evolution.recent_workflows.length}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Codex runs</div>
              <div className="snapshot-value">{evolution.recent_codex_runs.length}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Canaries</div>
              <div className="snapshot-value">{evolution.recent_canary_runs.length}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Promotion decisions</div>
              <div className="snapshot-value">{evolution.recent_promotion_decisions.length}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Loops</div>
              <div className="snapshot-value">{evolution.supervisor_loops.length}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Rollbacks</div>
              <div className={`snapshot-value ${evolution.metrics.rolled_back_count > 0 ? "tone-warn" : ""}`}>
                {evolution.metrics.rolled_back_count}
              </div>
            </article>
          </div>

          <h4 className="subsection-title">What to review now</h4>
          <div className="stack tight-stack">
            {operatorFocus.map((item) => (
              <article key={item} className="stack-card compact-stack-card">
                <p className="callout">{item}</p>
              </article>
            ))}
          </div>
        </aside>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Workflow</div>
          <h3>Recent workflows</h3>
          {evolution.recent_workflows.length === 0 ? (
            <div className="stack">
              <article className="stack-card">
                <strong>No evolution workflows yet</strong>
                <p className="callout">Workflow evidence should appear here once the autonomous evolution lane starts running.</p>
              </article>
            </div>
          ) : (
            <div className="table-shell">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Workflow</th>
                    <th>Family</th>
                    <th>Status</th>
                    <th>Latest</th>
                  </tr>
                </thead>
                <tbody>
                  {evolution.recent_workflows.map((workflow) => (
                    <tr key={workflow.id}>
                      <td>{workflow.workflow_name}</td>
                      <td>{workflow.workflow_family}</td>
                      <td>{workflow.status}</td>
                      <td>{workflow.latest_event_summary ?? "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>

        <article className="panel">
          <div className="section-kicker">Execution</div>
          <h3>Recent Codex runs</h3>
          <div className="stack">
            {evolution.recent_codex_runs.map((run) => (
              <article key={run.id} className="stack-card">
                <strong>{run.worker_class}</strong>
                <span>
                  {run.status} | {run.current_attempt}/{run.max_iterations}
                </span>
                <p className="callout">{run.objective}</p>
              </article>
            ))}
            {evolution.recent_codex_runs.length === 0 ? <div className="tile-meta">No recent Codex evolution runs are visible yet.</div> : null}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Proposals</div>
          <h3>Improvement proposals</h3>
          <div className="stack">
            {evolution.recent_proposals.map((proposal) => (
              <article key={proposal.id} className="stack-card">
                <strong>{proposal.title}</strong>
                <span>
                  {proposal.target_surface} | {proposal.proposal_kind} | {proposal.proposal_state}
                </span>
                <p className="callout">{proposal.risk_summary ?? "No explicit risk summary recorded."}</p>
              </article>
            ))}
            {evolution.recent_proposals.length === 0 ? <div className="tile-meta">No recent improvement proposals yet.</div> : null}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Promotion</div>
          <h3>Canary and promotion</h3>
          <div className="stack">
            {evolution.recent_canary_runs.map((run) => (
              <article key={run.id} className="stack-card">
                <strong>
                  {run.lane_type} | {run.status}
                </strong>
                <span>
                  {run.environment} | traffic {run.traffic_pct}% | rollback ready {run.rollback_ready ? "yes" : "no"}
                </span>
                <p className="callout">
                  drift score {run.objective_drift_score ?? "n/a"} | proposal {run.proposal_id}
                </p>
              </article>
            ))}
            {evolution.recent_promotion_decisions.map((decision) => (
              <article key={decision.id} className="stack-card">
                <strong>
                  {decision.decision} | {decision.decided_by}
                </strong>
                <p className="callout">{decision.rationale}</p>
              </article>
            ))}
            {evolution.recent_canary_runs.length === 0 && evolution.recent_promotion_decisions.length === 0 ? (
              <div className="tile-meta">No recent canary run or promotion decision is visible yet.</div>
            ) : null}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Signals</div>
          <h3>Evolution counters</h3>
          <div className="runtime-mini-grid">
            {evolution.summary_cards.map((card) => (
              <article key={card.label} className="stat-card compact-stat-card">
                <div className="stat-label">{card.label}</div>
                <div className={`stat-value compact-stat-value ${toneClass(card.tone)}`}>{card.value}</div>
                {card.hint ? <div className="tile-meta">{card.hint}</div> : null}
              </article>
            ))}
            {evolution.summary_cards.length === 0 ? (
              <>
                <article className="stat-card compact-stat-card">
                  <div className="stat-label">Proposals</div>
                  <div className="stat-value compact-stat-value">{evolution.metrics.proposal_count}</div>
                </article>
                <article className="stat-card compact-stat-card">
                  <div className="stat-label">Ready for review</div>
                  <div className="stat-value compact-stat-value">{evolution.metrics.ready_for_review_count}</div>
                </article>
                <article className="stat-card compact-stat-card">
                  <div className="stat-label">Canaries</div>
                  <div className="stat-value compact-stat-value">{evolution.metrics.active_canary_count}</div>
                </article>
                <article className="stat-card compact-stat-card">
                  <div className="stat-label">Promoted / Rolled back</div>
                  <div className="stat-value compact-stat-value">
                    {evolution.metrics.promoted_count} / {evolution.metrics.rolled_back_count}
                  </div>
                </article>
              </>
            ) : null}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Cadence</div>
          <h3>Loop monitor</h3>
          <div className="tile-grid">
            {evolution.supervisor_loops.map((loop) => (
              <article key={loop.loop_key} className="tile">
                <div className="tile-label">{loop.display_name}</div>
                <div className={`tile-value ${loopTone(loop.last_status, loop.failure_streak)}`}>{loop.last_status}</div>
                <div className="tile-meta">mode {loop.execution_mode}</div>
                <div className="tile-meta">failure streak {loop.failure_streak}</div>
                <div className="tile-meta">cadence {loop.cadence_seconds}s</div>
              </article>
            ))}
            {evolution.supervisor_loops.length === 0 ? <div className="tile-meta">No evolution loop is visible yet.</div> : null}
          </div>
        </article>
      </section>
    </>
  );
}

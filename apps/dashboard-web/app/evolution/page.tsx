import { fetchEvolution } from "@/lib/dashboard";

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

export default async function EvolutionPage() {
  const evolution = await fetchEvolution();

  return (
    <>
      <section className="hero">
        <article className="panel hero-panel">
          <div className="chip-row">
            <span className="chip">
              Freshness <strong>{evolution.freshness.state}</strong>
            </span>
          </div>
          <h2 className="headline">Autonomous Evolution Council</h2>
          <ul className="list">
            {evolution.highlights.map((highlight) => (
              <li key={highlight}>{highlight}</li>
            ))}
          </ul>
        </article>
      </section>

      <section className="card-grid">
        {evolution.summary_cards.map((card) => (
          <article key={card.label} className="stat-card">
            <div className="stat-label">{card.label}</div>
            <div className={`stat-value ${toneClass(card.tone)}`}>{card.value}</div>
          </article>
        ))}
      </section>

      <section className="card-grid">
        <article className="stat-card">
          <div className="stat-label">Improvement proposals</div>
          <div className="stat-value">{evolution.metrics.proposal_count}</div>
        </article>
        <article className="stat-card">
          <div className="stat-label">Ready for review</div>
          <div className="stat-value">{evolution.metrics.ready_for_review_count}</div>
        </article>
        <article className="stat-card">
          <div className="stat-label">Active canary lanes</div>
          <div className="stat-value">{evolution.metrics.active_canary_count}</div>
        </article>
        <article className="stat-card">
          <div className="stat-label">Promoted / rolled back</div>
          <div className="stat-value">
            {evolution.metrics.promoted_count} / {evolution.metrics.rolled_back_count}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <h3>Recent Workflows</h3>
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
        </article>

        <article className="panel">
          <h3>Recent Codex Runs</h3>
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
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <h3>Improvement Proposals</h3>
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
          </div>
        </article>

        <article className="panel">
          <h3>Canary And Promotion</h3>
          <div className="stack">
            {evolution.recent_canary_runs.map((run) => (
              <article key={run.id} className="stack-card">
                <strong>
                  {run.lane_type} | {run.status}
                </strong>
                <span>
                  {run.environment} | {run.traffic_pct}% | rollback ready {run.rollback_ready ? "yes" : "no"}
                </span>
                <p className="callout">
                  Drift score {run.objective_drift_score ?? "n/a"} | proposal {run.proposal_id}
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
          </div>
        </article>
      </section>

      <section className="panel">
        <h3>Loop Monitor</h3>
        <div className="tile-grid">
          {evolution.supervisor_loops.map((loop) => (
            <article key={loop.loop_key} className="tile">
              <div className="tile-label">{loop.display_name}</div>
              <div className="tile-value">{loop.last_status}</div>
              <div className="tile-meta">Mode: {loop.execution_mode}</div>
              <div className="tile-meta">Failure streak: {loop.failure_streak}</div>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}

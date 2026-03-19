import { fetchLearning } from "@/lib/dashboard";

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

export default async function LearningPage() {
  const learning = await fetchLearning();

  return (
    <>
      <section className="hero">
        <article className="panel hero-panel">
          <div className="chip-row">
            <span className="chip">
              Freshness <strong>{learning.freshness.state}</strong>
            </span>
            <span className="chip">
              Ready <strong>{learning.metrics.ready_insight_count}</strong>
            </span>
            <span className="chip">
              Quarantined <strong>{learning.metrics.quarantined_insight_count}</strong>
            </span>
          </div>
          <h2 className="headline">Learning Mesh</h2>
          <ul className="list">
            {learning.highlights.map((highlight) => (
              <li key={highlight}>{highlight}</li>
            ))}
          </ul>
        </article>
      </section>

      <section className="card-grid">
        {learning.summary_cards.map((card) => (
          <article key={card.label} className="stat-card">
            <div className="stat-label">{card.label}</div>
            <div className={`stat-value ${toneClass(card.tone)}`}>{card.value}</div>
          </article>
        ))}
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <h3>Source Health</h3>
          <div className="table-shell">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Status</th>
                  <th>Trust</th>
                  <th>Freshness</th>
                  <th>Last Validated</th>
                </tr>
              </thead>
              <tbody>
                {learning.sources.map((source) => (
                  <tr key={source.source_key}>
                    <td>{source.source_key}</td>
                    <td>{source.health_status}</td>
                    <td>{source.trust_score.toFixed(2)}</td>
                    <td>{source.freshness_score.toFixed(2)}</td>
                    <td>{source.last_validated_at ?? "n/a"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>

        <article className="panel">
          <h3>Research Inbox</h3>
          <div className="tile-grid">
            {learning.recent_documents.map((document) => (
              <article key={document.id} className="tile">
                <div className="tile-label">{document.title}</div>
                <div className="tile-value">{document.source_type}</div>
                <div className="tile-meta">Status: {document.status}</div>
                <div className="tile-meta">Source: {document.source_key}</div>
                <div className="tile-meta">Codex: {document.codex_run_id ?? "n/a"}</div>
                <div className="tile-meta">Workflow: {document.workflow_run_id ?? "n/a"}</div>
                <div className="tile-meta">Citations: {document.citation_count}</div>
                <div className="tile-meta">Evidence: {document.evidence_count}</div>
                <div className="tile-meta">
                  Confidence:{" "}
                  {document.confidence !== null && document.confidence !== undefined ? document.confidence.toFixed(2) : "n/a"}
                </div>
              </article>
            ))}
            {learning.recent_documents.length === 0 ? <div className="tile-meta">No durable research documents yet.</div> : null}
          </div>
        </article>

        <article className="panel">
          <h3>Insight Gates</h3>
          <div className="tile-grid">
            {learning.recent_insights.map((insight) => (
              <article key={insight.id} className="tile">
                <div className="tile-label">{insight.title}</div>
                <div className="tile-value">{insight.promotion_state}</div>
                <div className="tile-meta">Topic: {insight.topic_key}</div>
                <div className="tile-meta">Document: {insight.document_id}</div>
                <div className="tile-meta">Status: {insight.status}</div>
                <div className="tile-meta">Codex: {insight.codex_run_id ?? "n/a"}</div>
                <div className="tile-meta">Workflow: {insight.workflow_run_id ?? "n/a"}</div>
                <div className="tile-meta">Loop: {insight.supervisor_loop_key ?? "n/a"}</div>
                <div className="tile-meta">Evidence: {insight.evidence_count}</div>
                <div className="tile-meta">Citations: {insight.citation_count}</div>
                <div className="tile-meta">
                  Confidence: {insight.confidence !== null && insight.confidence !== undefined ? insight.confidence.toFixed(2) : "n/a"}
                </div>
                {insight.quarantine_reason ? <div className="tile-meta">Quarantine: {insight.quarantine_reason}</div> : null}
              </article>
            ))}
            {learning.recent_insights.length === 0 ? <div className="tile-meta">No durable insight candidates yet.</div> : null}
          </div>
        </article>

        <article className="panel">
          <h3>Supervisor Loops</h3>
          <div className="tile-grid">
            {learning.supervisor_loops.map((loop) => (
              <article key={loop.loop_key} className="tile">
                <div className="tile-label">{loop.display_name}</div>
                <div className="tile-value">{loop.last_status}</div>
                <div className="tile-meta">Mode: {loop.execution_mode}</div>
                <div className="tile-meta">Cadence: {loop.cadence_seconds}s</div>
                <div className="tile-meta">Failure streak: {loop.failure_streak}</div>
                <div className="tile-meta">Last completed: {loop.last_completed_at ?? "n/a"}</div>
                <div className="tile-meta">Next due: {loop.next_due_at ?? "n/a"}</div>
                {loop.last_error ? <div className="tile-meta">Last error: {loop.last_error}</div> : null}
              </article>
            ))}
          </div>
        </article>
      </section>
    </>
  );
}

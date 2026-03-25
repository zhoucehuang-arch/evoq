import { fetchLearning } from "@/lib/dashboard";
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

function average(values: number[]): number {
  if (values.length === 0) {
    return 0;
  }
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function percent(value: number): string {
  return `${value.toFixed(1)}%`;
}

function loopTone(status: string, failureStreak: number): string {
  if (failureStreak > 0) {
    return "tone-warn";
  }
  return /warning|review|degraded|halt/i.test(status) ? "tone-warn" : "tone-good";
}

export default async function LearningPage() {
  const learning = await fetchLearning();
  const frontendStatus = learning.frontend_status;
  const avgTrust = average(learning.sources.map((source) => source.trust_score));
  const avgFreshness = average(learning.sources.map((source) => source.freshness_score));
  const degradedSources = learning.sources.filter((source) => source.health_status !== "healthy" && source.health_status !== "ok").length;

  const topMetrics = [
    {
      label: "Research documents",
      value: `${learning.metrics.document_count}`,
      tone: learning.metrics.document_count > 0 ? "good" : "warn",
      note: "durable documents retained in the runtime mesh",
    },
    {
      label: "Insight candidates",
      value: `${learning.metrics.insight_count}`,
      tone: learning.metrics.insight_count > 0 ? "good" : "neutral",
      note: "candidate lessons extracted from recent intake",
    },
    {
      label: "Ready insights",
      value: `${learning.metrics.ready_insight_count}`,
      tone: learning.metrics.ready_insight_count > 0 ? "good" : "warn",
      note: "promotion-ready items waiting for governance",
    },
    {
      label: "Quarantined",
      value: `${learning.metrics.quarantined_insight_count}`,
      tone: learning.metrics.quarantined_insight_count > 0 ? "warn" : "good",
      note: "items blocked by evidence or safety concerns",
    },
    {
      label: "Supervisor loops",
      value: `${learning.supervisor_loops.length}`,
      tone: learning.supervisor_loops.length > 0 ? "good" : "warn",
      note: "cadence engines driving intake and promotion",
    },
  ] as const;

  const operatorFocus = [
    learning.metrics.ready_insight_count > 0
      ? `${learning.metrics.ready_insight_count} insight candidate${learning.metrics.ready_insight_count > 1 ? "s are" : " is"} ready for promotion review.`
      : "No insight candidate is currently waiting at the promotion gate.",
    learning.metrics.quarantined_insight_count > 0
      ? `${learning.metrics.quarantined_insight_count} quarantined item${learning.metrics.quarantined_insight_count > 1 ? "s need" : " needs"} evidence review.`
      : "No quarantined insight is currently visible.",
    degradedSources > 0
      ? `${degradedSources} source${degradedSources > 1 ? "s are" : " is"} not in a healthy state.`
      : "All visible sources appear healthy enough for supervised intake.",
    learning.supervisor_loops.some((loop) => loop.failure_streak > 0)
      ? "At least one supervisor loop has a non-zero failure streak and deserves inspection."
      : "No visible supervisor loop is showing a failure streak right now.",
  ];

  return (
    <>
      <section className="metric-strip" aria-label="Learning metrics">
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
              <div className="section-kicker">Research Mesh</div>
              <h2 className="headline">Learning Mesh</h2>
              <p className="panel-copy">
                This page should show whether EvoQ is merely collecting material or actually turning research into durable,
                promotable operating knowledge.
              </p>
            </div>
            <div className="panel-badge-row">
              <span className="panel-badge">Freshness {learning.freshness.state}</span>
              <span className="panel-badge">Ready {learning.metrics.ready_insight_count}</span>
              <span className="panel-badge">Quarantined {learning.metrics.quarantined_insight_count}</span>
            </div>
          </div>

          <div className="fact-grid">
            <article className="fact-card">
              <div className="fact-label">Sources</div>
              <div className="fact-value">{learning.sources.length}</div>
              <div className="fact-meta">{degradedSources} degraded source states</div>
            </article>
            <article className="fact-card">
              <div className="fact-label">Average trust</div>
              <div className="fact-value">{avgTrust.toFixed(2)}</div>
              <div className="fact-meta">mean confidence across visible sources</div>
            </article>
            <article className="fact-card">
              <div className="fact-label">Average freshness</div>
              <div className="fact-value">{avgFreshness.toFixed(2)}</div>
              <div className="fact-meta">source freshness score across the intake stack</div>
            </article>
            <article className="fact-card">
              <div className="fact-label">Recent intake</div>
              <div className="fact-value">
                {learning.recent_documents.length} / {learning.recent_insights.length}
              </div>
              <div className="fact-meta">documents / insight candidates on screen</div>
            </article>
          </div>

          <div className="bullet-cloud">
            {learning.highlights.map((highlight) => (
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
          <h3>Promotion snapshot</h3>
          <div className="snapshot-grid">
            <article className="snapshot-cell">
              <div className="snapshot-label">Documents</div>
              <div className="snapshot-value">{learning.metrics.document_count}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Insights</div>
              <div className="snapshot-value">{learning.metrics.insight_count}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Ready</div>
              <div className="snapshot-value">{learning.metrics.ready_insight_count}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Quarantined</div>
              <div className={`snapshot-value ${learning.metrics.quarantined_insight_count > 0 ? "tone-warn" : ""}`}>
                {learning.metrics.quarantined_insight_count}
              </div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Loops</div>
              <div className="snapshot-value">{learning.supervisor_loops.length}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Source health</div>
              <div className="snapshot-value">{percent((1 - degradedSources / Math.max(learning.sources.length, 1)) * 100)}</div>
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
          <div className="section-kicker">Inputs</div>
          <h3>Source health</h3>
          {learning.sources.length === 0 ? (
            <div className="stack">
              <article className="stack-card">
                <strong>No source health visible yet</strong>
                <p className="callout">The learning mesh will not feel trustworthy until the source-health layer is populated.</p>
              </article>
            </div>
          ) : (
            <div className="table-shell">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Source</th>
                    <th>Status</th>
                    <th>Trust</th>
                    <th>Freshness</th>
                    <th>Last validated</th>
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
          )}
        </article>

        <article className="panel">
          <div className="section-kicker">Promotion</div>
          <h3>Learning counters</h3>
          <div className="runtime-mini-grid">
            {learning.summary_cards.map((card) => (
              <article key={card.label} className="stat-card compact-stat-card">
                <div className="stat-label">{card.label}</div>
                <div className={`stat-value compact-stat-value ${toneClass(card.tone)}`}>{card.value}</div>
                {card.hint ? <div className="tile-meta">{card.hint}</div> : null}
              </article>
            ))}
            {learning.summary_cards.length === 0 ? (
              <article className="stat-card compact-stat-card">
                <div className="stat-label">Summary cards</div>
                <div className="stat-value compact-stat-value">n/a</div>
                <div className="tile-meta">the backend has not supplied learning summary cards yet</div>
              </article>
            ) : null}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Intake</div>
          <h3>Research inbox</h3>
          <div className="stack">
            {learning.recent_documents.map((document) => (
              <article key={document.id} className="stack-card">
                <strong>{document.title}</strong>
                <span>
                  {document.source_type} | {document.status} | source {document.source_key}
                </span>
                <p className="callout">
                  citations {document.citation_count} | evidence {document.evidence_count} | confidence{" "}
                  {document.confidence !== null && document.confidence !== undefined ? document.confidence.toFixed(2) : "n/a"}
                </p>
                <p className="callout">
                  codex {document.codex_run_id ?? "n/a"} | workflow {document.workflow_run_id ?? "n/a"}
                </p>
              </article>
            ))}
            {learning.recent_documents.length === 0 ? <div className="tile-meta">No durable research documents yet.</div> : null}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Gate</div>
          <h3>Insight gates</h3>
          <div className="stack">
            {learning.recent_insights.map((insight) => (
              <article key={insight.id} className="stack-card">
                <strong>{insight.title}</strong>
                <span>
                  {insight.promotion_state} | {insight.status} | topic {insight.topic_key}
                </span>
                <p className="callout">
                  evidence {insight.evidence_count} | citations {insight.citation_count} | confidence{" "}
                  {insight.confidence !== null && insight.confidence !== undefined ? insight.confidence.toFixed(2) : "n/a"}
                </p>
                <p className="callout">
                  codex {insight.codex_run_id ?? "n/a"} | workflow {insight.workflow_run_id ?? "n/a"} | loop {insight.supervisor_loop_key ?? "n/a"}
                </p>
                {insight.quarantine_reason ? <p className="callout">quarantine: {insight.quarantine_reason}</p> : null}
              </article>
            ))}
            {learning.recent_insights.length === 0 ? <div className="tile-meta">No durable insight candidates yet.</div> : null}
          </div>
        </article>
      </section>

      <section className="panel">
        <div className="section-kicker">Cadence</div>
        <h3>Supervisor loops</h3>
        <div className="tile-grid">
          {learning.supervisor_loops.map((loop) => (
            <article key={loop.loop_key} className="tile">
              <div className="tile-label">{loop.display_name}</div>
              <div className={`tile-value ${loopTone(loop.last_status, loop.failure_streak)}`}>{loop.last_status}</div>
              <div className="tile-meta">mode {loop.execution_mode}</div>
              <div className="tile-meta">cadence {loop.cadence_seconds}s</div>
              <div className="tile-meta">failure streak {loop.failure_streak}</div>
              <div className="tile-meta">last completed {loop.last_completed_at ?? "n/a"}</div>
              <div className="tile-meta">next due {loop.next_due_at ?? "n/a"}</div>
              {loop.last_error ? <p className="callout">{loop.last_error}</p> : null}
            </article>
          ))}
          {learning.supervisor_loops.length === 0 ? <div className="tile-meta">No supervisor loops are visible yet.</div> : null}
        </div>
      </section>
    </>
  );
}

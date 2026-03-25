import { fetchIncidents } from "@/lib/dashboard";
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

function dateLabel(value: string | null | undefined): string {
  if (!value) {
    return "n/a";
  }
  return new Date(value).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function severityTone(severity: string): MetricTone {
  const normalized = severity.toLowerCase();
  if (normalized === "critical") {
    return "bad";
  }
  if (normalized === "high" || normalized === "medium") {
    return "warn";
  }
  return "good";
}

export default async function IncidentsPage() {
  const incidents = await fetchIncidents();
  const frontendStatus = incidents.frontend_status;
  const criticalPressure = incidents.active_incidents.filter((incident) => ["critical", "high"].includes(incident.severity.toLowerCase())).length;
  const highRiskApprovals = incidents.pending_approvals.filter((approval) => approval.risk_level.toLowerCase() === "high").length;
  const unresolvedRecent = incidents.recent_incidents.filter((incident) => !["resolved", "closed"].includes(incident.status.toLowerCase())).length;

  const topMetrics = [
    {
      label: "Active incidents",
      value: `${incidents.active_incidents.length}`,
      tone: incidents.active_incidents.length > 0 ? "warn" : "good",
      note: incidents.active_incidents.length > 0 ? "live surfaces deserve explicit review" : "no active incident is visible",
    },
    {
      label: "Critical pressure",
      value: `${criticalPressure}`,
      tone: criticalPressure > 0 ? "bad" : "good",
      note: "high or critical incident severity on screen",
    },
    {
      label: "Pending approvals",
      value: `${incidents.pending_approvals.length}`,
      tone: incidents.pending_approvals.length > 0 ? "warn" : "good",
      note: "governed decisions waiting for owner or policy sign-off",
    },
    {
      label: "High-risk approvals",
      value: `${highRiskApprovals}`,
      tone: highRiskApprovals > 0 ? "warn" : "good",
      note: "items with higher downside if approved carelessly",
    },
    {
      label: "Recent unresolved",
      value: `${unresolvedRecent}`,
      tone: unresolvedRecent > 0 ? "warn" : "good",
      note: frontendStatus ? statusLabel(frontendStatus) : "open or monitoring incidents in the recent tape",
    },
  ] as const;

  const operatorFocus = [
    frontendStatus
      ? `${statusLabel(frontendStatus)}. ${frontendStatus.operator_action}`
      : "The dashboard is reading incident and approval state without a visible frontend degradation flag.",
    incidents.active_incidents.length > 0
      ? `${incidents.active_incidents.length} active incident${incidents.active_incidents.length === 1 ? " is" : "s are"} still shaping runtime posture.`
      : "No active incident is currently changing the runtime posture.",
    criticalPressure > 0
      ? `${criticalPressure} active incident${criticalPressure === 1 ? "" : "s"} carries high or critical severity and should block casual live changes.`
      : "No high-severity incident is currently visible.",
    incidents.pending_approvals.length > 0
      ? `${incidents.pending_approvals.length} approval${incidents.pending_approvals.length === 1 ? " is" : "s are"} still gating trading or system evolution.`
      : "No approval is currently waiting in the queue.",
    highRiskApprovals > 0
      ? `${highRiskApprovals} queued approval${highRiskApprovals === 1 ? " is" : "s are"} marked high risk and deserves deliberate review.`
      : "The queue is not currently showing a high-risk approval.",
  ];

  const responsePlaybook = [
    "Review open incidents before changing live posture, even if the dashboard looks mostly healthy.",
    "Treat approval backlog as real operational pressure because it directly changes what the system is allowed to do next.",
    "Resolve provider or reconciliation incidents before promoting new trading or evolution changes.",
    "If the dashboard is degraded, verify the authority core through smoke checks and logs instead of trusting the screen.",
  ];

  return (
    <>
      <section className="metric-strip" aria-label="Incidents metrics">
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
              <div className="section-kicker">Incident Command</div>
              <h2 className="headline">Governance And Incident Desk</h2>
              <p className="panel-copy">
                This page should make risk and backlog actionable: what is actively wrong, what is merely waiting on
                judgment, and what should block a live posture change right now.
              </p>
            </div>
            <div className="panel-badge-row">
              <span className="panel-badge">Freshness {incidents.freshness.state}</span>
              <span className="panel-badge">Active {incidents.active_incidents.length}</span>
              <span className="panel-badge">Approvals {incidents.pending_approvals.length}</span>
            </div>
          </div>

          <div className="fact-grid">
            <article className="fact-card">
              <div className="fact-label">Generated</div>
              <div className="fact-value">{dateLabel(incidents.generated_at)}</div>
              <div className="fact-meta">incident and governance snapshot</div>
            </article>
            <article className="fact-card">
              <div className="fact-label">Active incidents</div>
              <div className={`fact-value ${incidents.active_incidents.length > 0 ? "tone-warn" : "tone-good"}`}>
                {incidents.active_incidents.length}
              </div>
              <div className="fact-meta">open incident desk count</div>
            </article>
            <article className="fact-card">
              <div className="fact-label">Critical / high</div>
              <div className={`fact-value ${criticalPressure > 0 ? "tone-bad" : "tone-good"}`}>{criticalPressure}</div>
              <div className="fact-meta">severity pressure inside active incidents</div>
            </article>
            <article className="fact-card">
              <div className="fact-label">Approval backlog</div>
              <div className={`fact-value ${incidents.pending_approvals.length > 0 ? "tone-warn" : ""}`}>
                {incidents.pending_approvals.length}
              </div>
              <div className="fact-meta">{highRiskApprovals} high-risk approval items</div>
            </article>
          </div>

          <div className="bullet-cloud">
            {incidents.highlights.map((highlight) => (
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
          <h3>Pressure snapshot</h3>
          <div className="snapshot-grid">
            <article className="snapshot-cell">
              <div className="snapshot-label">Recent incidents</div>
              <div className="snapshot-value">{incidents.recent_incidents.length}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Unresolved recent</div>
              <div className={`snapshot-value ${unresolvedRecent > 0 ? "tone-warn" : ""}`}>{unresolvedRecent}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Active incidents</div>
              <div className={`snapshot-value ${incidents.active_incidents.length > 0 ? "tone-warn" : ""}`}>
                {incidents.active_incidents.length}
              </div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Critical / high</div>
              <div className={`snapshot-value ${criticalPressure > 0 ? "tone-bad" : ""}`}>{criticalPressure}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Approvals</div>
              <div className={`snapshot-value ${incidents.pending_approvals.length > 0 ? "tone-warn" : ""}`}>
                {incidents.pending_approvals.length}
              </div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">High-risk approvals</div>
              <div className={`snapshot-value ${highRiskApprovals > 0 ? "tone-warn" : ""}`}>{highRiskApprovals}</div>
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
          <div className="section-kicker">Incident Desk</div>
          <h3>Active incidents</h3>
          <div className="stack">
            {incidents.active_incidents.map((incident) => (
              <article key={incident.id} className="stack-card">
                <strong>{incident.title}</strong>
                <span className={toneClass(severityTone(incident.severity))}>
                  {incident.severity} | {incident.status}
                </span>
                <p className="callout">{incident.summary}</p>
                <p className="callout">opened {dateLabel(incident.created_at)}</p>
              </article>
            ))}
            {incidents.active_incidents.length === 0 ? (
              <div className="tile-meta">No active incident is visible right now.</div>
            ) : null}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Approval Queue</div>
          <h3>Pending approvals</h3>
          <div className="stack">
            {incidents.pending_approvals.map((approval) => (
              <article key={approval.id} className="stack-card">
                <strong>{approval.approval_type}</strong>
                <span>
                  {approval.subject_id} | {approval.risk_level} | {approval.decision_status}
                </span>
                <p className="callout">requested by {approval.requested_by}</p>
                <p className="callout">created {dateLabel(approval.created_at)}</p>
              </article>
            ))}
            {incidents.pending_approvals.length === 0 ? <div className="tile-meta">No approval is waiting right now.</div> : null}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Signals</div>
          <h3>Governance counters</h3>
          <div className="runtime-mini-grid">
            {incidents.summary_cards.map((card) => (
              <article key={card.label} className="stat-card compact-stat-card">
                <div className="stat-label">{card.label}</div>
                <div className={`stat-value compact-stat-value ${toneClass(card.tone)}`}>{card.value}</div>
                {card.hint ? <div className="tile-meta">{card.hint}</div> : null}
              </article>
            ))}
            {incidents.summary_cards.length === 0 ? (
              <article className="stat-card compact-stat-card">
                <div className="stat-label">Incident counters</div>
                <div className="stat-value compact-stat-value">n/a</div>
                <div className="tile-meta">the backend has not supplied incident summary cards yet</div>
              </article>
            ) : null}
          </div>

          <h4 className="subsection-title">Response rail</h4>
          <div className="stack tight-stack">
            {responsePlaybook.map((step) => (
              <article key={step} className="stack-card compact-stack-card">
                <p className="callout">{step}</p>
              </article>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Tape</div>
          <h3>Recent incidents</h3>
          {incidents.recent_incidents.length === 0 ? (
            <div className="stack">
              <article className="stack-card">
                <strong>No recent incident history</strong>
                <p className="callout">The recent tape will appear here once authority-core incident history is available.</p>
              </article>
            </div>
          ) : (
            <div className="table-shell">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Severity</th>
                    <th>Status</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {incidents.recent_incidents.map((incident) => (
                    <tr key={incident.id}>
                      <td>{incident.title}</td>
                      <td className={toneClass(severityTone(incident.severity))}>{incident.severity}</td>
                      <td>{incident.status}</td>
                      <td>{dateLabel(incident.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>
      </section>
    </>
  );
}

import { fetchIncidents } from "@/lib/dashboard";

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

export default async function IncidentsPage() {
  const incidents = await fetchIncidents();

  return (
    <>
      <section className="hero">
        <article className="panel hero-panel">
          <div className="chip-row">
            <span className="chip">
              Freshness <strong>{incidents.freshness.state}</strong>
            </span>
          </div>
          <h2 className="headline">Incidents And Approval Backlog</h2>
          <ul className="list">
            {incidents.highlights.map((highlight) => (
              <li key={highlight}>{highlight}</li>
            ))}
          </ul>
        </article>
      </section>

      <section className="card-grid">
        {incidents.summary_cards.map((card) => (
          <article key={card.label} className="stat-card">
            <div className="stat-label">{card.label}</div>
            <div className={`stat-value ${toneClass(card.tone)}`}>{card.value}</div>
          </article>
        ))}
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <h3>Active Incidents</h3>
          <div className="stack">
            {incidents.active_incidents.map((incident) => (
              <article key={incident.id} className="stack-card">
                <strong>{incident.title}</strong>
                <span>
                  {incident.severity} | {incident.status}
                </span>
                <p className="callout">{incident.summary}</p>
              </article>
            ))}
          </div>
        </article>

        <article className="panel">
          <h3>Pending Approvals</h3>
          <div className="stack">
            {incidents.pending_approvals.map((approval) => (
              <article key={approval.id} className="stack-card">
                <strong>{approval.approval_type}</strong>
                <span>
                  {approval.subject_id} | {approval.risk_level}
                </span>
                <p className="callout">Requested by {approval.requested_by}</p>
              </article>
            ))}
          </div>
        </article>
      </section>

      <section className="panel">
        <h3>Recent Incidents</h3>
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
                  <td>{incident.severity}</td>
                  <td>{incident.status}</td>
                  <td>{new Date(incident.created_at).toLocaleString("en-US")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

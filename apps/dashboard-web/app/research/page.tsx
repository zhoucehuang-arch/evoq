import { promoteResearchBriefAction } from "@/app/actions";
import { fetchResearchBriefs } from "@/lib/dashboard";
import type { StrategyResearchBriefCard } from "@/lib/types";

type ResearchPageProps = {
  searchParams?: Promise<{
    brief?: string;
    code?: string;
  }>;
};

type Tone = "good" | "warn" | "bad" | "neutral";

function toneClass(tone: Tone): string {
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

function auditTone(status: string): Tone {
  switch (status) {
    case "ready_for_spec":
      return "good";
    case "blocked":
      return "bad";
    case "needs_evidence":
      return "warn";
    default:
      return "neutral";
  }
}

function auditLabel(status: string): string {
  switch (status) {
    case "ready_for_spec":
      return "Ready";
    case "needs_evidence":
      return "Needs evidence";
    case "blocked":
      return "Blocked";
    default:
      return status || "Unknown";
  }
}

function dateLabel(value: string): string {
  return new Date(value).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function nextAction(brief: StrategyResearchBriefCard): string {
  if (brief.promoted_hypothesis_id) {
    return "Already promoted to a strategy hypothesis. Continue in the trading lifecycle.";
  }
  if (brief.audit_status === "ready_for_spec") {
    return "Promote this brief to a hypothesis, then build a deterministic spec and backtest plan.";
  }
  if (brief.audit_status === "needs_evidence") {
    return "Fill missing evidence, PIT controls, baseline, cost model, and attack-test references before promotion.";
  }
  if (brief.audit_status === "blocked") {
    return "Rewrite the idea so it stays inside research and validation gates. Do not promote while blocked.";
  }
  return "Review the audit notes and decide whether to enrich, rewrite, or archive this brief.";
}

function statusMessage(status?: string, code?: string): string | null {
  switch (status) {
    case "created":
      return "Research brief created. It is now visible in the lab.";
    case "promoted":
      return "Research brief promoted to a strategy hypothesis.";
    case "missing_id":
      return "The dashboard could not find the brief id to promote.";
    case "promote_failed":
      return `Promotion failed${code ? ` with HTTP ${code}` : ""}. The brief may still need evidence or may already be promoted.`;
    case "unavailable":
      return "The backend was unavailable, so the action did not complete.";
    default:
      return null;
  }
}

export default async function ResearchPage({ searchParams }: ResearchPageProps) {
  const params = searchParams ? await searchParams : undefined;
  const briefs = await fetchResearchBriefs();
  const ready = briefs.filter((brief) => brief.audit_status === "ready_for_spec").length;
  const needsEvidence = briefs.filter((brief) => brief.audit_status === "needs_evidence").length;
  const blocked = briefs.filter((brief) => brief.audit_status === "blocked").length;
  const promoted = briefs.filter((brief) => Boolean(brief.promoted_hypothesis_id)).length;
  const message = statusMessage(params?.brief, params?.code);

  return (
    <>
      <section className="metric-strip" aria-label="Research lab metrics">
        <article className="metric-card metric-card-good">
          <div className="metric-kicker">Ready</div>
          <div className="metric-value tone-good">{ready}</div>
          <div className="metric-note">briefs that can become hypotheses</div>
        </article>
        <article className="metric-card metric-card-warn">
          <div className="metric-kicker">Needs evidence</div>
          <div className="metric-value tone-warn">{needsEvidence}</div>
          <div className="metric-note">ideas that need more data discipline</div>
        </article>
        <article className="metric-card metric-card-bad">
          <div className="metric-kicker">Blocked</div>
          <div className="metric-value tone-bad">{blocked}</div>
          <div className="metric-note">briefs violating validation or risk gates</div>
        </article>
        <article className="metric-card metric-card-neutral">
          <div className="metric-kicker">Promoted</div>
          <div className="metric-value">{promoted}</div>
          <div className="metric-note">briefs already converted to hypotheses</div>
        </article>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <div className="section-kicker">Research Lab</div>
            <h2 className="headline">Turn ideas into auditable quant work.</h2>
            <p className="panel-copy">
              This is the first operational loop: owner idea in, research brief audited, then a ready brief can be promoted
              into a strategy hypothesis. Trading still remains behind later spec, backtest, paper, and approval gates.
            </p>
          </div>
          <div className="panel-badge-row">
            <span className="panel-badge">Idea intake</span>
            <span className="panel-badge">Evidence gate</span>
            <span className="panel-badge">Hypothesis promotion</span>
          </div>
        </div>

        {message ? (
          <div className={`form-status ${params?.brief === "promoted" || params?.brief === "created" ? "form-status-good" : "form-status-warn"}`}>
            {message}
          </div>
        ) : null}

        <div className="research-list">
          {briefs.map((brief) => {
            const tone = auditTone(brief.audit_status);
            const canPromote = brief.audit_status === "ready_for_spec" && !brief.promoted_hypothesis_id;

            return (
              <article key={brief.id} className="research-card">
                <div className="research-card-main">
                  <div className="research-card-top">
                    <div>
                      <div className="section-kicker">{brief.target_market.toUpperCase()} / {brief.opportunity_kind}</div>
                      <h3>{brief.title}</h3>
                    </div>
                    <span className={`status-pill status-pill-${tone}`}>{auditLabel(brief.audit_status)}</span>
                  </div>

                  <div className="research-facts">
                    <div>
                      <span>Readiness</span>
                      <strong className={toneClass(tone)}>{Math.round(brief.readiness_score * 100)}%</strong>
                    </div>
                    <div>
                      <span>Status</span>
                      <strong>{brief.status}</strong>
                    </div>
                    <div>
                      <span>Created</span>
                      <strong>{dateLabel(brief.created_at)}</strong>
                    </div>
                  </div>

                  <p className="callout">{nextAction(brief)}</p>

                  <div className="audit-note-list">
                    {brief.audit_notes.slice(0, 5).map((note) => (
                      <div key={note} className="audit-note">
                        {note}
                      </div>
                    ))}
                    {brief.audit_notes.length > 5 ? (
                      <div className="audit-note">+{brief.audit_notes.length - 5} more audit notes</div>
                    ) : null}
                  </div>
                </div>

                <div className="research-card-actions">
                  {brief.promoted_hypothesis_id ? (
                    <div className="action-note">
                      Hypothesis
                      <code>{brief.promoted_hypothesis_id}</code>
                    </div>
                  ) : canPromote ? (
                    <form action={promoteResearchBriefAction}>
                      <input type="hidden" name="brief_id" value={brief.id} />
                      <button className="primary-action" type="submit">
                        Promote
                      </button>
                    </form>
                  ) : (
                    <div className="action-note">Not promotable yet</div>
                  )}
                </div>
              </article>
            );
          })}
        </div>

        {briefs.length === 0 ? (
          <div className="empty-state">
            No research brief exists yet. Start from the Workbench page with a short idea or a detailed strategy design.
          </div>
        ) : null}
      </section>
    </>
  );
}

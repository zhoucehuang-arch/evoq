import { fetchTrading } from "@/lib/dashboard";
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

function metric(value: number | null | undefined, digits = 2, suffix = ""): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "n/a";
  }
  return `${value.toFixed(digits)}${suffix}`;
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

export default async function TradingPage() {
  const trading = await fetchTrading();
  const frontendStatus = trading.frontend_status;
  const readiness = trading.execution_readiness;
  const runningDomains = trading.domain_states.filter((state) => !state.is_paused).length;
  const activeWarnings = readiness.warnings.length;
  const blockedReasons = readiness.blocked_reasons.length;
  const optionWatchCount = trading.expiring_option_positions.length;

  const topMetrics = [
    {
      label: "Trading allowed",
      value: readiness.trading_allowed ? "Yes" : "No",
      tone: readiness.trading_allowed ? "good" : "warn",
      note: readiness.market_open ? "market is open and the gate is green" : "runtime is not currently clear to trade",
    },
    {
      label: "Production lanes",
      value: `${readiness.active_production_strategies}`,
      tone: readiness.active_production_strategies > 0 ? "good" : "warn",
      note: `${trading.strategy_lab.production_count} production specs in strategy lab`,
    },
    {
      label: "Provider incidents",
      value: `${readiness.open_provider_incidents}`,
      tone: readiness.open_provider_incidents > 0 ? "warn" : "good",
      note: `${trading.active_provider_incidents.length} active provider events visible`,
    },
    {
      label: "Domain control",
      value: `${runningDomains}/${trading.domain_states.length || 0}`,
      tone: blockedReasons > 0 ? "warn" : "neutral",
      note: `${trading.domain_states.length - runningDomains} paused domain lanes`,
    },
    {
      label: "Option watch",
      value: `${optionWatchCount}`,
      tone: optionWatchCount > 0 ? "warn" : "good",
      note: "option positions expiring inside the next 14 days",
    },
  ] as const;

  const executionChecks = [
    blockedReasons > 0
      ? `${blockedReasons} blocking reason${blockedReasons > 1 ? "s" : ""} still need resolution before the runtime should trust the trading gate.`
      : "No hard trading block is visible in the current readiness payload.",
    activeWarnings > 0
      ? `${activeWarnings} warning${activeWarnings > 1 ? "s" : ""} still need operator attention even if the system resumes trading.`
      : "No warnings are currently attached to the execution gate.",
    readiness.reconciliation_halt_triggered
      ? "A reconciliation halt is active, so execution should remain deliberately constrained."
      : "No reconciliation halt is currently tripped.",
    readiness.broker_snapshot_age_seconds === null
      ? "Broker state has no recent account snapshot yet."
      : `Latest broker snapshot is ${readiness.broker_snapshot_age_seconds}s old.`,
  ];

  return (
    <>
      <section className="metric-strip" aria-label="Trading metrics">
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
              <div className="section-kicker">Execution Desk</div>
              <h2 className="headline">Trading Control Surface</h2>
              <p className="panel-copy">
                This page should answer one question fast: can EvoQ safely trade right now, and if not, exactly what is
                blocking the path from research to governed execution.
              </p>
            </div>
            <div className="panel-badge-row">
              <span className="panel-badge">Freshness {trading.freshness.state}</span>
              <span className="panel-badge">Execution {readiness.status}</span>
              <span className="panel-badge">Session {readiness.market_session_label ?? "n/a"}</span>
            </div>
          </div>

          <div className="fact-grid">
            <article className="fact-card">
              <div className="fact-label">Trading allowed</div>
              <div className={`fact-value ${readiness.trading_allowed ? "tone-good" : "tone-warn"}`}>
                {readiness.trading_allowed ? "Yes" : "No"}
              </div>
              <div className="fact-meta">calendar {readiness.market_calendar}</div>
            </article>
            <article className="fact-card">
              <div className="fact-label">Market state</div>
              <div className={`fact-value ${readiness.market_open ? "tone-good" : "tone-warn"}`}>
                {readiness.market_open ? "Open" : "Closed"}
              </div>
              <div className="fact-meta">{readiness.market_session_label ?? "session unavailable"}</div>
            </article>
            <article className="fact-card">
              <div className="fact-label">Provider health</div>
              <div className="fact-value">{readiness.latest_provider_health ?? "unknown"}</div>
              <div className="fact-meta">{readiness.open_provider_incidents} provider incidents</div>
            </article>
            <article className="fact-card">
              <div className="fact-label">Reconciliation</div>
              <div className={`fact-value ${readiness.reconciliation_halt_triggered ? "tone-warn" : ""}`}>
                {readiness.reconciliation_status ?? "missing"}
              </div>
              <div className="fact-meta">
                {readiness.broker_snapshot_age_seconds === null ? "snapshot unavailable" : `${readiness.broker_snapshot_age_seconds}s snapshot age`}
              </div>
            </article>
          </div>

          <div className="bullet-cloud">
            {trading.highlights.map((highlight) => (
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
          <h3>Execution snapshot</h3>
          <div className="snapshot-grid">
            <article className="snapshot-cell">
              <div className="snapshot-label">Market</div>
              <div className="snapshot-value">{readiness.market_calendar}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Live candidates</div>
              <div className="snapshot-value">{trading.strategy_lab.live_candidate_count}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Paper running</div>
              <div className="snapshot-value">{trading.strategy_lab.paper_running_count}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Open orders</div>
              <div className="snapshot-value">{trading.recent_order_records.length}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Positions</div>
              <div className="snapshot-value">{trading.active_positions.length}</div>
            </article>
            <article className="snapshot-cell">
              <div className="snapshot-label">Intent queue</div>
              <div className="snapshot-value">{trading.recent_order_intents.length}</div>
            </article>
          </div>

          <h4 className="subsection-title">Immediate checks</h4>
          <div className="stack tight-stack">
            {executionChecks.map((item) => (
              <article key={item} className="stack-card compact-stack-card">
                <p className="callout">{item}</p>
              </article>
            ))}
          </div>
        </aside>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Policy</div>
          <h3>Allocation policy</h3>
          {trading.allocation_policy ? (
            <div className="fact-grid">
              <article className="fact-card">
                <div className="fact-label">Policy</div>
                <div className="fact-value">{trading.allocation_policy.policy_key}</div>
                <div className="fact-meta">{trading.allocation_policy.environment}</div>
              </article>
              <article className="fact-card">
                <div className="fact-label">Strategy cap</div>
                <div className="fact-value">
                  {metric(trading.allocation_policy.max_strategy_notional_pct * 100, 2, "%")}
                </div>
                <div className="fact-meta">max notional per strategy</div>
              </article>
              <article className="fact-card">
                <div className="fact-label">Gross cap</div>
                <div className="fact-value">
                  {metric(trading.allocation_policy.max_gross_exposure_pct * 100, 2, "%")}
                </div>
                <div className="fact-meta">portfolio gross exposure ceiling</div>
              </article>
              <article className="fact-card">
                <div className="fact-label">Position / Order caps</div>
                <div className="fact-value">
                  {trading.allocation_policy.max_open_positions} / {trading.allocation_policy.max_open_orders}
                </div>
                <div className="fact-meta">
                  short {trading.allocation_policy.allow_short ? "on" : "off"} | fractional {trading.allocation_policy.allow_fractional ? "on" : "off"}
                </div>
              </article>
            </div>
          ) : (
            <div className="stack">
              <article className="stack-card">
                <strong>No active allocation policy</strong>
                <p className="callout">The trading desk should not be trusted until an allocation policy is visible and current.</p>
              </article>
            </div>
          )}
        </article>

        <article className="panel">
          <div className="section-kicker">Strategy Lab</div>
          <h3>Lifecycle pressure</h3>
          <div className="runtime-mini-grid">
            <article className="stat-card compact-stat-card">
              <div className="stat-label">Hypotheses</div>
              <div className="stat-value compact-stat-value">{trading.strategy_lab.hypothesis_count}</div>
            </article>
            <article className="stat-card compact-stat-card">
              <div className="stat-label">Specs</div>
              <div className="stat-value compact-stat-value">{trading.strategy_lab.spec_count}</div>
            </article>
            <article className="stat-card compact-stat-card">
              <div className="stat-label">Paper candidates</div>
              <div className="stat-value compact-stat-value">{trading.strategy_lab.paper_candidate_count}</div>
            </article>
            <article className="stat-card compact-stat-card">
              <div className="stat-label">Paper running</div>
              <div className="stat-value compact-stat-value">{trading.strategy_lab.paper_running_count}</div>
            </article>
            <article className="stat-card compact-stat-card">
              <div className="stat-label">Live candidates</div>
              <div className="stat-value compact-stat-value">{trading.strategy_lab.live_candidate_count}</div>
            </article>
            <article className="stat-card compact-stat-card">
              <div className="stat-label">Production</div>
              <div className="stat-value compact-stat-value">{trading.strategy_lab.production_count}</div>
            </article>
          </div>

          {trading.summary_cards.length > 0 ? (
            <>
              <h4 className="subsection-title">Runtime counters</h4>
              <div className="runtime-mini-grid">
                {trading.summary_cards.map((card) => (
                  <article key={card.label} className="stat-card compact-stat-card">
                    <div className="stat-label">{card.label}</div>
                    <div className={`stat-value compact-stat-value ${toneClass(card.tone)}`}>{card.value}</div>
                    {card.hint ? <div className="tile-meta">{card.hint}</div> : null}
                  </article>
                ))}
              </div>
            </>
          ) : null}
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Account</div>
          <h3>Latest account snapshot</h3>
          {trading.latest_account_snapshot ? (
            <div className="fact-grid">
              <article className="fact-card">
                <div className="fact-label">Provider</div>
                <div className="fact-value">{trading.latest_account_snapshot.provider_key}</div>
                <div className="fact-meta">{trading.latest_account_snapshot.environment}</div>
              </article>
              <article className="fact-card">
                <div className="fact-label">Equity</div>
                <div className="fact-value">{metric(trading.latest_account_snapshot.equity, 2)}</div>
                <div className="fact-meta">cash {metric(trading.latest_account_snapshot.cash, 2)}</div>
              </article>
              <article className="fact-card">
                <div className="fact-label">Exposure</div>
                <div className="fact-value">{metric(trading.latest_account_snapshot.gross_exposure, 2)}</div>
                <div className="fact-meta">net {metric(trading.latest_account_snapshot.net_exposure, 2)}</div>
              </article>
              <article className="fact-card">
                <div className="fact-label">Positions / Orders</div>
                <div className="fact-value">
                  {trading.latest_account_snapshot.positions_count} / {trading.latest_account_snapshot.open_orders_count}
                </div>
                <div className="fact-meta">captured {dateLabel(trading.latest_account_snapshot.source_captured_at)}</div>
              </article>
            </div>
          ) : (
            <div className="stack">
              <article className="stack-card">
                <strong>No broker account snapshot recorded</strong>
                <p className="callout">Bring up broker sync and account capture before treating this desk as operator-ready.</p>
              </article>
            </div>
          )}
        </article>

        <article className="panel">
          <div className="section-kicker">Risk</div>
          <h3>Latest reconciliation</h3>
          {trading.latest_reconciliation ? (
            <div className="fact-grid">
              <article className="fact-card">
                <div className="fact-label">Status</div>
                <div className={`fact-value ${trading.latest_reconciliation.status === "matched" ? "tone-good" : "tone-warn"}`}>
                  {trading.latest_reconciliation.status}
                </div>
                <div className="fact-meta">checked {dateLabel(trading.latest_reconciliation.checked_at)}</div>
              </article>
              <article className="fact-card">
                <div className="fact-label">Equity delta</div>
                <div className="fact-value">
                  {metric(trading.latest_reconciliation.equity_delta_abs, 2)} / {metric(trading.latest_reconciliation.equity_delta_pct, 2, "%")}
                </div>
                <div className="fact-meta">
                  pos {trading.latest_reconciliation.position_delta_count} | orders {trading.latest_reconciliation.order_delta_count}
                </div>
              </article>
              <article className="fact-card">
                <div className="fact-label">Halt triggered</div>
                <div className={`fact-value ${trading.latest_reconciliation.halt_triggered ? "tone-warn" : "tone-good"}`}>
                  {trading.latest_reconciliation.halt_triggered ? "Yes" : "No"}
                </div>
                <div className="fact-meta">{trading.latest_reconciliation.blocking_reason ?? "no blocking reason recorded"}</div>
              </article>
            </div>
          ) : (
            <div className="stack">
              <article className="stack-card">
                <strong>No reconciliation result recorded</strong>
                <p className="callout">The desk is less trustworthy until reconciliation has produced at least one durable result.</p>
              </article>
            </div>
          )}
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Controls</div>
          <h3>Domain controls</h3>
          <div className="tile-grid">
            {trading.domain_states.map((state) => (
              <article key={state.domain} className="tile">
                <div className="tile-label">{state.domain}</div>
                <div className={`tile-value ${state.is_paused ? "tone-warn" : "tone-good"}`}>
                  {state.is_paused ? "Paused" : "Running"}
                </div>
                <div className="tile-meta">pending approvals {state.pending_approval_count}</div>
                <div className="tile-meta">active overrides {state.override_count}</div>
                {state.latest_reason ? <p className="callout">{state.latest_reason}</p> : null}
              </article>
            ))}
            {trading.domain_states.length === 0 ? <div className="tile-meta">No governed domain state yet.</div> : null}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Broker</div>
          <h3>Sync and provider incidents</h3>
          <div className="stack">
            {trading.latest_broker_sync ? (
              <article className="stack-card">
                <strong>
                  {trading.latest_broker_sync.status} | {trading.latest_broker_sync.broker_adapter}
                </strong>
                <span>{trading.latest_broker_sync.sync_scope}</span>
                <p className="callout">
                  Synced {trading.latest_broker_sync.synced_orders_count} / {trading.latest_broker_sync.synced_positions_count}
                  {" | "}
                  unmanaged {trading.latest_broker_sync.unmanaged_orders_count} / {trading.latest_broker_sync.unmanaged_positions_count}
                  {" | "}
                  missing internal {trading.latest_broker_sync.missing_internal_orders_count} / {trading.latest_broker_sync.missing_internal_positions_count}
                </p>
              </article>
            ) : (
              <article className="stack-card">
                <strong>No broker sync run recorded</strong>
                <p className="callout">Broker synchronization should appear here once the trading control plane is connected.</p>
              </article>
            )}

            {trading.active_provider_incidents.map((incident) => (
              <article key={incident.id} className="stack-card">
                <strong>
                  {incident.provider_key} / {incident.title}
                </strong>
                <span>
                  {incident.severity} | {incident.status}
                </span>
                <p className="callout">Detected {dateLabel(incident.detected_at)}</p>
              </article>
            ))}
            {trading.active_provider_incidents.length === 0 ? (
              <article className="stack-card">
                <strong>No active provider incidents</strong>
                <p className="callout">Provider connectivity is currently not reporting any active incident record.</p>
              </article>
            ) : null}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Exposure</div>
          <h3>Active positions</h3>
          <div className="stack">
            {trading.active_positions.map((position) => (
              <article key={position.id} className="stack-card">
                <strong>
                  {position.symbol} / {position.direction} / {position.asset_type}
                </strong>
                <span>
                  qty {metric(position.quantity, 4)} | entry {metric(position.avg_entry_price, 2)} | mark {metric(position.market_price, 2)}
                </span>
                <p className="callout">
                  notional {metric(position.notional_value, 2)} | realized {metric(position.realized_pnl, 2)} | unrealized {metric(position.unrealized_pnl, 2)}
                  {position.underlying_symbol ? ` | underlying ${position.underlying_symbol}` : ""}
                </p>
              </article>
            ))}
            {trading.active_positions.length === 0 ? <div className="tile-meta">No active positions.</div> : null}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Orders</div>
          <h3>Recent order records</h3>
          <div className="stack">
            {trading.recent_order_records.map((orderRecord) => (
              <article key={orderRecord.id} className="stack-card">
                <strong>
                  {orderRecord.symbol} / {orderRecord.side} / {orderRecord.asset_type}
                </strong>
                <span>
                  {orderRecord.status} | qty {metric(orderRecord.quantity, 4)} | filled {metric(orderRecord.filled_quantity, 4)}
                </span>
                <p className="callout">
                  broker {orderRecord.broker_order_id}
                  {orderRecord.client_order_id ? ` | client ${orderRecord.client_order_id}` : ""}
                  {orderRecord.parent_order_record_id ? ` | replaces ${orderRecord.parent_order_record_id}` : ""}
                  {` | legs ${orderRecord.leg_count} | effect ${orderRecord.position_effect} | fill ${metric(orderRecord.avg_fill_price, 2)} | updated ${dateLabel(orderRecord.broker_updated_at ?? orderRecord.submitted_at)}`}
                </p>
              </article>
            ))}
            {trading.recent_order_records.length === 0 ? <div className="tile-meta">No order records yet.</div> : null}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Options</div>
          <h3>Expiring option watch</h3>
          <div className="stack">
            {trading.expiring_option_positions.map((position) => (
              <article key={position.id} className="stack-card">
                <strong>
                  {position.symbol}
                  {position.underlying_symbol ? ` / ${position.underlying_symbol}` : ""}
                </strong>
                <span>
                  {position.direction} | qty {metric(position.quantity, 4)} | {position.days_to_expiry} days
                </span>
                <p className="callout">
                  expires {dateLabel(position.expiration_date)} | mark {metric(position.market_price, 2)} | unrealized {metric(position.unrealized_pnl, 2)}
                </p>
              </article>
            ))}
            {trading.expiring_option_positions.length === 0 ? (
              <div className="tile-meta">No option positions expire inside the next 14 days.</div>
            ) : null}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Lifecycle</div>
          <h3>Recent option events</h3>
          <div className="stack">
            {trading.recent_option_events.map((event) => (
              <article key={event.id} className="stack-card">
                <strong>
                  {event.event_type} / {event.symbol}
                </strong>
                <span>
                  qty {metric(event.quantity, 4)} | {event.review_required ? "review required" : "applied"}
                </span>
                <p className="callout">
                  price {metric(event.event_price, 2)} | cash flow {metric(event.cash_flow, 2)} | at {dateLabel(event.occurred_at)}
                  {event.notes ? ` | ${event.notes}` : ""}
                </p>
              </article>
            ))}
            {trading.recent_option_events.length === 0 ? (
              <div className="tile-meta">No option lifecycle events recorded yet.</div>
            ) : null}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <div className="section-kicker">Validation</div>
          <h3>Strategy specs and backtests</h3>
          <div className="stack">
            {trading.recent_specs.map((spec) => (
              <article key={spec.id} className="stack-card">
                <strong>
                  {spec.spec_code} / {spec.title}
                </strong>
                <span>{spec.target_market}</span>
                <p className="callout">
                  stage {spec.current_stage} | backtest {spec.latest_backtest_gate ?? "n/a"} | paper {spec.latest_paper_gate ?? "n/a"}
                </p>
              </article>
            ))}
            {trading.recent_backtests.map((backtest) => (
              <article key={backtest.id} className="stack-card">
                <strong>{backtest.strategy_spec_id}</strong>
                <span>
                  {backtest.gate_result} / sample {backtest.sample_size}
                </span>
                <p className="callout">
                  return {metric(backtest.total_return_pct, 2, "%")} | sharpe {metric(backtest.sharpe_ratio)} | max DD {metric(backtest.max_drawdown_pct, 2, "%")}
                </p>
              </article>
            ))}
            {trading.recent_specs.length === 0 && trading.recent_backtests.length === 0 ? (
              <div className="tile-meta">No recent strategy spec or backtest evidence yet.</div>
            ) : null}
          </div>
        </article>

        <article className="panel">
          <div className="section-kicker">Paper path</div>
          <h3>Paper runs and order intents</h3>
          <div className="stack">
            {trading.recent_paper_runs.map((paperRun) => (
              <article key={paperRun.id} className="stack-card">
                <strong>
                  {paperRun.deployment_label} / {paperRun.strategy_spec_id}
                </strong>
                <span>
                  {paperRun.gate_result} / {paperRun.monitoring_days} days
                </span>
                <p className="callout">
                  net PnL {metric(paperRun.net_pnl_pct, 2, "%")} | profit factor {metric(paperRun.profit_factor)} | max DD {metric(paperRun.max_drawdown_pct, 2, "%")}
                </p>
              </article>
            ))}
            {trading.recent_order_intents.map((intent) => (
              <article key={intent.id} className="stack-card">
                <strong>
                  {intent.symbol} / {intent.side} / {intent.asset_type}
                </strong>
                <span>
                  {metric(intent.quantity, 4)} @ {metric(intent.reference_price, 2)} | {intent.status}
                </span>
                <p className="callout">
                  notional {metric(intent.requested_notional, 2)} | legs {intent.leg_count} | effect {intent.position_effect} | adapter {intent.broker_adapter}
                  {intent.decision_reason ? ` | ${intent.decision_reason}` : ""}
                </p>
              </article>
            ))}
            {trading.recent_paper_runs.length === 0 && trading.recent_order_intents.length === 0 ? (
              <div className="tile-meta">No recent paper-run or order-intent evidence yet.</div>
            ) : null}
          </div>
        </article>
      </section>
    </>
  );
}

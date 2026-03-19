import { fetchTrading } from "@/lib/dashboard";

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
  const readiness = trading.execution_readiness;

  return (
    <>
      <section className="hero">
        <article className="panel hero-panel">
          <div className="chip-row">
            <span className="chip">
              Freshness <strong>{trading.freshness.state}</strong>
            </span>
            <span className="chip">
              Execution <strong>{readiness.status}</strong>
            </span>
            <span className="chip">
              Session <strong>{readiness.market_session_label ?? "n/a"}</strong>
            </span>
          </div>
          <h2 className="headline">Trading Control Surface</h2>
          <ul className="list">
            {trading.highlights.map((highlight) => (
              <li key={highlight}>{highlight}</li>
            ))}
          </ul>
        </article>
      </section>

      <section className="card-grid">
        {trading.summary_cards.map((card) => (
          <article key={card.label} className="stat-card">
            <div className="stat-label">{card.label}</div>
            <div className={`stat-value ${toneClass(card.tone)}`}>{card.value}</div>
            {card.hint ? <div className="callout">{card.hint}</div> : null}
          </article>
        ))}
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <h3>Execution Readiness</h3>
          <div className="tile-grid">
            <article className="tile">
              <div className="tile-label">Trading allowed</div>
              <div className={`tile-value ${readiness.trading_allowed ? "tone-good" : "tone-warn"}`}>
                {readiness.trading_allowed ? "Yes" : "No"}
              </div>
              <div className="tile-meta">Calendar: {readiness.market_calendar}</div>
            </article>
            <article className="tile">
              <div className="tile-label">Market open</div>
              <div className={`tile-value ${readiness.market_open ? "tone-good" : "tone-warn"}`}>
                {readiness.market_open ? "Open" : "Closed"}
              </div>
              <div className="tile-meta">Session: {readiness.market_session_label ?? "n/a"}</div>
            </article>
            <article className="tile">
              <div className="tile-label">Provider health</div>
              <div className="tile-value">{readiness.latest_provider_health ?? "unknown"}</div>
              <div className="tile-meta">Open incidents: {readiness.open_provider_incidents}</div>
            </article>
            <article className="tile">
              <div className="tile-label">Broker snapshot age</div>
              <div className="tile-value">
                {readiness.broker_snapshot_age_seconds === null ? "n/a" : `${readiness.broker_snapshot_age_seconds}s`}
              </div>
              <div className="tile-meta">Reconciliation: {readiness.reconciliation_status ?? "missing"}</div>
            </article>
          </div>
          {readiness.blocked_reasons.length > 0 ? (
            <div className="stack">
              {readiness.blocked_reasons.map((reason) => (
                <article key={reason} className="stack-card">
                  <strong className="tone-warn">Blocked</strong>
                  <p className="callout">{reason}</p>
                </article>
              ))}
            </div>
          ) : null}
          {readiness.warnings.length > 0 ? (
            <div className="stack">
              {readiness.warnings.map((warning) => (
                <article key={warning} className="stack-card">
                  <strong>Warning</strong>
                  <p className="callout">{warning}</p>
                </article>
              ))}
            </div>
          ) : null}
        </article>

        <article className="panel">
          <h3>Domain Controls</h3>
          <div className="tile-grid">
            {trading.domain_states.map((state) => (
              <article key={state.domain} className="tile">
                <div className="tile-label">{state.domain}</div>
                <div className={`tile-value ${state.is_paused ? "tone-warn" : "tone-good"}`}>
                  {state.is_paused ? "Paused" : "Running"}
                </div>
                <div className="tile-meta">Pending approvals: {state.pending_approval_count}</div>
                <div className="tile-meta">Active overrides: {state.override_count}</div>
                {state.latest_reason ? <p className="callout">{state.latest_reason}</p> : null}
              </article>
            ))}
            {trading.domain_states.length === 0 ? <div className="tile-meta">No governed domain state yet.</div> : null}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <h3>Latest Account Snapshot</h3>
          {trading.latest_account_snapshot ? (
            <div className="tile-grid">
              <article className="tile">
                <div className="tile-label">Provider</div>
                <div className="tile-value">{trading.latest_account_snapshot.provider_key}</div>
                <div className="tile-meta">{trading.latest_account_snapshot.environment}</div>
              </article>
              <article className="tile">
                <div className="tile-label">Equity</div>
                <div className="tile-value">{metric(trading.latest_account_snapshot.equity, 2)}</div>
                <div className="tile-meta">Cash {metric(trading.latest_account_snapshot.cash, 2)}</div>
              </article>
              <article className="tile">
                <div className="tile-label">Exposure</div>
                <div className="tile-value">{metric(trading.latest_account_snapshot.gross_exposure, 2)}</div>
                <div className="tile-meta">Net {metric(trading.latest_account_snapshot.net_exposure, 2)}</div>
              </article>
              <article className="tile">
                <div className="tile-label">Positions / Orders</div>
                <div className="tile-value">
                  {trading.latest_account_snapshot.positions_count} / {trading.latest_account_snapshot.open_orders_count}
                </div>
                <div className="tile-meta">Captured {dateLabel(trading.latest_account_snapshot.source_captured_at)}</div>
              </article>
            </div>
          ) : (
            <div className="tile-meta">No broker account snapshot recorded yet.</div>
          )}
        </article>

        <article className="panel">
          <h3>Latest Reconciliation</h3>
          {trading.latest_reconciliation ? (
            <div className="tile-grid">
              <article className="tile">
                <div className="tile-label">Status</div>
                <div className={`tile-value ${trading.latest_reconciliation.status === "matched" ? "tone-good" : "tone-warn"}`}>
                  {trading.latest_reconciliation.status}
                </div>
                <div className="tile-meta">Checked {dateLabel(trading.latest_reconciliation.checked_at)}</div>
              </article>
              <article className="tile">
                <div className="tile-label">Equity delta</div>
                <div className="tile-value">
                  {metric(trading.latest_reconciliation.equity_delta_abs, 2)} / {metric(trading.latest_reconciliation.equity_delta_pct, 2, "%")}
                </div>
                <div className="tile-meta">
                  Pos {trading.latest_reconciliation.position_delta_count} | Orders {trading.latest_reconciliation.order_delta_count}
                </div>
              </article>
              <article className="tile">
                <div className="tile-label">Halt triggered</div>
                <div className={`tile-value ${trading.latest_reconciliation.halt_triggered ? "tone-warn" : "tone-good"}`}>
                  {trading.latest_reconciliation.halt_triggered ? "Yes" : "No"}
                </div>
                {trading.latest_reconciliation.blocking_reason ? (
                  <p className="callout">{trading.latest_reconciliation.blocking_reason}</p>
                ) : null}
              </article>
            </div>
          ) : (
            <div className="tile-meta">No reconciliation result recorded yet.</div>
          )}
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <h3>Latest Broker Sync</h3>
          {trading.latest_broker_sync ? (
            <div className="tile-grid">
              <article className="tile">
                <div className="tile-label">Status</div>
                <div className={`tile-value ${trading.latest_broker_sync.status === "synchronized" ? "tone-good" : "tone-warn"}`}>
                  {trading.latest_broker_sync.status}
                </div>
                <div className="tile-meta">
                  {trading.latest_broker_sync.broker_adapter} / {trading.latest_broker_sync.sync_scope}
                </div>
              </article>
              <article className="tile">
                <div className="tile-label">Synced</div>
                <div className="tile-value">
                  {trading.latest_broker_sync.synced_orders_count} / {trading.latest_broker_sync.synced_positions_count}
                </div>
                <div className="tile-meta">Orders / Positions</div>
              </article>
              <article className="tile">
                <div className="tile-label">Unmanaged</div>
                <div className="tile-value">
                  {trading.latest_broker_sync.unmanaged_orders_count} / {trading.latest_broker_sync.unmanaged_positions_count}
                </div>
                <div className="tile-meta">Orders / Positions</div>
              </article>
              <article className="tile">
                <div className="tile-label">Missing internal</div>
                <div className="tile-value">
                  {trading.latest_broker_sync.missing_internal_orders_count} / {trading.latest_broker_sync.missing_internal_positions_count}
                </div>
                <div className="tile-meta">Orders / Positions</div>
              </article>
            </div>
          ) : (
            <div className="tile-meta">No broker sync run recorded yet.</div>
          )}
        </article>

        <article className="panel">
          <h3>Provider Incidents</h3>
          <div className="stack">
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
              <div className="tile-meta">No active provider incidents.</div>
            ) : null}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <h3>Recent Market Sessions</h3>
          <div className="stack">
            {trading.recent_market_sessions.map((sessionState) => (
              <article key={sessionState.id} className="stack-card">
                <strong>
                  {sessionState.market_calendar} / {sessionState.session_label}
                </strong>
                <span>
                  {sessionState.is_market_open ? "Market open" : "Market closed"} |{" "}
                  {sessionState.trading_allowed ? "Trading allowed" : "Trading blocked"}
                </span>
                <p className="callout">
                  Next open {dateLabel(sessionState.next_open_at)} | Next close {dateLabel(sessionState.next_close_at)}
                </p>
              </article>
            ))}
            {trading.recent_market_sessions.length === 0 ? (
              <div className="tile-meta">No market session snapshots yet.</div>
            ) : null}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <h3>Allocation Policy</h3>
          {trading.allocation_policy ? (
            <div className="tile-grid">
              <article className="tile">
                <div className="tile-label">Policy</div>
                <div className="tile-value">{trading.allocation_policy.policy_key}</div>
                <div className="tile-meta">{trading.allocation_policy.environment}</div>
              </article>
              <article className="tile">
                <div className="tile-label">Strategy cap</div>
                <div className="tile-value">{metric(trading.allocation_policy.max_strategy_notional_pct * 100, 2, "%")}</div>
                <div className="tile-meta">Max notional per strategy</div>
              </article>
              <article className="tile">
                <div className="tile-label">Gross exposure cap</div>
                <div className="tile-value">{metric(trading.allocation_policy.max_gross_exposure_pct * 100, 2, "%")}</div>
                <div className="tile-meta">Portfolio gross exposure ceiling</div>
              </article>
              <article className="tile">
                <div className="tile-label">Position / Order caps</div>
                <div className="tile-value">
                  {trading.allocation_policy.max_open_positions} / {trading.allocation_policy.max_open_orders}
                </div>
                <div className="tile-meta">
                  Short {trading.allocation_policy.allow_short ? "on" : "off"} | Fractional {trading.allocation_policy.allow_fractional ? "on" : "off"}
                </div>
              </article>
            </div>
          ) : (
            <div className="tile-meta">No active allocation policy found.</div>
          )}
        </article>

        <article className="panel">
          <h3>Recent Order Intents</h3>
          <div className="stack">
            {trading.recent_order_intents.map((intent) => (
              <article key={intent.id} className="stack-card">
                <strong>
                  {intent.symbol} / {intent.side} / {intent.asset_type}
                </strong>
                <span>
                  {metric(intent.quantity, 4)} @ {metric(intent.reference_price, 2)} | {intent.status}
                </span>
                <p className="callout">
                  Notional {metric(intent.requested_notional, 2)} | Legs {intent.leg_count} | Effect {intent.position_effect} | Adapter {intent.broker_adapter}
                  {intent.decision_reason ? ` | ${intent.decision_reason}` : ""}
                </p>
              </article>
            ))}
            {trading.recent_order_intents.length === 0 ? <div className="tile-meta">No order intents yet.</div> : null}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <h3>Active Positions</h3>
          <div className="stack">
            {trading.active_positions.map((position) => (
              <article key={position.id} className="stack-card">
                <strong>
                  {position.symbol} / {position.direction} / {position.asset_type}
                </strong>
                <span>
                  Qty {metric(position.quantity, 4)} | Entry {metric(position.avg_entry_price, 2)} | Mark {metric(position.market_price, 2)}
                </span>
                <p className="callout">
                  Notional {metric(position.notional_value, 2)} | Realized {metric(position.realized_pnl, 2)} | Unrealized {metric(position.unrealized_pnl, 2)}
                  {position.underlying_symbol ? ` | Underlying ${position.underlying_symbol}` : ""}
                </p>
              </article>
            ))}
            {trading.active_positions.length === 0 ? <div className="tile-meta">No active positions.</div> : null}
          </div>
        </article>

        <article className="panel">
          <h3>Recent Order Records</h3>
          <div className="stack">
            {trading.recent_order_records.map((orderRecord) => (
              <article key={orderRecord.id} className="stack-card">
                <strong>
                  {orderRecord.symbol} / {orderRecord.side} / {orderRecord.asset_type}
                </strong>
                <span>
                  {orderRecord.status} | Qty {metric(orderRecord.quantity, 4)} | Filled {metric(orderRecord.filled_quantity, 4)}
                </span>
                <p className="callout">
                  Broker {orderRecord.broker_order_id}
                  {orderRecord.client_order_id ? ` | Client ${orderRecord.client_order_id}` : ""}
                  {orderRecord.parent_order_record_id ? ` | Replaces ${orderRecord.parent_order_record_id}` : ""}
                  {` | Legs ${orderRecord.leg_count} | Effect ${orderRecord.position_effect} | Fill ${metric(orderRecord.avg_fill_price, 2)} | Updated ${dateLabel(orderRecord.broker_updated_at ?? orderRecord.submitted_at)}`}
                </p>
              </article>
            ))}
            {trading.recent_order_records.length === 0 ? <div className="tile-meta">No order records yet.</div> : null}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <h3>Expiring Options</h3>
          <div className="stack">
            {trading.expiring_option_positions.map((position) => (
              <article key={position.id} className="stack-card">
                <strong>
                  {position.symbol}
                  {position.underlying_symbol ? ` / ${position.underlying_symbol}` : ""}
                </strong>
                <span>
                  {position.direction} | Qty {metric(position.quantity, 4)} | {position.days_to_expiry} days
                </span>
                <p className="callout">
                  Expires {dateLabel(position.expiration_date)} | Mark {metric(position.market_price, 2)} | Unrealized {metric(position.unrealized_pnl, 2)}
                </p>
              </article>
            ))}
            {trading.expiring_option_positions.length === 0 ? (
              <div className="tile-meta">No option positions expire within the next 14 days.</div>
            ) : null}
          </div>
        </article>

        <article className="panel">
          <h3>Recent Option Events</h3>
          <div className="stack">
            {trading.recent_option_events.map((event) => (
              <article key={event.id} className="stack-card">
                <strong>
                  {event.event_type} / {event.symbol}
                </strong>
                <span>
                  Qty {metric(event.quantity, 4)} | {event.review_required ? "Review required" : "Applied"}
                </span>
                <p className="callout">
                  Price {metric(event.event_price, 2)} | Cash flow {metric(event.cash_flow, 2)} | At {dateLabel(event.occurred_at)}
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
          <h3>Strategy Lab</h3>
          <div className="tile-grid">
            <article className="tile">
              <div className="tile-label">Hypotheses</div>
              <div className="tile-value">{trading.strategy_lab.hypothesis_count}</div>
            </article>
            <article className="tile">
              <div className="tile-label">Specs</div>
              <div className="tile-value">{trading.strategy_lab.spec_count}</div>
            </article>
            <article className="tile">
              <div className="tile-label">Paper candidates</div>
              <div className="tile-value">{trading.strategy_lab.paper_candidate_count}</div>
            </article>
            <article className="tile">
              <div className="tile-label">Paper running</div>
              <div className="tile-value">{trading.strategy_lab.paper_running_count}</div>
            </article>
            <article className="tile">
              <div className="tile-label">Live candidates</div>
              <div className="tile-value">{trading.strategy_lab.live_candidate_count}</div>
            </article>
            <article className="tile">
              <div className="tile-label">Production</div>
              <div className="tile-value">{trading.strategy_lab.production_count}</div>
            </article>
          </div>
        </article>

        <article className="panel">
          <h3>Recent Strategy Specs</h3>
          <div className="stack">
            {trading.recent_specs.map((spec) => (
              <article key={spec.id} className="stack-card">
                <strong>
                  {spec.spec_code} / {spec.title}
                </strong>
                <span>{spec.target_market}</span>
                <p className="callout">
                  Stage {spec.current_stage} | Backtest {spec.latest_backtest_gate ?? "n/a"} | Paper {spec.latest_paper_gate ?? "n/a"}
                </p>
              </article>
            ))}
            {trading.recent_specs.length === 0 ? <div className="tile-meta">No durable strategy specs yet.</div> : null}
          </div>
        </article>
      </section>

      <section className="detail-grid two-col">
        <article className="panel">
          <h3>Recent Backtests</h3>
          <div className="stack">
            {trading.recent_backtests.map((backtest) => (
              <article key={backtest.id} className="stack-card">
                <strong>{backtest.strategy_spec_id}</strong>
                <span>
                  {backtest.gate_result} / sample {backtest.sample_size}
                </span>
                <p className="callout">
                  Return {metric(backtest.total_return_pct, 2, "%")} | Sharpe {metric(backtest.sharpe_ratio)} | Max DD {metric(backtest.max_drawdown_pct, 2, "%")}
                </p>
              </article>
            ))}
            {trading.recent_backtests.length === 0 ? <div className="tile-meta">No backtest records yet.</div> : null}
          </div>
        </article>

        <article className="panel">
          <h3>Recent Paper Runs</h3>
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
                  Net PnL {metric(paperRun.net_pnl_pct, 2, "%")} | Profit factor {metric(paperRun.profit_factor)} | Max DD {metric(paperRun.max_drawdown_pct, 2, "%")}
                </p>
              </article>
            ))}
            {trading.recent_paper_runs.length === 0 ? <div className="tile-meta">No paper-trading records yet.</div> : null}
          </div>
        </article>
      </section>
    </>
  );
}

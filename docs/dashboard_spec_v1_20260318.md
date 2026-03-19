# Dashboard Spec v1 · learned from nadah-dashboard.vercel.app

Generated: 2026-03-18 UTC
Owner proposal: wattson

## Source snapshot
- HTML snapshot saved at: `/root/.openclaw/workspace/bot-b/operator/memory/runtime/nadah_dashboard_20260318.html`
- External site title: `NADAH TERMINAL v3`
- Source-derived top-level data keys:
  - `account`
  - `equity_history`
  - `benchmark_comparison`
  - `family_attribution`
  - `universe`
  - `trades`
  - `cycle`
  - `generated_at`

## What is good about the reference dashboard
1. KPI-first layout
   - total equity
   - daily pnl
   - cash
   - exposure
   - total pnl
2. Time-series first, not just static numbers
   - equity history
   - benchmark comparison
   - session breakdown
3. Strategy attribution is visible
   - family-level contributions
   - benchmark-relative performance
4. Risk is explicit
   - long/short/hedge exposure
   - net/gross exposure
   - concentration / top winners / top losers
5. Positions and watchlist are separated
6. Data freshness is explicit via `generated_at`

## Proposed System B dashboard information architecture

### A. Admin Overview
Purpose: one-screen management summary for remote viewing.

Required modules:
1. KPI cards
   - total_equity
   - day_pnl_dollar
   - day_pnl_pct
   - cash
   - buying_power
   - exposure_ratio
   - positions_count
   - open_orders_count
   - data_freshness_status
   - generated_at
2. Equity curve
   - intraday
   - 5d
   - 30d
3. Benchmark panel
   - strategy_vs_spy
   - strategy_vs_qqq
4. Session breakdown
   - preopen
   - first_30m_after_open
   - regular_session_midday
   - final_hour
   - postmarket
5. Strategy family attribution
   - momentum
   - mean_reversion
   - event/options
   - news/sentiment
   - confluence/basket
6. Risk matrix
   - net exposure
   - gross exposure
   - concentration
   - max drawdown (windowed)
   - top winner / top loser
   - risk regime: risk_up | normal | risk_down | halt
7. Positions table
   - symbol
   - qty
   - side
   - avg_entry
   - current_price
   - market_value
   - unrealized_pnl
   - pnl_pct
8. Watchlist / opportunity pool
   - candidate symbol
   - score
   - status: selected | rejected | watch
   - rejection_reason / next_action
9. Activity log
   - signal accepted/rejected
   - risk change
   - order submit/fill/cancel
   - deployment / withdrawal events

### B. Runtime Detail Layer
Purpose: internal diagnostics and machine validation.

Required modules:
- execution snapshot
- data freshness / quality gate
- order flow state
- signal ranking state
- source health
- error / blocker log

### C. Learning / Research Layer
Purpose: feed back into A-side evolution.

Required modules:
- family attribution over time
- session attribution over time
- rejection reasons distribution
- alpha proxy vs benchmark
- strategy decay / regime drift indicators

## Minimum viable data contract for v1

```json
{
  "generated_at": "ISO-8601",
  "freshness": {
    "overall": "PASS|WARN|FAIL",
    "captured_age_seconds": 0,
    "source_age_seconds": 0
  },
  "account": {
    "equity": 0,
    "cash": 0,
    "buying_power": 0,
    "day_pnl_dollar": 0,
    "day_pnl_pct": 0,
    "exposure_ratio": 0,
    "positions_count": 0,
    "open_orders_count": 0
  },
  "equity_history": [],
  "benchmark_comparison": {},
  "family_attribution": [],
  "positions": [],
  "watchlist": [],
  "activity_log": []
}
```

## Delivery target
- Build a remote-access dashboard for admin.
- Deploy on Vercel.
- Must be readable on desktop and mobile.
- Must expose freshness explicitly.
- Must never present stale data as real-time without a freshness warning.

## Acceptance criteria
1. Vercel URL loads successfully from external network.
2. Page shows non-empty KPI cards.
3. Page shows data freshness / generated_at.
4. Page shows positions + watchlist + activity log.
5. Page shows benchmark comparison and strategy-family attribution.
6. If data source breaks, UI degrades visibly instead of faking normal.
7. Admin can use it remotely without opening logs or repo files.

## Suggested build sequence for wattson
1. Download and study reference HTML snapshot.
2. Define `dashboard_schema_v1.json`.
3. Build local static/mock version first.
4. Wire real runtime data sources.
5. Add freshness gate and degraded-state UI.
6. Deploy to Vercel.
7. Validate external accessibility.
8. Run a continuous repair loop until all data + display paths are stable.

## Notes
- Do not fake real-time.
- Prefer explicit degraded mode over silent failure.
- Admin-facing language should be Chinese.
- Internal code/docs can be English.

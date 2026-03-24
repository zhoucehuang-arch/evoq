# Runtime Schedules

## System A: Self-Evolution System (24/7 Operation)

### Cycle Structure (Compressed Timeline)

| Cycle Type | Frequency | Duration | Content |
|---|---|---|---|
| Micro-cycle | Every 2h | 2h | Strategy discovery / optimization / capability evolution |
| Synthesis cycle | Every 6h | ~30min | Principle synthesis + cross-strategy analysis |
| Evolution cycle | Daily ~22:00 EST | ~1.5h | Architecture debate + meta-reflection + threshold review |

**Daily average: ~12 micro-cycles** (Mode A ~7, Mode B ~2, Mode C ~3)

### Trading Days (Mon-Fri, US stock market open days)

| Time (EST) | Cycle | Content |
|---|---|---|
| 00:00-04:00 | Micro x2 | Mode A/C: overnight research, capability evolution |
| 04:00 | Synthesis | First synthesis of the day |
| 04:00-09:30 | Micro x2-3 | Mode A/C: pre-market research, event-calendar scan |
| 09:30-10:00 | Synthesis | Pre-market synthesis |
| 09:30-16:00 | Micro x3 | Mode A/B: market hours, real-time data available |
| 16:00 | Synthesis | Post-market synthesis + read System B daily data |
| 16:00-22:00 | Micro x3 | Mode A/B/C: after-hours cycles |
| 22:00 | Evolution | Daily architecture debate + meta-reflection |
| 22:00-24:00 | Micro x1 | Mode A/C: late-night research |

### Non-Trading Days (Weekends, US stock market holidays)

| Time (EST) | Cycle | Content |
|---|---|---|
| All day | Micro x12 | Higher Mode C allocation (~40%): deep capability evolution, cross-disciplinary research |
| 04:00, 10:00, 16:00, 22:00 | Synthesis x4 | Standard synthesis cycles |
| 22:00 | Evolution | Daily architecture debate (deeper on non-trading days) |

**Non-trading day focus:**
- More Mode C cycles (capability evolution and cross-disciplinary learning)
- In-depth paper analysis (Explorer research phase can extend)
- Backtesting with longer historical data windows
- Preparation for next week: upcoming earnings and economic-data releases

### Reporting Frequency

> **Note:** All reports sent to the admin (`#admin` channel) must be written in English.

| Frequency | Time | Content | Channel |
|---|---|---|---|
| Every 2h | End of micro-cycle | Hypothesis/verdict/backtest OR capability proposal/outcome | `#a-report` |
| Every 6h | Synthesis cycle | Principle synthesis + cross-strategy analysis + mode distribution | `#a-report` |
| Daily | 22:00 EST | Evolution report: architecture debate + meta-reflection + capability review | `#a-report` |

---

## System B: Automated Investment System

### Trading Days

| Time (EST) | Agent | Frequency | Content |
|---|---|---|---|
| 09:15 | Operator | 1x | Pre-market check: Alpaca connection, strategy readiness, risk parameters |
| 09:30-16:00 | Trader | Every 15min | Signal generation + execution |
| 09:30-16:00 | Guardian | Every 5min | Real-time risk monitoring |
| 09:30-16:00 | Operator | Every 15min | Check GitHub for new strategies |
| Every 2h (market hours) | Operator | 3x | Trading summary to `#b-report` |
| 16:00 | Operator | 1x | Market close procedure: stop signals, aggregate data |
| 16:15 | Guardian | 1x | Commit daily performance data to GitHub |
| 16:30 | Operator | 1x | Daily report to `#b-report` |

### Non-Trading Days

| Time (EST) | Agent | Frequency | Content |
|---|---|---|---|
| Every 4h | Operator | 6x/day | Check GitHub for new strategies |
| Every 12h | Guardian | 2x/day | Overnight risk check (position exposure) |
| Sat 10:00 | Operator | 1x | Weekly report to `#b-report` |

### Reporting Frequency

> **Note:** All reports sent to the admin (`#admin` channel) must be written in English.

| Frequency | Time | Content | Channel |
|---|---|---|---|
| Every 2h (market hours) | Trading session | Trading summary: P&L, trade count, risk status | `#b-report` |
| Daily | 16:30 EST | Daily report: P&L, Sharpe, strategy attribution, staging status | `#b-report` |
| Weekly | Sat 10:00 | Weekly report: cumulative performance, strategy ranking, risk review | `#b-report` |

---

## Strategy Validation Periods (Operator Decision Criteria)

| Strategy Archetype | Typical Holding Period | Minimum Validation | Standard Validation | Promotion Criteria |
|---|---|---|---|---|
| High-frequency momentum | 5min-1h | 1 trading day | 2-3 trading days | Sharpe>0.3, DD<15%, >20 trades |
| Intraday mean reversion | 30min-4h | 2 trading days | 3-5 trading days | Sharpe>0.3, DD<15%, >10 trades |
| Short-term trend | 4h-2d | 3 trading days | 5-7 trading days | Sharpe>0.3, DD<20%, >5 trades |
| Medium-term event-driven | 1d-5d | 5 trading days | 7-10 trading days | Sharpe>0.2, DD<20%, >3 trades |

---

## US Stock Market Holidays (2026)

The system must recognize the following dates as non-trading days:
- 2026-01-01 New Year's Day
- 2026-01-19 MLK Day
- 2026-02-16 Presidents' Day
- 2026-04-03 Good Friday
- 2026-05-25 Memorial Day
- 2026-07-03 Independence Day (observed)
- 2026-09-07 Labor Day
- 2026-11-26 Thanksgiving
- 2026-12-25 Christmas

The exact trading calendar can be obtained via the Alpaca API `GET /v2/calendar`.

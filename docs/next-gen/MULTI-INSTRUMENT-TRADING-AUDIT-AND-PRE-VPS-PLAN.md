# Multi-Instrument Trading Audit And Pre-VPS Plan

## 1. Purpose

This is the current honest trading-surface audit for the next-generation runtime.

It replaces the earlier pre-closure draft that was written before the option, multi-leg, short, and lifecycle work landed in the repository.

The goal is simple:

- say clearly what the repo really supports today
- separate shipped product surface from future expansion
- keep the deploy story honest before VPS activation

## 2. Current Verdict

Short version:

- the repo is no longer equity-only
- the US product surface now has real multi-instrument closure for governed paper-first operation and Alpaca-backed paper/live progression
- the CN product surface is honest for research, ranking, market-session governance, and paper-first operation
- the biggest remaining trading gap is no longer "options do not exist"
- the biggest remaining trading gap is that `CN live` is not shipped, and some cross-product capital semantics remain conservative rather than universal

## 3. What Is Closed Today

### 3.1 Canonical instrument model

The runtime now has durable instrument definitions and broker capability records for:

- equities
- ETFs and leveraged ETF style instruments
- options with canonical contract identity
- broker/account capability hints for shorting, margin, options, multi-leg options, exercise, and assignment handling

### 3.2 Governed order semantics

The order path now supports:

- explicit `position_effect`
- product-aware validation
- durable order legs
- external-adapter submission with leg-aware payloads
- rejection of unsupported product paths before broker calls

### 3.3 Paper execution closure

The paper path now closes materially more than the old audit described:

- long equity lifecycle
- short equity lifecycle with borrow and maintenance-margin-style gating
- single-leg long option open/close
- short option paths in bounded forms where the policy and capability allow them
- multi-leg option structure in paper mode
- option premium and multiplier-aware notional and PnL accounting

### 3.4 Option lifecycle closure

The runtime now records and applies:

- expiration
- exercise
- assignment
- review-required fallback when the event cannot be applied safely

That means option positions no longer have to remain as silent stale state when a terminal lifecycle event occurs.

### 3.5 External broker closure

The repo now includes a real Alpaca adapter with governed:

- submit
- sync
- cancel
- replace
- account capability seeding
- broker-state refresh

For the US product surface, that is enough to treat Alpaca as a real first live path rather than a placeholder.

## 4. What Is Honest But Still Not Fully Closed

### 4.1 CN live execution

This is still the single biggest boundary.

The system can honestly support:

- `QE_DEPLOYMENT_MARKET_MODE=cn`
- A-share research and ranking
- A-share market-session governance
- A-share paper-first operation

It cannot honestly claim:

- a shipped bounded CN live broker adapter on Linux VPS

That remains a future adapter project and should stay out of the README promise surface.

### 4.2 Universal capital semantics

The system now has real product-aware capital and risk logic, but it is still conservative rather than universal.

The remaining gaps include:

- universal maintenance-margin modeling across every product path
- universal borrow-fee modeling
- universal locate / HTB workflow closure
- universal liquidation-prevention behavior across every broker/account mode

This does not mean the current risk engine is fake. It means the remaining gap is depth and breadth, not total absence.

### 4.3 Sleeve attribution and cross-strategy netting

Some cross-strategy cases are still handled conservatively because full sleeve attribution is not fully closed yet.

That is the right current behavior for safety, but it remains a real product gap for a long-running multi-sleeve deployment.

## 5. Current Product Truth By Market Mode

### 5.1 US deployment

Current honest US product surface:

- US equities
- US options
- multi-leg option structure
- short equity paths with borrow and margin gates
- broker sync and reconciliation
- Alpaca-backed paper/live progression

This is the market mode that can honestly target the first serious live-capital path.

### 5.2 CN deployment

Current honest CN product surface:

- China A-share research
- China A-share ranking and strategy generation
- China market-calendar-aware supervision
- paper-first operation

This is not a broken mode. It is a bounded mode.

## 6. Pre-VPS Operator Rule

Before treating a VPS deployment as ready for unattended operation, these must all be true:

- `./ops/bin/core-smoke.sh` reports no `fail`
- `./ops/bin/system-doctor.sh` reports no `fail`
- the dashboard loads
- the Discord bot responds only in the allowed owner surface
- the first broker sync and reconciliation are clean
- the deployment market mode is explicitly chosen as `us` or `cn`

## 7. Practical Conclusion

The earlier version of this audit said the repo still lacked real options trading support.

That is no longer true.

The current honest conclusion is:

- `US` mode now has a real governed multi-instrument shell that is strong enough for paper-first deployment and controlled Alpaca-backed live progression
- `CN` mode is real and useful now, but still paper-first because the CN live broker edge is not shipped
- the remaining work is concentrated in capital-depth semantics, sleeve attribution, and future CN live closure rather than in basic options existence

## 8. Sources

- Alpaca options overview: https://docs.alpaca.markets/docs/options-trading-overview
- Alpaca level-3 multi-leg options: https://docs.alpaca.markets/docs/options-level-3-trading
- Alpaca margin and short selling: https://docs.alpaca.markets/docs/margin-and-short-selling
- Shanghai Stock Exchange trading mechanism: https://english.sse.com.cn/start/trading/mechanism/
- XtQuant / MiniQMT start guide: https://dict.thinktrader.net/nativeApi/start_now.html

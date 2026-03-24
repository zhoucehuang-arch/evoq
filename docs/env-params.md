# Environment Parameters Reference

This document summarizes the main environment parameters used during deployment.

## Discord

- `QE_DISCORD_TOKEN`: Discord bot token for the Core node.
- `QE_DISCORD_GUILD_ID`: Discord guild ID.
- `QE_DISCORD_CONTROL_CHANNEL_ID`: channel used for owner control commands.
- `QE_DISCORD_APPROVALS_CHANNEL_ID`: channel used for approvals.
- `QE_DISCORD_ALERTS_CHANNEL_ID`: channel used for alerts.
- `QE_DISCORD_ALLOWED_USER_IDS`: comma-separated user IDs that may control the bot.

## Model and Relay

- `QE_OPENAI_API_KEY`: API key or relay key used for Codex / OpenAI-compatible calls.
- `QE_OPENAI_BASE_URL`: relay base URL when you use a proxy or third-party compatible endpoint.
- `QE_CODEX_DEFAULT_MODEL`: default Codex model.
- `QE_CODEX_COMMAND`: explicit Codex command if your runtime path is custom.
- `QE_CODEX_WORKSPACE_MODE`: workspace isolation mode for Codex runs.

## Deployment Shape

- `QE_DEPLOYMENT_TOPOLOGY`: usually `single_vps_compact` for the first deployment.
- `QE_DEPLOYMENT_MARKET_MODE`: `us` or `cn`.
- `QE_MARKET_TIMEZONE`: market timezone, for example `America/New_York` or `Asia/Shanghai`.
- `QE_MARKET_CALENDAR`: market calendar, for example `XNYS` or `XSHG`.

## Dashboard

- `QE_DASHBOARD_ACCESS_USERNAME`: dashboard login username.
- `QE_DASHBOARD_ACCESS_PASSWORD`: dashboard login password.
- `QE_DASHBOARD_API_TOKEN`: dashboard API token.
- `QE_EDGE_PUBLIC_HOST`: public host name when you expose the dashboard through the edge layer.
- `QE_EDGE_ACME_EMAIL`: email used for ACME / TLS automation.

## Database

- `QE_POSTGRES_PASSWORD`: local Postgres password for Core deployments.
- `QE_POSTGRES_URL`: Postgres URL used by the Worker when you scale out.

## Acquisition Stack

- `QE_SEARXNG_BASE_URL`: optional SearXNG endpoint.
- `QE_RSSHUB_BASE_URL`: optional RSSHub endpoint.
- `QE_PLAYWRIGHT_BROWSER_ENABLED`: enable governed Playwright fallback.
- `QE_PLAYWRIGHT_BROWSER_ENDPOINT`: Playwright browser endpoint.
- `QE_SKILL_LIBRARY_ROOT`: local skill library root when needed by Codex workers.

## Broker

Safe first-boot defaults:

- `QE_DEFAULT_BROKER_ADAPTER=paper_sim`
- `QE_DEFAULT_BROKER_ENVIRONMENT=paper`

US Alpaca credentials, when used:

- `QE_ALPACA_PAPER_API_KEY`
- `QE_ALPACA_PAPER_API_SECRET`
- `QE_ALPACA_LIVE_API_KEY`
- `QE_ALPACA_LIVE_API_SECRET`

## Operational Advice

- Keep the first deployment on `single_vps_compact`.
- Keep the broker in paper mode until smoke, doctor, and broker sync are consistently clean.
- Do not place broker credentials on the Worker node.
- Treat relay and dashboard secrets as required production credentials.

# Stream Error Retry Guard Rollout (Explorer)

- source: admin_1476297430919024822
- rule: STREAM_ERROR_RETRY_GUARD_V1
- applied_at_utc: 2026-02-25T19:25:00Z
- agent: explorer

## Enforced Rules
1. Never echo raw stream/provider errors to channel.
2. Auto-retry once on stream_read_error.
3. If retry fails, send structured DEPENDENCY_BLOCK with retry ETA.
4. Provider-error-only inbound messages return NO_REPLY.

## Runtime Note
- Guard is treated as mandatory channel-output policy for this agent.

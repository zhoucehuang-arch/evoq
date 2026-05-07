# Discord Channel Permissions Matrix

## 4-Instance Architecture

System A runs as 3 separate OpenClaw instances, each with its own Discord bot. System B runs as 1 instance with a shared bot. All System A bots have `allowBots: true` to enable cross-bot debate.

## Bot-Explorer (QuantEvo-Explorer) Permissions

| Channel | Read | Write | Manage Messages |
|---|---|---|---|
| #a-arena | ✅ | ✅ | ❌ |
| #a-verdict | ❌ | ❌ | ❌ |
| #a-research | ✅ | ✅ | ❌ |
| #a-report | ✅ | ✅ | ❌ |
| #b-ops | ❌ | ❌ | ❌ |
| #b-desk | ❌ | ❌ | ❌ |
| #b-risk | ❌ | ❌ | ❌ |
| #b-report | ❌ | ❌ | ❌ |
| #bridge | ❌ | ❌ | ❌ |
| #admin | ❌ | ❌ | ❌ |

## Bot-Critic (QuantEvo-Critic) Permissions

| Channel | Read | Write | Manage Messages |
|---|---|---|---|
| #a-arena | ✅ | ✅ | ❌ |
| #a-verdict | ❌ | ❌ | ❌ |
| #a-research | ❌ | ❌ | ❌ |
| #a-report | ✅ | ❌ | ❌ |
| #b-ops | ❌ | ❌ | ❌ |
| #b-desk | ❌ | ❌ | ❌ |
| #b-risk | ❌ | ❌ | ❌ |
| #b-report | ❌ | ❌ | ❌ |
| #bridge | ❌ | ❌ | ❌ |
| #admin | ❌ | ❌ | ❌ |

## Bot-Evolver (QuantEvo-Evolver) Permissions

| Channel | Read | Write | Manage Messages |
|---|---|---|---|
| #a-arena | ✅ | ✅ | ❌ |
| #a-verdict | ✅ | ✅ | ❌ |
| #a-research | ❌ | ❌ | ❌ |
| #a-report | ✅ | ✅ | ❌ |
| #b-ops | ❌ | ❌ | ❌ |
| #b-desk | ❌ | ❌ | ❌ |
| #b-risk | ❌ | ❌ | ❌ |
| #b-report | ❌ | ❌ | ❌ |
| #bridge | ✅ | ✅ | ❌ |
| #admin | ✅ | ✅ | ❌ |

## Bot-B (QuantEvo-B) Permissions

| Channel | Read | Write | Manage Messages |
|---|---|---|---|
| #a-arena | ❌ | ❌ | ❌ |
| #a-verdict | ❌ | ❌ | ❌ |
| #a-research | ❌ | ❌ | ❌ |
| #a-report | ❌ | ❌ | ❌ |
| #b-ops | ✅ | ✅ | ❌ |
| #b-desk | ✅ | ✅ | ❌ |
| #b-risk | ✅ | ✅ | ❌ |
| #b-report | ✅ | ✅ | ❌ |
| #bridge | ✅ | ✅ | ❌ |
| #admin | ✅ | ✅ | ❌ |

## Admin (Human) Permissions

| Channel | Read | Write | Manage Messages |
|---|---|---|---|
| All channels | ✅ | ✅ | ✅ |

## Discord Server Setup Commands

```bash
# After creating the server and channels, set permissions via Discord UI:
# 1. Server Settings → Roles → Create 4 roles: "Bot-Explorer", "Bot-Critic", "Bot-Evolver", "Bot-B"
# 2. For each channel, set role-specific permissions:
#    - Bot-Explorer: allow on #a-arena, #a-research, #a-report; deny all others
#    - Bot-Critic: allow on #a-arena; read-only on #a-report; deny all others
#    - Bot-Evolver: allow on #a-arena, #a-verdict, #a-report, #bridge, #admin; deny all others
#    - Bot-B: allow on #b-*, #bridge, #admin; deny all #a-* channels
# 3. Assign each role to the corresponding bot
```

## Agent-to-Channel Binding

### System A (Each agent = separate bot, no internal routing needed)
| Bot | Agent | Primary Channel | Secondary Channels |
|---|---|---|---|
| Bot-Explorer | Explorer | #a-arena | #a-research, #a-report |
| Bot-Critic | Critic | #a-arena | #a-report (read-only) |
| Bot-Evolver | Evolver | #a-arena | #a-verdict, #a-report, #bridge, #admin |

### System B (3 agents share Bot-B, internal routing via bindings)
| Agent | Primary Channel | Secondary Channels |
|---|---|---|
| Operator | #b-ops | #b-report, #bridge |
| Trader | #b-desk | — |
| Guardian | #b-risk | — |

## Cross-Bot Communication

System A agents communicate via Discord messages across different bots. Each bot has `allowBots: true` in its OpenClaw config, enabling it to see and respond to messages from other bots. The debate flow works as:

```
Bot-Evolver posts CYCLE_TRIGGER to #a-arena
    → Bot-Explorer sees it, researches, posts HYPOTHESIS
    → Bot-Critic sees it, stress-tests, posts RISK_ASSESSMENT
    → Bot-Explorer sees it, posts REBUTTAL
    → Bot-Critic sees it, posts final RISK_ASSESSMENT
    → Bot-Evolver sees it, posts VERDICT to #a-verdict
```

System B agents communicate internally within a single bot instance. The `allowBots: true` setting on Bot-B enables it to see System A messages in #bridge and #admin.

# Setup Guide: Deploying with OpenClaw

## Prerequisites

- Node.js >= 22
- Four machines (or four separate OpenClaw config directories on one machine)
- Discord server with 4 bot tokens (one per instance)
- GitHub PAT for all instances
- OpenAI API keys (6 total, one per agent)
- Alpaca Paper Trading account (for Instance B)

## Step 1: Install OpenClaw

```bash
npm install -g openclaw@latest

# Run the onboarding wizard
openclaw onboard --install-daemon
```

## Step 2: Create Discord Server & Bots

### 2.1 Create Discord Server
Create a Discord server (e.g., "Quant-Evo") with these channels:

**System A channels:**
- `#a-arena` — Debate arena (Explorer + Critic)
- `#a-verdict` — Verdicts and backtest results (Evolver)
- `#a-research` — Research notes (Explorer)
- `#a-report` — Multi-frequency reports (Evolver)

**System B channels:**
- `#b-ops` — Operations and deployment (Operator)
- `#b-desk` — Trading signals and execution (Trader)
- `#b-risk` — Risk alerts and HALT (Guardian)
- `#b-report` — Performance reports (Operator)

**Shared channels:**
- `#bridge` — Cross-system sync notifications
- `#admin` — System health and admin commands

### 2.2 Create Four Discord Bots

Go to [Discord Developer Portal](https://discord.com/developers/applications):

1. Create **Bot-Explorer** (e.g., "QuantEvo-Explorer"):
   - Enable "Message Content Intent" in Bot settings
   - Copy the bot token → save as `DISCORD_BOT_TOKEN_EXPLORER`
   - Invite to your server with permissions: Send Messages, Read Message History, Manage Messages

2. Create **Bot-Critic** (e.g., "QuantEvo-Critic"):
   - Same settings as above
   - Copy the bot token → save as `DISCORD_BOT_TOKEN_CRITIC`
   - Invite to your server

3. Create **Bot-Evolver** (e.g., "QuantEvo-Evolver"):
   - Same settings as above
   - Copy the bot token → save as `DISCORD_BOT_TOKEN_EVOLVER`
   - Invite to your server

4. Create **Bot-B** (e.g., "QuantEvo-B"):
   - Same settings as above
   - Copy the bot token → save as `DISCORD_BOT_TOKEN_B`
   - Invite to your server

### 2.3 Get Channel & Guild IDs
Enable Developer Mode in Discord (Settings → Advanced → Developer Mode).
Right-click your server → Copy Server ID → this is your `GUILD_ID`.
Right-click each channel → Copy Channel ID.

## Step 3: Configure System A Instances (Self-Evolution System)

System A is split into three single-agent instances so each agent runs in its own process with its own Discord bot. All three have `allowBots: true` so they can see and respond to each other's messages.

### 3.1 Instance Explorer

#### 3.1.1 Set Up Config Directory

```bash
mkdir -p ~/.openclaw-explorer
git clone https://github.com/zhoucehuang-arch/quant-evo-do-test.git ~/quant-evo-do-test
```

#### 3.1.2 Copy Agent Files

```bash
cp -r ~/quant-evo-do-test/config/instance-explorer/agents ~/.openclaw-explorer/
```

#### 3.1.3 Create openclaw.json

Create `~/.openclaw-explorer/openclaw.json`:

```json
{
  "models": {
    "providers": {
      "openai-codex-a1": {
        "baseUrl": "https://api.openai.com/v1",
        "apiKey": "${OPENAI_KEY_A1}",
        "api": "openai-completions",
        "models": [{ "id": "gpt-5.3-codex", "name": "GPT-5.3 Codex (Explorer)", "reasoning": true, "input": ["text", "image"], "contextWindow": 200000, "maxTokens": 32768 }]
      },
      "kimi-fallback": {
        "baseUrl": "https://api.moonshot.cn/v1",
        "apiKey": "${KIMI_KEY_SHARED}",
        "api": "openai-completions",
        "models": [{ "id": "kimi-k2.5", "name": "Kimi K2.5 (Fallback)", "reasoning": false, "input": ["text"], "contextWindow": 128000, "maxTokens": 8192 }]
      }
    }
  },

  "agents": {
    "defaults": {
      "heartbeat": { "enabled": true, "interval": 600000 },
      "compaction": {
        "enabled": true,
        "memoryFlush": { "enabled": true, "softThreshold": 4000 }
      }
    },
    "list": [
      {
        "id": "explorer",
        "name": "Explorer",
        "workspace": "./agents/explorer",
        "model": "openai-codex-a1/gpt-5.3-codex",
        "skills": ["github", "discord"],
        "identity": { "name": "Explorer", "emoji": "🔬" }
      }
    ]
  },

  "bindings": [
    { "agentId": "explorer", "match": { "channel": "discord", "guildId": "${DISCORD_GUILD_ID}", "peer": { "kind": "group", "id": "${CH_A_ARENA}" } } },
    { "agentId": "explorer", "match": { "channel": "discord", "guildId": "${DISCORD_GUILD_ID}", "peer": { "kind": "group", "id": "${CH_A_RESEARCH}" } } },
    { "agentId": "explorer", "match": { "channel": "discord", "guildId": "${DISCORD_GUILD_ID}", "peer": { "kind": "group", "id": "${CH_A_REPORT}" } } }
  ],

  "channels": {
    "discord": {
      "token": "${DISCORD_BOT_TOKEN_EXPLORER}",
      "groupPolicy": "allowlist",
      "allowBots": true,
      "guilds": {
        "${DISCORD_GUILD_ID}": {
          "slug": "quant-evo-explorer",
          "requireMention": false
        }
      }
    }
  },

  "cron": { "enabled": true, "maxConcurrentRuns": 1 },
  "skills": { "allowBundled": ["discord", "github"] },

  "mcpServers": {
    "one-search": {
      "command": "npx",
      "args": ["-y", "one-search-mcp"],
      "env": {
        "SEARCH_PROVIDER": "searxng",
        "SEARXNG_URL": "http://localhost:8888"
      }
    }
  },
  "memorySearch": {
    "cache": {
      "enabled": true,
      "maxEntries": 50000
    }
  }
}
```

#### 3.1.4 Set Environment Variables

Create `~/.openclaw-explorer/.env`:

```bash
# LLM API Key
OPENAI_KEY_A1=sk-explorer-key-here
KIMI_KEY_SHARED=kimi-shared-key-here

# Discord
DISCORD_BOT_TOKEN_EXPLORER=bot-token-explorer-here
DISCORD_GUILD_ID=your-guild-id

# Discord Channel IDs
CH_A_ARENA=
CH_A_RESEARCH=
CH_A_REPORT=

# GitHub
GITHUB_TOKEN_A=ghp-pat-a-here
GITHUB_REPO=zhoucehuang-arch/quant-evo-do-test
```

#### 3.1.5 Start Instance Explorer

```bash
export OPENCLAW_CONFIG_DIR=~/.openclaw-explorer
openclaw gateway run --port 18789 --verbose
```

### 3.2 Instance Critic

#### 3.2.1 Set Up Config Directory

```bash
mkdir -p ~/.openclaw-critic
```

#### 3.2.2 Copy Agent Files

```bash
cp -r ~/quant-evo-do-test/config/instance-critic/agents ~/.openclaw-critic/
```

#### 3.2.3 Create openclaw.json

Create `~/.openclaw-critic/openclaw.json`:

```json
{
  "models": {
    "providers": {
      "openai-codex-a2": {
        "baseUrl": "https://api.openai.com/v1",
        "apiKey": "${OPENAI_KEY_A2}",
        "api": "openai-completions",
        "models": [{ "id": "gpt-5.3-codex", "name": "GPT-5.3 Codex (Critic)", "reasoning": true, "input": ["text", "image"], "contextWindow": 200000, "maxTokens": 32768 }]
      },
      "kimi-fallback": {
        "baseUrl": "https://api.moonshot.cn/v1",
        "apiKey": "${KIMI_KEY_SHARED}",
        "api": "openai-completions",
        "models": [{ "id": "kimi-k2.5", "name": "Kimi K2.5 (Fallback)", "reasoning": false, "input": ["text"], "contextWindow": 128000, "maxTokens": 8192 }]
      }
    }
  },

  "agents": {
    "defaults": {
      "heartbeat": { "enabled": true, "interval": 600000 },
      "compaction": {
        "enabled": true,
        "memoryFlush": { "enabled": true, "softThreshold": 4000 }
      }
    },
    "list": [
      {
        "id": "critic",
        "name": "Critic",
        "workspace": "./agents/critic",
        "model": "openai-codex-a2/gpt-5.3-codex",
        "skills": ["github", "discord"],
        "identity": { "name": "Critic", "emoji": "🛡" }
      }
    ]
  },

  "bindings": [
    { "agentId": "critic", "match": { "channel": "discord", "guildId": "${DISCORD_GUILD_ID}", "peer": { "kind": "group", "id": "${CH_A_ARENA}" } } },
    { "agentId": "critic", "match": { "channel": "discord", "guildId": "${DISCORD_GUILD_ID}", "peer": { "kind": "group", "id": "${CH_A_REPORT}" } } }
  ],

  "channels": {
    "discord": {
      "token": "${DISCORD_BOT_TOKEN_CRITIC}",
      "groupPolicy": "allowlist",
      "allowBots": true,
      "guilds": {
        "${DISCORD_GUILD_ID}": {
          "slug": "quant-evo-critic",
          "requireMention": false
        }
      }
    }
  },

  "cron": { "enabled": true, "maxConcurrentRuns": 1 },
  "skills": { "allowBundled": ["discord", "github"] },

  "mcpServers": {
    "one-search": {
      "command": "npx",
      "args": ["-y", "one-search-mcp"],
      "env": {
        "SEARCH_PROVIDER": "searxng",
        "SEARXNG_URL": "http://localhost:8888"
      }
    }
  },
  "memorySearch": {
    "cache": {
      "enabled": true,
      "maxEntries": 50000
    }
  }
}
```

#### 3.2.4 Set Environment Variables

Create `~/.openclaw-critic/.env`:

```bash
# LLM API Key
OPENAI_KEY_A2=sk-critic-key-here
KIMI_KEY_SHARED=kimi-shared-key-here

# Discord
DISCORD_BOT_TOKEN_CRITIC=bot-token-critic-here
DISCORD_GUILD_ID=your-guild-id

# Discord Channel IDs
CH_A_ARENA=
CH_A_REPORT=

# GitHub
GITHUB_TOKEN_A=ghp-pat-a-here
GITHUB_REPO=zhoucehuang-arch/quant-evo-do-test
```

#### 3.2.5 Start Instance Critic

```bash
export OPENCLAW_CONFIG_DIR=~/.openclaw-critic
openclaw gateway run --port 18790 --verbose
```

### 3.3 Instance Evolver

#### 3.3.1 Set Up Config Directory

```bash
mkdir -p ~/.openclaw-evolver
```

#### 3.3.2 Copy Agent Files

```bash
cp -r ~/quant-evo-do-test/config/instance-evolver/agents ~/.openclaw-evolver/
```

#### 3.3.3 Create openclaw.json

Create `~/.openclaw-evolver/openclaw.json`:

```json
{
  "models": {
    "providers": {
      "openai-codex-a3": {
        "baseUrl": "https://api.openai.com/v1",
        "apiKey": "${OPENAI_KEY_A3}",
        "api": "openai-completions",
        "models": [{ "id": "gpt-5.3-codex", "name": "GPT-5.3 Codex (Evolver)", "reasoning": true, "input": ["text", "image"], "contextWindow": 200000, "maxTokens": 32768 }]
      },
      "kimi-fallback": {
        "baseUrl": "https://api.moonshot.cn/v1",
        "apiKey": "${KIMI_KEY_SHARED}",
        "api": "openai-completions",
        "models": [{ "id": "kimi-k2.5", "name": "Kimi K2.5 (Fallback)", "reasoning": false, "input": ["text"], "contextWindow": 128000, "maxTokens": 8192 }]
      }
    }
  },

  "agents": {
    "defaults": {
      "heartbeat": { "enabled": true, "interval": 7200000 },
      "compaction": {
        "enabled": true,
        "memoryFlush": { "enabled": true, "softThreshold": 4000 }
      }
    },
    "list": [
      {
        "id": "evolver",
        "name": "Evolver",
        "workspace": "./agents/evolver",
        "model": "openai-codex-a3/gpt-5.3-codex",
        "skills": ["github", "discord"],
        "identity": { "name": "Evolver", "emoji": "⚖" }
      }
    ]
  },

  "bindings": [
    { "agentId": "evolver", "match": { "channel": "discord", "guildId": "${DISCORD_GUILD_ID}", "peer": { "kind": "group", "id": "${CH_A_ARENA}" } } },
    { "agentId": "evolver", "match": { "channel": "discord", "guildId": "${DISCORD_GUILD_ID}", "peer": { "kind": "group", "id": "${CH_A_VERDICT}" } } },
    { "agentId": "evolver", "match": { "channel": "discord", "guildId": "${DISCORD_GUILD_ID}", "peer": { "kind": "group", "id": "${CH_A_REPORT}" } } },
    { "agentId": "evolver", "match": { "channel": "discord", "guildId": "${DISCORD_GUILD_ID}", "peer": { "kind": "group", "id": "${CH_BRIDGE}" } } },
    { "agentId": "evolver", "match": { "channel": "discord", "guildId": "${DISCORD_GUILD_ID}", "peer": { "kind": "group", "id": "${CH_ADMIN}" } } }
  ],

  "channels": {
    "discord": {
      "token": "${DISCORD_BOT_TOKEN_EVOLVER}",
      "groupPolicy": "allowlist",
      "allowBots": true,
      "guilds": {
        "${DISCORD_GUILD_ID}": {
          "slug": "quant-evo-evolver",
          "requireMention": false
        }
      }
    }
  },

  "cron": { "enabled": true, "maxConcurrentRuns": 1 },
  "skills": { "allowBundled": ["discord", "github"] },

  "mcpServers": {
    "one-search": {
      "command": "npx",
      "args": ["-y", "one-search-mcp"],
      "env": {
        "SEARCH_PROVIDER": "searxng",
        "SEARXNG_URL": "http://localhost:8888"
      }
    }
  },
  "memorySearch": {
    "cache": {
      "enabled": true,
      "maxEntries": 50000
    }
  }
}
```

Note: Evolver uses a 2-hour heartbeat (`7200000` ms) because evolution cycles are long-running. Explorer and Critic use 10-minute heartbeats (`600000` ms).

#### 3.3.4 Set Environment Variables

Create `~/.openclaw-evolver/.env`:

```bash
# LLM API Key
OPENAI_KEY_A3=sk-evolver-key-here
KIMI_KEY_SHARED=kimi-shared-key-here

# Discord
DISCORD_BOT_TOKEN_EVOLVER=bot-token-evolver-here
DISCORD_GUILD_ID=your-guild-id

# Discord Channel IDs
CH_A_ARENA=
CH_A_VERDICT=
CH_A_REPORT=
CH_BRIDGE=
CH_ADMIN=

# GitHub
GITHUB_TOKEN_A=ghp-pat-a-here
GITHUB_REPO=zhoucehuang-arch/quant-evo-do-test
```

#### 3.3.5 Start Instance Evolver

```bash
export OPENCLAW_CONFIG_DIR=~/.openclaw-evolver
openclaw gateway run --port 18791 --verbose
```

## Step 4: Configure Instance B (Automated Investment System)

### 4.1 Set Up Config Directory

```bash
mkdir -p ~/.openclaw-b
```

### 4.2 Copy Agent Files

```bash
cp -r ~/quant-evo-do-test/config/instance-b/agents ~/.openclaw-b/
```

### 4.3 Create openclaw.json for Instance B

Create `~/.openclaw-b/openclaw.json`:

```json
{
  "models": {
    "providers": {
      "openai-codex-b1": {
        "baseUrl": "https://api.openai.com/v1",
        "apiKey": "${OPENAI_KEY_B1}",
        "api": "openai-completions",
        "models": [{ "id": "gpt-5.3-codex", "name": "GPT-5.3 Codex (Operator)", "reasoning": true, "input": ["text", "image"], "contextWindow": 200000, "maxTokens": 32768 }]
      },
      "openai-codex-b2": {
        "baseUrl": "https://api.openai.com/v1",
        "apiKey": "${OPENAI_KEY_B2}",
        "api": "openai-completions",
        "models": [{ "id": "gpt-5.3-codex", "name": "GPT-5.3 Codex (Trader)", "reasoning": true, "input": ["text", "image"], "contextWindow": 200000, "maxTokens": 32768 }]
      },
      "openai-codex-b3": {
        "baseUrl": "https://api.openai.com/v1",
        "apiKey": "${OPENAI_KEY_B3}",
        "api": "openai-completions",
        "models": [{ "id": "gpt-5.3-codex", "name": "GPT-5.3 Codex (Guardian)", "reasoning": true, "input": ["text", "image"], "contextWindow": 200000, "maxTokens": 32768 }]
      },
      "kimi-fallback": {
        "baseUrl": "https://api.moonshot.cn/v1",
        "apiKey": "${KIMI_KEY_SHARED}",
        "api": "openai-completions",
        "models": [{ "id": "kimi-k2.5", "name": "Kimi K2.5 (Fallback)", "reasoning": false, "input": ["text"], "contextWindow": 128000, "maxTokens": 8192 }]
      }
    }
  },

  "agents": {
    "defaults": {
      "heartbeat": { "enabled": true, "interval": 300000 },
      "compaction": {
        "enabled": true,
        "memoryFlush": { "enabled": true, "softThreshold": 4000 }
      }
    },
    "list": [
      {
        "id": "operator",
        "name": "Operator",
        "workspace": "./agents/operator",
        "model": "openai-codex-b1/gpt-5.3-codex",
        "skills": ["github", "discord"],
        "identity": { "name": "Operator", "emoji": "📋" }
      },
      {
        "id": "trader",
        "name": "Trader",
        "workspace": "./agents/trader",
        "model": "openai-codex-b2/gpt-5.3-codex",
        "skills": ["github", "discord"],
        "identity": { "name": "Trader", "emoji": "📡" }
      },
      {
        "id": "guardian",
        "name": "Guardian",
        "workspace": "./agents/guardian",
        "model": "openai-codex-b3/gpt-5.3-codex",
        "skills": ["github", "discord"],
        "identity": { "name": "Guardian", "emoji": "🚨" }
      }
    ]
  },

  "bindings": [
    { "agentId": "operator", "match": { "channel": "discord", "guildId": "${DISCORD_GUILD_ID}", "peer": { "kind": "group", "id": "${CH_B_OPS}" } } },
    { "agentId": "trader",   "match": { "channel": "discord", "guildId": "${DISCORD_GUILD_ID}", "peer": { "kind": "group", "id": "${CH_B_DESK}" } } },
    { "agentId": "guardian",  "match": { "channel": "discord", "guildId": "${DISCORD_GUILD_ID}", "peer": { "kind": "group", "id": "${CH_B_RISK}" } } },
    { "agentId": "operator", "match": { "channel": "discord", "guildId": "${DISCORD_GUILD_ID}", "peer": { "kind": "group", "id": "${CH_B_REPORT}" } } }
  ],

  "channels": {
    "discord": {
      "token": "${DISCORD_BOT_TOKEN_B}",
      "groupPolicy": "allowlist",
      "allowBots": true,
      "guilds": {
        "${DISCORD_GUILD_ID}": {
          "slug": "quant-evo-b",
          "requireMention": false
        }
      }
    }
  },

  "cron": {
    "enabled": true,
    "maxConcurrentRuns": 2
  },

  "skills": {
    "allowBundled": ["discord", "github"]
  },

  "mcpServers": {
    "one-search": {
      "command": "npx",
      "args": ["-y", "one-search-mcp"],
      "env": {
        "SEARCH_PROVIDER": "searxng",
        "SEARXNG_URL": "http://localhost:8888"
      }
    }
  },
  "memorySearch": {
    "cache": {
      "enabled": true,
      "maxEntries": 50000
    }
  }
}
```

### 4.4 Set Environment Variables for Instance B

Create `~/.openclaw-b/.env`:

```bash
# LLM API Keys (one per agent)
OPENAI_KEY_B1=sk-operator-key-here
OPENAI_KEY_B2=sk-trader-key-here
OPENAI_KEY_B3=sk-guardian-key-here
KIMI_KEY_SHARED=kimi-shared-key-here

# Discord
DISCORD_BOT_TOKEN_B=bot-token-b-here
DISCORD_GUILD_ID=your-guild-id

# Discord Channel IDs
CH_B_OPS=
CH_B_DESK=
CH_B_RISK=
CH_B_REPORT=
CH_BRIDGE=
CH_ADMIN=

# GitHub
GITHUB_TOKEN_B=ghp-pat-b-here
GITHUB_REPO=zhoucehuang-arch/quant-evo-do-test

# Alpaca Paper Trading
ALPACA_API_KEY=your-alpaca-key
ALPACA_SECRET_KEY=your-alpaca-secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

### 4.5 Start Instance B

```bash
export OPENCLAW_CONFIG_DIR=~/.openclaw-b
openclaw gateway run --port 18792 --verbose
```

## Step 5: Clone the Shared GitHub Repo

All four instances need access to the shared repo for data exchange:

```bash
# Clone on each machine (if running on separate machines)
git clone https://github.com/zhoucehuang-arch/quant-evo-do-test.git ~/quant-evo-do-test-workspace
```

The agents will read/write to this repo according to their permissions defined in USER.md.

## Step 6: Verify Setup

```bash
# Check Instance Explorer
OPENCLAW_CONFIG_DIR=~/.openclaw-explorer openclaw doctor
OPENCLAW_CONFIG_DIR=~/.openclaw-explorer openclaw agents list --bindings
OPENCLAW_CONFIG_DIR=~/.openclaw-explorer openclaw channels status --probe

# Check Instance Critic
OPENCLAW_CONFIG_DIR=~/.openclaw-critic openclaw doctor
OPENCLAW_CONFIG_DIR=~/.openclaw-critic openclaw agents list --bindings
OPENCLAW_CONFIG_DIR=~/.openclaw-critic openclaw channels status --probe

# Check Instance Evolver
OPENCLAW_CONFIG_DIR=~/.openclaw-evolver openclaw doctor
OPENCLAW_CONFIG_DIR=~/.openclaw-evolver openclaw agents list --bindings
OPENCLAW_CONFIG_DIR=~/.openclaw-evolver openclaw channels status --probe

# Check Instance B
OPENCLAW_CONFIG_DIR=~/.openclaw-b openclaw doctor
OPENCLAW_CONFIG_DIR=~/.openclaw-b openclaw agents list --bindings
OPENCLAW_CONFIG_DIR=~/.openclaw-b openclaw channels status --probe
```

## Step 7: Bootstrap the System

Once all four gateways are running and connected to Discord:

1. Start **Instance Evolver first** — it drives the evolution cycle
2. Start Instance Explorer and Instance Critic — they respond to triggers from Evolver
3. Start Instance B — it watches for promoted strategies independently
4. Go to `#a-report` channel in Discord
5. Send a message to Evolver: "Read BOOTSTRAP-A.md from the GitHub repo and begin your first micro-cycle"
6. Evolver will read the bootstrap guide and start the self-evolution loop
7. Go to `#b-ops` channel
8. Send a message to Operator: "Read BOOTSTRAP-B.md from the GitHub repo and begin monitoring"
9. Operator will initialize and start watching for strategies

## Architecture Recap

```
Instance Explorer (port 18789)    Instance Critic (port 18790)
├── Explorer → #a-arena,          ├── Critic → #a-arena,
│              #a-research,       │            #a-report
│              #a-report          │
│   allowBots: true               │   allowBots: true
│   heartbeat: 600s               │   heartbeat: 600s
│                                 │
Instance Evolver (port 18791)     Instance B (port 18792)
├── Evolver → #a-arena,           ├── Operator → #b-ops, #b-report
│             #a-verdict,         ├── Trader   → #b-desk
│             #a-report,          ├── Guardian → #b-risk
│             #bridge, #admin     │
│   allowBots: true               │   allowBots: true
│   heartbeat: 7200s (2h)        │   heartbeat: 300s

              ↕ GitHub Repo (quant-evo) ↕
              strategies/ evo/ memory/ trading/
```

## Troubleshooting

- **Bot not responding**: Check `openclaw channels status --probe` and ensure Message Content Intent is enabled
- **Agent not routing**: Verify channel IDs in bindings match actual Discord channel IDs
- **Bots ignoring each other**: Ensure `allowBots: true` is set in all System A instances
- **API rate limits**: Each agent has its own API key, so rate limits are isolated
- **GitHub sync issues**: Check GITHUB_TOKEN permissions (needs repo read/write)
- **Alpaca connection**: Verify ALPACA_API_KEY and ALPACA_SECRET_KEY are for paper trading
- **Evolver heartbeat too frequent**: Evolver uses 2h heartbeat by design; don't lower it

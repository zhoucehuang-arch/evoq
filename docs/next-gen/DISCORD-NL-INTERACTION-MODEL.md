# Discord Natural-Language Interaction Model

## Purpose

This document defines how the owner interacts with the system through Discord.

The key design principle is `natural language first`. The owner should not have to memorize a large command surface to operate the product safely.

## Design Objective

The system should feel like talking to an autonomous investment team, not operating a pile of scripts.

Interaction principles:

- natural language first
- slash commands as fallback
- risky actions require confirmation or approval
- responses should be concise, operational, and human-readable
- answer with the result first, then reason, then next action when useful

## Interaction Modes

### Natural-language commands

Examples:

- `status`
- `pause auto-trading`
- `show runtime config`
- `why was this strategy not promoted?`

The system should classify intent, extract entities, and route the request without requiring exact syntax.

### Slash-command fallback

When natural language is ambiguous or an explicit parameter surface helps, slash commands remain available:

- `/status`
- `/pause-trading`
- `/pause-evolution`
- `/resume-domain`
- `/approve`
- `/reject`

### Approval cards

High-risk actions should create approval objects instead of executing immediately.

### Scheduled summaries

Discord may also receive:

- market-open summary
- end-of-day summary
- daily learning summary
- weekly governance summary

## Natural-Language Router

Natural-language interaction should always pass through a dedicated routing layer.

### Router pipeline

```text
Discord message
  -> intent classification
  -> entity extraction
  -> policy check
  -> ambiguity detection
  -> action plan
  -> confirmation or execution
  -> result summary
```

### Required router outputs

- `intent_type`
- `target_domain`
- `risk_tier`
- `requires_confirmation`
- `clarification_needed`
- `proposed_action`

## Intent Catalog

### Governance intents

- show status
- list approvals
- pause or resume domains
- adjust budgets or runtime policy
- open or close goals

### Learning intents

- ask what the system learned
- ask it to research a topic
- ask for supporting evidence

### Strategy intents

- show strategy state
- explain promotion or withdrawal
- request deeper analysis on a direction

### Trading intents

- show current risk and positions
- pause auto-trading
- switch to paper-only posture
- explain a trade decision

### Evolution intents

- show recent self-improvement work
- pause auto-evolution
- review Codex run results

### Incident intents

- explain an alert
- show the latest incident
- request safe mode
- request recovery review

## Confirmation Policy

Not every action needs the same friction.

### No-confirm actions

- read-only status
- reports
- evidence lookup
- decision explanation

### Soft-confirm actions

- pausing learning
- pausing evolution
- low-risk budget changes

### Hard-confirm actions

- enabling live trading
- resuming halted execution
- modifying core risk boundaries
- raising autonomy level
- accepting high-risk Codex changes

## Clarification Strategy

When intent is ambiguous:

- ask for the missing entity or scope
- offer the most likely interpretation
- prefer a narrow follow-up question over a broad help dump

## Response Style

Discord responses should be:

- short
- operational
- fully English
- explicit about what happened and what did not happen

## Security and Channel Boundaries

Discord is a control shell, not the source of truth.

Hard requirements:

- only approved owner user IDs may issue control commands
- only approved channels may accept control or approval flows
- secrets must be redacted in summaries
- risky requests must be written into durable state

## Deploy-Draft Control

Discord may update deploy drafts for owner convenience, but:

- changes remain draft-state until services restart
- deploy-draft updates do not bypass preflight
- secret values must be redacted in chat summaries

## Non-Goals

Discord should not become:

- the canonical runtime database
- the only place decisions live
- an unrestricted production console with no governance

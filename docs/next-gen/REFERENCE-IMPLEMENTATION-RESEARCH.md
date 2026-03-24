# Reference Implementation Research

## Purpose

This document records which outside systems influenced the implementation direction and what was adopted from each.

The goal is not trend chasing. The goal is to avoid repeating known failure modes.

## Sources Reviewed

1. Ralph Loop Agent
   `https://github.com/vercel-labs/ralph-loop-agent`
2. Dynamous Remote Coding Agent
   `https://github.com/coleam00/remote-agentic-coding-system`
3. OpenClaw
   `https://github.com/openclaw/openclaw`
4. OpenClaw ACP Bridge
   `https://github.com/openclaw/openclaw/blob/main/docs.acp.md`
5. OpenAI Codex docs
   `https://developers.openai.com/codex/agent-approvals-security/`
   `https://developers.openai.com/codex/config-reference/`

## Ralph Loop Agent

### Main takeaway

Ralph wraps agent work in an outer loop with explicit completion verification and bounded retries.

### Why it matters here

This is useful for:

- continuous research loops
- repeated repair loops
- bounded reflection loops

### What we adopted

- Ralph-style bounded outer loops
- explicit verify functions
- token / cost / retry stop conditions

### What we did not adopt directly

Ralph is more about persistent single-agent completion than multi-domain governance for a trading system.

## Dynamous Remote Coding Agent

### Main takeaway

It demonstrates that IM adapters, session persistence, and coding-agent abstraction can work well together.

### What we adopted

- platform-adapter thinking
- session persistence as an operating primitive
- clear owner escape hatches

### What we did not adopt directly

Its data model is too light for trading, risk, learning, and evolution truth.

## OpenClaw

### Main takeaway

The gateway / shell / session mapping ideas are strong. The chat shell can still feel natural when the runtime truth lives elsewhere.

### What we adopted

- shell-first owner experience
- gateway-style thinking for channel routing and sessions
- daemon-friendly long-running posture

### What we avoided

- chat-heavy prompt swarms as runtime truth
- trusted-operator assumptions that do not fit capital systems
- making Discord conversation state equivalent to durable operational state

## Codex Official Guidance

### Main takeaway

Codex is excellent as an execution layer, but it still needs policy, sandbox, review, and budgeting around it.

### What we adopted

- Codex-centered execution
- explicit policy envelope
- review / eval / artifact requirements
- provider and relay abstraction from the beginning

### What we avoided

- treating Codex CLI as the entire runtime kernel
- assuming approvals, search, or sandbox behavior should remain implicit

## Final Synthesis

The resulting direction is:

```text
authoritative core
  + runtime database
  + Discord shell
  + dashboard
  + Codex fabric
  + bounded loop supervisor
```

In other words:

- not an OpenClaw-style prompt swarm
- not Codex-only orchestration
- not a toy one-shot agent loop

The product keeps the natural IM shell, but the durable truth lives in workflows, state, artifacts, approvals, and review.

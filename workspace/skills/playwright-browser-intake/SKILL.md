# Playwright Browser Intake

Use this skill only when search, feeds, and direct fetches are insufficient.

## Purpose

- recover content from JavaScript-heavy pages
- inspect pages that block simple fetch flows
- keep browser use bounded, explainable, and rare

## Workflow

1. Confirm that the search/feed path was attempted first.
2. Open the target page with the configured Playwright browser endpoint.
3. Wait only for the minimal page state needed to extract the signal.
4. Capture the canonical URL, page title, visible publication time, and the exact evidence used.
5. Return a concise summary with citations and a note explaining why browser fallback was necessary.

## Guardrails

- Use headless browser fallback only for dynamic pages, anti-bot friction, or missing content.
- Keep browser sessions short and focused on one objective.
- Do not rely on browser-only evidence when an official API or feed disagrees.
- Stop and report the blocker if the page requires login, complex interaction, or unclear legal access.

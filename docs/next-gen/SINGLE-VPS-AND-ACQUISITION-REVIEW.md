# Single-VPS And Acquisition Review

This page records the current optimization checklist for the "single VPS first" product path and the review conclusions that now shape implementation.

## Optimization Checklist

- promote `single_vps_compact` into a first-class deployment profile
- keep the authority model unchanged even when deployment collapses to one machine
- preserve one Discord bot and one owner-facing control path
- make Codex research, browser fallback, and dashboard coexist safely on one VPS
- prefer skill-based acquisition over ad-hoc prompting
- make Playwright a governed fallback, not the default crawler
- keep the acquisition stack free of paid search or browser APIs
- make deployment steps shorter and easier to audit

## Multi-Expert Review

### Product review

- The repository already had a viable two-VPS production story, but the one-VPS path still felt like a bootstrap convenience rather than a product mode.
- The simplest product path should be one command on one VPS, not "pretend the local bootstrap stack is good enough."

### Infrastructure review

- A single VPS is acceptable if the topology remains logically separated and the noisy Codex worker path stays budgeted.
- Browser automation must be an exception path on one machine because it competes directly with trading, Discord, and database resources.

### Research and learning review

- Codex web search is strong enough to be the primary discovery layer.
- A durable research product still needs free local fallbacks: SearXNG-style metasearch, RSS and RSSHub feeds, then Playwright.
- Search, feed, and browser workflows should be expressed as explicit skills so the system does not rediscover the same method by prompt every time.

### Security review

- A single-VPS product must still keep the final trading authority singular and explicit.
- Browser and scrape capabilities should never silently become the default acquisition path.
- The operator should be able to inspect whether the local fallback stack is present before trusting unattended learning.

## Resulting Implementation Direction

- `single_vps_compact` becomes a supported deployment topology.
- `quickstart-single-vps.sh` becomes the shortest one-machine entrypoint, with `onboard-single-vps.sh` as the draft-first path.
- The Core stack can host the Codex worker runtime when the single-VPS topology is selected.
- The acquisition stack now treats SearXNG, RSSHub, repo-local skills, and Playwright as first-class layers.
- Two repo-local acquisition skills are now expected:
  - `skills/search-rss-intake/SKILL.md`
  - `skills/playwright-browser-intake/SKILL.md`

## What This Slice Does Not Claim

- It does not claim that every social network can be scraped reliably without friction.
- It does not treat Playwright as a permanent always-on collector.
- It does not remove the long-term value of a two-VPS authority split.

The point of this slice is narrower and more practical: make the one-VPS product path honest, deployable, and aligned with the long-term acquisition architecture instead of leaving it as a vague bootstrap mode.

# Contributing Guide

Thank you for improving Quant Evo Next-Gen.

This project mixes product surfaces, automation, and trading-system safety concerns, so changes should be easy to review, easy to verify, and easy to operate.

## Before you start

- Read [README.md](README.md) for the product overview.
- Read [docs/next-gen/README.md](docs/next-gen/README.md) for the docs index.
- If your change touches deployment or owner operations, read:
  - [docs/next-gen/GITHUB-TO-VPS-DEPLOYMENT.md](docs/next-gen/GITHUB-TO-VPS-DEPLOYMENT.md)
  - [docs/next-gen/VPS-DEPLOYMENT-RUNBOOK.md](docs/next-gen/VPS-DEPLOYMENT-RUNBOOK.md)
  - [docs/next-gen/OWNER-OPERATION-QUICKSTART.md](docs/next-gen/OWNER-OPERATION-QUICKSTART.md)

## What good contributions look like

- A clear user or operator problem is being solved.
- The change fits the current product direction.
- Docs are updated when behavior, deployment, or operator steps change.
- Verification is included and honest about what was and was not tested.
- High-risk behavior is not hidden behind vague language.

## Local verification

For most backend or contract changes:

```bash
py -m pytest -q
py -m compileall src tests alembic/versions
```

For dashboard changes:

```bash
cd apps/dashboard-web
npm run build
```

If your change affects deployment or owner operations, review the relevant runbooks and examples as part of the change.

## Pull request expectations

Each pull request should explain:

- what changed
- why it changed
- how it was verified
- what operators need to know
- whether docs were updated

Use the pull request template in this repo.

## Documentation standard

When changing behavior that affects an owner, operator, or deploy workflow, update the relevant docs in the same PR.

Common files to update:

- [README.md](README.md)
- [docs/next-gen/README.md](docs/next-gen/README.md)
- [docs/next-gen/GITHUB-TO-VPS-DEPLOYMENT.md](docs/next-gen/GITHUB-TO-VPS-DEPLOYMENT.md)
- [docs/next-gen/OWNER-OPERATION-QUICKSTART.md](docs/next-gen/OWNER-OPERATION-QUICKSTART.md)
- [docs/next-gen/CURRENT-DELIVERY-STATUS.md](docs/next-gen/CURRENT-DELIVERY-STATUS.md)

## Security and secrets

- Never commit secrets, broker credentials, session tokens, or private URLs with live access.
- Do not paste real credentials into issues or PR comments.
- Use placeholders in docs and screenshots.
- Follow [SECURITY.md](SECURITY.md) for vulnerability reporting.

## Scope discipline

Prefer focused PRs.

Good examples:

- improve owner onboarding copy
- fix a deployment preflight check
- tighten a risk-control edge case
- polish the dashboard status presentation

Avoid mixing unrelated refactors with deploy, trading, or docs changes unless there is a real reason to do them together.

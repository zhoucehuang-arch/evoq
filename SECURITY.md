# Security Policy

Quant Evo Next-Gen handles automation, deployment workflows, and broker-facing behavior. Security issues should be reported privately.

## Supported branch

Security fixes are expected to land on:

- `main`

## How to report a vulnerability

Please do not open a public issue for:

- leaked credentials
- broker or funding-path vulnerabilities
- privilege-escalation paths
- remote execution paths
- secrets exposure in logs, prompts, artifacts, or deploy flows

Preferred reporting path:

1. Use GitHub private vulnerability reporting if it is enabled for this repository.
2. If not, contact the maintainer through a private channel and include enough detail to reproduce and assess the issue safely.

## What to include

- affected area
- impact
- reproduction steps
- configuration assumptions
- whether the issue affects paper mode, live mode, or both
- whether credentials or operator approvals are involved

## Disclosure guidance

- Do not share live credentials in the report.
- Use redacted examples where possible.
- Give maintainers time to reproduce and patch the issue before public disclosure.

# Support

## Where to start

For most questions, start with:

1. [README.md](README.md)
2. [docs/next-gen/README.md](docs/next-gen/README.md)
3. [docs/next-gen/FAQ.md](docs/next-gen/FAQ.md)

## Deployment and operations help

Use these first:

- [docs/next-gen/GITHUB-TO-VPS-DEPLOYMENT.md](docs/next-gen/GITHUB-TO-VPS-DEPLOYMENT.md)
- [docs/next-gen/VPS-DEPLOYMENT-RUNBOOK.md](docs/next-gen/VPS-DEPLOYMENT-RUNBOOK.md)
- [docs/next-gen/OWNER-OPERATION-QUICKSTART.md](docs/next-gen/OWNER-OPERATION-QUICKSTART.md)
- [docs/next-gen/BREAK-GLASS-RUNBOOK.md](docs/next-gen/BREAK-GLASS-RUNBOOK.md)

## If the system is already running

Check these first:

- `./ops/bin/core-smoke.sh`
- `./ops/bin/worker-smoke.sh`
- `/api/v1/system/doctor`
- dashboard health and Discord responsiveness

## Filing a useful issue

Include:

- what you were trying to do
- what happened instead
- exact commands or prompts used
- which environment was affected
- relevant logs or screenshots with secrets removed
- which docs you already followed

## Security issues

For vulnerabilities or secret exposure, do not use public issues. Follow [SECURITY.md](SECURITY.md).

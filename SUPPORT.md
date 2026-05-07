# Support

## Where to start

For most questions, start with:

1. [README.md](README.md)
2. [README.zh-CN.md](README.zh-CN.md) if you prefer Chinese
3. [docs/next-gen/EVOQ-BEGINNER-README.md](docs/next-gen/EVOQ-BEGINNER-README.md)
4. [docs/next-gen/EVOQ-USER-MANUAL.md](docs/next-gen/EVOQ-USER-MANUAL.md)
5. [docs/next-gen/README.md](docs/next-gen/README.md)
6. [docs/next-gen/FAQ.md](docs/next-gen/FAQ.md)

## Deployment and operations help

Use these first:

- [docs/next-gen/GITHUB-TO-VPS-DEPLOYMENT.md](docs/next-gen/GITHUB-TO-VPS-DEPLOYMENT.md)
- [docs/next-gen/VPS-DEPLOYMENT-RUNBOOK.md](docs/next-gen/VPS-DEPLOYMENT-RUNBOOK.md)
- [docs/next-gen/OWNER-OPERATION-QUICKSTART.md](docs/next-gen/OWNER-OPERATION-QUICKSTART.md)
- [docs/next-gen/BREAK-GLASS-RUNBOOK.md](docs/next-gen/BREAK-GLASS-RUNBOOK.md)

## If the system is already running

Check these first:

- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\smoke_local.ps1` for local Windows runs
- `./ops/bin/core-smoke.sh` for Core VPS deployments
- `./ops/bin/worker-smoke.sh` for Worker VPS deployments
- `/api/v1/system/doctor`
- dashboard health and Telegram/Discord gateway responsiveness, depending on your deployment

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

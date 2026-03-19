# GitHub to VPS Deployment Guide

This is the recommended path if you want to publish the project on GitHub first, then deploy it onto your VPS nodes by `git clone` and later maintain it by `git pull`.

Recommended production topology:

- `1 Discord bot`
- `1 Core VPS`
- `1 Worker VPS`

The canonical repo path on both VPS nodes is:

- `/opt/quant-evo-nextgen`

## 中文部署指南

### 1. 部署前准备

你需要准备：

- 一个 GitHub 仓库
- 两台 Ubuntu 或 Debian VPS
- Core 与 Worker 之间的私网互通能力
- Discord Bot Token、Guild ID、频道 ID、允许控制的用户 ID
- OpenAI 或中转 API Key
- 如果你使用第三方中转，还需要中转地址 `QE_OPENAI_BASE_URL`

建议：

- 生产形态使用 `2 VPS`，不要把 Worker 和 Core 长期混在一台机器上
- 第一次上线先保持 `paper` 模式
- 如果 Worker 要访问 Core 的 Postgres，请优先使用 Tailscale 或其他私网地址，不要直接暴露公网数据库

### 2. 先把本地项目上传到 GitHub

如果你的本地目录还不是一个 Git 仓库，可以在本地机器执行：

```bash
git init
git branch -M main
git add .
git commit -m "Initial deployable Quant Evo Next-Gen"
git remote add origin <your-github-repo-url>
git push -u origin main
```

如果你已经有 Git 仓库，只需要：

```bash
git add .
git commit -m "Update deployment-ready docs and runtime"
git push
```

### 3. 在 Core VPS 上部署

在 Core VPS 上执行：

```bash
cd /opt
sudo git clone <your-github-repo-url> quant-evo-nextgen
sudo chown -R "$USER":"$USER" /opt/quant-evo-nextgen
cd /opt/quant-evo-nextgen
chmod +x ops/bin/*.sh
sudo ./ops/bin/install-host-deps.sh
./ops/bin/bootstrap-node.sh core
```

然后检查并填写：

- `ops/production/core/core.env`

Core 至少要填这些：

- `QE_POSTGRES_PASSWORD`
- `QE_DISCORD_TOKEN`
- `QE_DISCORD_GUILD_ID`
- `QE_DISCORD_CONTROL_CHANNEL_ID`
- `QE_DISCORD_APPROVALS_CHANNEL_ID`
- `QE_DISCORD_ALERTS_CHANNEL_ID`
- `QE_DISCORD_ALLOWED_USER_IDS`
- `QE_OPENAI_API_KEY`
- `QE_OPENAI_BASE_URL`，如果你使用第三方中转
- `QE_DASHBOARD_ACCESS_USERNAME`
- `QE_DASHBOARD_ACCESS_PASSWORD`
- `QE_DASHBOARD_API_TOKEN`

建议第一次启动保持这些安全默认值：

- `QE_DEFAULT_BROKER_ADAPTER=paper_sim`
- `QE_DEFAULT_BROKER_ENVIRONMENT=paper`
- `QE_POSTGRES_BIND_HOST=127.0.0.1`
- `QE_API_BIND_HOST=127.0.0.1`
- `QE_DASHBOARD_BIND_HOST=127.0.0.1`

填写后启动：

```bash
cd /opt/quant-evo-nextgen
./ops/bin/core-up.sh
./ops/bin/core-smoke.sh
```

### 4. 在 Worker VPS 上部署

在 Worker VPS 上执行：

```bash
cd /opt
sudo git clone <your-github-repo-url> quant-evo-nextgen
sudo chown -R "$USER":"$USER" /opt/quant-evo-nextgen
cd /opt/quant-evo-nextgen
chmod +x ops/bin/*.sh
sudo ./ops/bin/install-host-deps.sh
./ops/bin/bootstrap-node.sh worker
```

然后检查并填写：

- `ops/production/worker/worker.env`

Worker 至少要填这些：

- `QE_POSTGRES_URL`
- `QE_OPENAI_API_KEY`
- `QE_OPENAI_BASE_URL`，如果你使用第三方中转

重要规则：

- `QE_POSTGRES_URL` 必须指向 Core 的私网地址，不能是 `localhost` 或 `127.0.0.1`
- 不要把 broker 凭证放到 Worker
- Core 上如果要让 Worker 访问 Postgres，需要把 `QE_POSTGRES_BIND_HOST` 改成 Core 的私网 IP 或 Tailscale IP

填写后启动：

```bash
cd /opt/quant-evo-nextgen
./ops/bin/worker-up.sh
./ops/bin/worker-smoke.sh
```

### 5. 设置开机自启

Core VPS：

```bash
cd /opt/quant-evo-nextgen
sudo ./ops/bin/install-systemd.sh core /opt/quant-evo-nextgen
```

Worker VPS：

```bash
cd /opt/quant-evo-nextgen
sudo ./ops/bin/install-systemd.sh worker /opt/quant-evo-nextgen
```

### 6. 第一次安全运行建议

第一次上线时，不要直接开 live 交易。建议顺序是：

1. Core 和 Worker 都先通过 smoke 检查
2. Dashboard 可正常打开
3. Discord Bot 只响应你允许的账号和频道
4. 先保持 `paper` 模式运行
5. 等第一次 broker sync 正常、风控状态正常后，再考虑切换到真实券商纸面环境或更进一步的 live 审批

### 7. 后续通过 GitHub 更新 VPS

以后每次你把更新推到 GitHub 后，在 Core 和 Worker 上分别执行：

```bash
cd /opt/quant-evo-nextgen
git pull
```

Core：

```bash
cd /opt/quant-evo-nextgen
./ops/bin/update-from-github.sh core
```

Worker：

```bash
cd /opt/quant-evo-nextgen
./ops/bin/update-from-github.sh worker
```

如果你更希望手动执行，也可以继续使用：

- `./ops/bin/core-up.sh`
- `./ops/bin/core-smoke.sh`
- `./ops/bin/worker-up.sh`
- `./ops/bin/worker-smoke.sh`

### 8. 常见错误

- Worker 的 `QE_POSTGRES_URL` 不能写成 `localhost`
- Worker 不能带 Core 专属密钥或 broker 凭证
- 如果你用中转，Core 和 Worker 都要配置 `QE_OPENAI_API_KEY`
- 如果你用中转，Core 和 Worker 都要配置 `QE_OPENAI_BASE_URL`
- 如果你把 Dashboard 对外公开，优先使用反向代理，不要直接把 API 暴露到公网
- 在第一次完整 bring-up 成功前，不要急着切到 live

### 9. 建议阅读顺序

1. [VPS-DEPLOYMENT-RUNBOOK.md](VPS-DEPLOYMENT-RUNBOOK.md)
2. [OWNER-OPERATION-QUICKSTART.md](OWNER-OPERATION-QUICKSTART.md)
3. [CURRENT-DELIVERY-STATUS.md](CURRENT-DELIVERY-STATUS.md)
4. [BREAK-GLASS-RUNBOOK.md](BREAK-GLASS-RUNBOOK.md)

## English Deployment Guide

### 1. Before You Start

Prepare the following:

- a GitHub repository
- two Ubuntu or Debian VPS nodes
- private connectivity between Core and Worker
- Discord bot token, guild ID, channel IDs, and allowed owner user IDs
- an OpenAI or relay API key
- `QE_OPENAI_BASE_URL` if you use a third-party relay

Recommended posture:

- use `2 VPS` for production
- keep the first activation in `paper` mode
- use Tailscale or another private-network path for Worker-to-Core Postgres access

### 2. Publish the Local Project to GitHub

If your local folder is not already a Git repository:

```bash
git init
git branch -M main
git add .
git commit -m "Initial deployable Quant Evo Next-Gen"
git remote add origin <your-github-repo-url>
git push -u origin main
```

If it is already a Git repository:

```bash
git add .
git commit -m "Update deployment-ready docs and runtime"
git push
```

### 3. Deploy on the Core VPS

Run on the Core VPS:

```bash
cd /opt
sudo git clone <your-github-repo-url> quant-evo-nextgen
sudo chown -R "$USER":"$USER" /opt/quant-evo-nextgen
cd /opt/quant-evo-nextgen
chmod +x ops/bin/*.sh
sudo ./ops/bin/install-host-deps.sh
./ops/bin/bootstrap-node.sh core
```

Then review and fill:

- `ops/production/core/core.env`

Minimum Core values:

- `QE_POSTGRES_PASSWORD`
- `QE_DISCORD_TOKEN`
- `QE_DISCORD_GUILD_ID`
- `QE_DISCORD_CONTROL_CHANNEL_ID`
- `QE_DISCORD_APPROVALS_CHANNEL_ID`
- `QE_DISCORD_ALERTS_CHANNEL_ID`
- `QE_DISCORD_ALLOWED_USER_IDS`
- `QE_OPENAI_API_KEY`
- `QE_OPENAI_BASE_URL` if you use a relay
- `QE_DASHBOARD_ACCESS_USERNAME`
- `QE_DASHBOARD_ACCESS_PASSWORD`
- `QE_DASHBOARD_API_TOKEN`

Recommended safe first-boot defaults:

- `QE_DEFAULT_BROKER_ADAPTER=paper_sim`
- `QE_DEFAULT_BROKER_ENVIRONMENT=paper`
- `QE_POSTGRES_BIND_HOST=127.0.0.1`
- `QE_API_BIND_HOST=127.0.0.1`
- `QE_DASHBOARD_BIND_HOST=127.0.0.1`

Start the Core stack:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/core-up.sh
./ops/bin/core-smoke.sh
```

### 4. Deploy on the Worker VPS

Run on the Worker VPS:

```bash
cd /opt
sudo git clone <your-github-repo-url> quant-evo-nextgen
sudo chown -R "$USER":"$USER" /opt/quant-evo-nextgen
cd /opt/quant-evo-nextgen
chmod +x ops/bin/*.sh
sudo ./ops/bin/install-host-deps.sh
./ops/bin/bootstrap-node.sh worker
```

Then review and fill:

- `ops/production/worker/worker.env`

Minimum Worker values:

- `QE_POSTGRES_URL`
- `QE_OPENAI_API_KEY`
- `QE_OPENAI_BASE_URL` if you use a relay

Important rules:

- `QE_POSTGRES_URL` must point to the Core private-network address, not `localhost`
- do not place broker credentials on the Worker
- if the Worker must reach Core Postgres, set Core `QE_POSTGRES_BIND_HOST` to a private-network or Tailscale IP

Start the Worker stack:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/worker-up.sh
./ops/bin/worker-smoke.sh
```

### 5. Enable Start-on-Boot

Core VPS:

```bash
cd /opt/quant-evo-nextgen
sudo ./ops/bin/install-systemd.sh core /opt/quant-evo-nextgen
```

Worker VPS:

```bash
cd /opt/quant-evo-nextgen
sudo ./ops/bin/install-systemd.sh worker /opt/quant-evo-nextgen
```

### 6. First Safe Activation

Do not switch straight into live trading. Recommended order:

1. both Core and Worker pass their smoke checks
2. the dashboard loads
3. the Discord bot responds only in approved owner channels
4. the system stays in `paper` mode first
5. only after clean broker sync and healthy risk posture should you consider paper-broker activation or later live promotion

### 7. Update from GitHub Later

After you push updates to GitHub, run this on both nodes:

```bash
cd /opt/quant-evo-nextgen
git pull
```

Then restart and smoke-check the appropriate role:

Core:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/update-from-github.sh core
```

Worker:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/update-from-github.sh worker
```

If you prefer the explicit manual path, you can still run:

- `./ops/bin/core-up.sh`
- `./ops/bin/core-smoke.sh`
- `./ops/bin/worker-up.sh`
- `./ops/bin/worker-smoke.sh`

### 8. Common Mistakes

- using `localhost` in Worker `QE_POSTGRES_URL`
- placing Core-only or broker secrets on the Worker
- forgetting to set `QE_OPENAI_API_KEY` on both nodes
- forgetting to set `QE_OPENAI_BASE_URL` on both nodes when using a relay
- exposing the API directly to the public internet
- switching to live before the first clean paper deployment and smoke cycle

### 9. Recommended Reading Order

1. [VPS-DEPLOYMENT-RUNBOOK.md](VPS-DEPLOYMENT-RUNBOOK.md)
2. [OWNER-OPERATION-QUICKSTART.md](OWNER-OPERATION-QUICKSTART.md)
3. [CURRENT-DELIVERY-STATUS.md](CURRENT-DELIVERY-STATUS.md)
4. [BREAK-GLASS-RUNBOOK.md](BREAK-GLASS-RUNBOOK.md)

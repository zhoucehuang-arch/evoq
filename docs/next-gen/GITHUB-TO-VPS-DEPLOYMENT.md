# GitHub to VPS Deployment Guide

This guide is for the owner who wants to publish the repository on GitHub first, then deploy it to VPS nodes with `git clone`, and later maintain it with `git pull`.

## English

### Recommended Starting Point

The product now supports two valid deployment shapes:

- simplest first deploy: `1 VPS` with `single_vps_compact`
- long-term stronger isolation: `1 Core VPS + 1 Worker VPS`

If this is your first real deployment, start with `1 VPS` unless you already know you need the two-node shape.

### What You Need Before You Start

- a GitHub repository for this project
- one Ubuntu or Debian VPS for the first deploy
- Discord bot token, guild ID, channel IDs, and allowed owner user IDs
- an OpenAI-compatible API key or relay key
- `QE_OPENAI_BASE_URL` if you use a relay
- optional broker credentials if you plan to move beyond `paper`

### 1. Push the Project to GitHub

If the local folder is not already a Git repository:

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
git commit -m "Update deployment-ready runtime"
git push
```

### 2. Deploy the One-VPS Product Path

Run on the VPS:

```bash
cd /opt
sudo git clone <your-github-repo-url> quant-evo-nextgen
sudo chown -R "$USER":"$USER" /opt/quant-evo-nextgen
cd /opt/quant-evo-nextgen
chmod +x ops/bin/*.sh
./ops/bin/quickstart-single-vps.sh
```

This creates the simplest supported product shape:

- Core services
- dashboard
- Discord bot
- Postgres
- Codex runner on the same host

### 3. Fill the Core Env File

Edit:

- `ops/production/core/core.env`

Minimum values:

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

Recommended safe first-boot values:

- `QE_DEPLOYMENT_TOPOLOGY=single_vps_compact`
- `QE_DEFAULT_BROKER_ADAPTER=paper_sim`
- `QE_DEFAULT_BROKER_ENVIRONMENT=paper`
- `QE_POSTGRES_BIND_HOST=127.0.0.1`
- `QE_API_BIND_HOST=127.0.0.1`
- `QE_DASHBOARD_BIND_HOST=127.0.0.1`

### 4. Owner-Friendly Draft Control

If you prefer to separate host preparation from app onboarding, use:

```bash
./ops/bin/quickstart-single-vps.sh
```

If you prefer to prepare the single-VPS draft first and start the stack later, use:

```bash
./ops/bin/onboard-single-vps.sh --no-start
```

If you want the lower-level owner CLI instead of the shell wrapper, use:

```bash
py -m quant_evo_nextgen.runner.deploy_config --repo-root . onboard-single-vps
py -m quant_evo_nextgen.runner.deploy_config --repo-root . status core
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core 中转地址 https://relay.example.com/v1
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core 中转key <secret>
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core Playwright启用 true
```

### 5. Start and Verify

```bash
cd /opt/quant-evo-nextgen
./ops/bin/core-up.sh
./ops/bin/core-smoke.sh
```

Also check:

- dashboard loads
- Discord bot responds only in the allowed owner path
- `/api/v1/system/doctor` reports no `fail`

### 6. Safe First Activation

Do not switch straight into live trading.

Recommended order:

1. finish the first clean bring-up on the single VPS
2. keep the broker path in `paper`
3. let the first broker sync and reconciliation finish cleanly
4. verify dashboard, Discord, and doctor all agree on runtime health
5. only then consider a paper-broker path or later live approval

### 7. Scale to Core + Worker Later

When you want stronger isolation or more research throughput, keep the same repo and add a second machine:

- Core remains the authority node
- Worker runs Codex-heavy execution and research loops
- broker credentials stay on Core only
- Worker connects to Core Postgres through a private-network address

Bootstrap the Worker later with:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/bootstrap-node.sh worker
```

Then fill:

- `ops/production/worker/worker.env`

Minimum Worker values:

- `QE_POSTGRES_URL`
- `QE_OPENAI_API_KEY`
- `QE_OPENAI_BASE_URL` if you use a relay

Important rules:

- `QE_POSTGRES_URL` must point to the Core private-network address, not `localhost`
- do not place broker credentials on the Worker
- do not bootstrap a Worker at all when you intentionally stay on `single_vps_compact`

### 8. Enable Start-on-Boot

Single-VPS or Core node:

```bash
cd /opt/quant-evo-nextgen
sudo ./ops/bin/install-systemd.sh core /opt/quant-evo-nextgen
```

Worker node, when used:

```bash
cd /opt/quant-evo-nextgen
sudo ./ops/bin/install-systemd.sh worker /opt/quant-evo-nextgen
```

### 9. Update Later from GitHub

On the single-VPS or Core host:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/update-from-github.sh core
```

On the Worker, when used:

```bash
cd /opt/quant-evo-nextgen
./ops/bin/update-from-github.sh worker
```

### 10. Common Mistakes

- switching to live before the first clean paper deployment
- filling Worker secrets on a one-VPS deployment that does not use a Worker
- leaving `QE_OPENAI_BASE_URL` empty when you depend on a relay
- exposing the API directly to the public internet
- putting broker credentials on the Worker

### Recommended Reading Order

1. [README.md](../../README.md)
2. [VPS-DEPLOYMENT-RUNBOOK.md](VPS-DEPLOYMENT-RUNBOOK.md)
3. [OWNER-OPERATION-QUICKSTART.md](OWNER-OPERATION-QUICKSTART.md)
4. [FIRST-PAPER-RUN-CHECKLIST.md](FIRST-PAPER-RUN-CHECKLIST.md)
5. [CURRENT-DELIVERY-STATUS.md](CURRENT-DELIVERY-STATUS.md)

## 中文

### 推荐起步方式

这套系统现在支持两种部署形态：

- 最简单的首次部署：`1 VPS` + `single_vps_compact`
- 长期更稳的隔离形态：`1 Core VPS + 1 Worker VPS`

如果这是你的第一次真实部署，建议先用 `1 VPS` 跑通，再决定要不要扩成两台机器。

### 部署前需要准备什么

- 这个项目对应的 GitHub 仓库
- 一台 Ubuntu 或 Debian VPS
- Discord Bot Token、Guild ID、频道 ID、允许控制的 owner 用户 ID
- OpenAI 兼容 API Key 或中转 Key
- 如果你使用中转，还要准备 `QE_OPENAI_BASE_URL`
- 如果后续准备接近真实交易，还要准备 broker 凭证

### 1. 先把项目推到 GitHub

如果本地目录还不是 Git 仓库：

```bash
git init
git branch -M main
git add .
git commit -m "Initial deployable Quant Evo Next-Gen"
git remote add origin <your-github-repo-url>
git push -u origin main
```

如果已经是 Git 仓库：

```bash
git add .
git commit -m "Update deployment-ready runtime"
git push
```

### 2. 走一台 VPS 的产品路径

在 VPS 上执行：

```bash
cd /opt
sudo git clone <your-github-repo-url> quant-evo-nextgen
sudo chown -R "$USER":"$USER" /opt/quant-evo-nextgen
cd /opt/quant-evo-nextgen
chmod +x ops/bin/*.sh
sudo ./ops/bin/install-host-deps.sh
./ops/bin/onboard-single-vps.sh
```

这样会得到最简单、也最推荐的首次部署形态：

- Core 服务
- dashboard
- Discord bot
- Postgres
- 同机运行的 Codex runner

### 3. 填写 Core 环境文件

编辑：

- `ops/production/core/core.env`

至少要填这些值：

- `QE_POSTGRES_PASSWORD`
- `QE_DISCORD_TOKEN`
- `QE_DISCORD_GUILD_ID`
- `QE_DISCORD_CONTROL_CHANNEL_ID`
- `QE_DISCORD_APPROVALS_CHANNEL_ID`
- `QE_DISCORD_ALERTS_CHANNEL_ID`
- `QE_DISCORD_ALLOWED_USER_IDS`
- `QE_OPENAI_API_KEY`
- 如果用中转则填写 `QE_OPENAI_BASE_URL`
- `QE_DASHBOARD_ACCESS_USERNAME`
- `QE_DASHBOARD_ACCESS_PASSWORD`
- `QE_DASHBOARD_API_TOKEN`

推荐第一次启动保持这些安全默认值：

- `QE_DEPLOYMENT_TOPOLOGY=single_vps_compact`
- `QE_DEFAULT_BROKER_ADAPTER=paper_sim`
- `QE_DEFAULT_BROKER_ENVIRONMENT=paper`
- `QE_POSTGRES_BIND_HOST=127.0.0.1`
- `QE_API_BIND_HOST=127.0.0.1`
- `QE_DASHBOARD_BIND_HOST=127.0.0.1`

### 4. 如果你更喜欢引导式配置

如果你不想直接手改 env 文件，也可以用 owner-friendly 的引导方式：

```bash
./ops/bin/onboard-single-vps.sh --no-start
py -m quant_evo_nextgen.runner.deploy_config --repo-root . onboard-single-vps
py -m quant_evo_nextgen.runner.deploy_config --repo-root . status core
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core 中转地址 https://relay.example.com/v1
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core 中转key <secret>
py -m quant_evo_nextgen.runner.deploy_config --repo-root . set-field core Playwright启用 true
```

### 5. 启动并验证

```bash
cd /opt/quant-evo-nextgen
./ops/bin/core-up.sh
./ops/bin/core-smoke.sh
```

同时确认：

- dashboard 能打开
- Discord bot 只在允许的 owner 路径里响应
- `/api/v1/system/doctor` 没有 `fail`

### 6. 第一次安全激活顺序

不要一上来就切 live。

建议顺序是：

1. 先在单机上完成第一次干净的 bring-up
2. broker 保持在 `paper`
3. 等第一次 broker sync 和 reconciliation 都正常
4. 确认 dashboard、Discord 和 doctor 对系统健康的判断一致
5. 之后再考虑纸面券商环境或更后面的 live 审批

### 7. 后续再扩成 Core + Worker

当你需要更强的隔离或更高的研究吞吐时，再增加第二台机器：

- Core 继续做权威节点
- Worker 负责更重的 Codex 执行和研究循环
- broker 凭证只放在 Core
- Worker 通过私网地址连接 Core 的 Postgres

Worker 之后可以这样初始化：

```bash
cd /opt/quant-evo-nextgen
./ops/bin/bootstrap-node.sh worker
```

然后填写：

- `ops/production/worker/worker.env`

Worker 至少要填：

- `QE_POSTGRES_URL`
- `QE_OPENAI_API_KEY`
- 如果用中转则填写 `QE_OPENAI_BASE_URL`

重要规则：

- `QE_POSTGRES_URL` 必须指向 Core 的私网地址，不能写 `localhost`
- 不要把 broker 凭证放到 Worker
- 如果你决定长期保持 `single_vps_compact`，就不要再初始化 Worker

### 8. 设置开机自启

单 VPS 或 Core 节点：

```bash
cd /opt/quant-evo-nextgen
sudo ./ops/bin/install-systemd.sh core /opt/quant-evo-nextgen
```

Worker 节点，只有在你真的使用 Worker 时才需要：

```bash
cd /opt/quant-evo-nextgen
sudo ./ops/bin/install-systemd.sh worker /opt/quant-evo-nextgen
```

### 9. 以后通过 GitHub 更新

单 VPS 或 Core：

```bash
cd /opt/quant-evo-nextgen
./ops/bin/update-from-github.sh core
```

Worker，只有在你真的使用 Worker 时才需要：

```bash
cd /opt/quant-evo-nextgen
./ops/bin/update-from-github.sh worker
```

### 10. 常见错误

- 第一次 paper 跑通之前就急着切 live
- 明明是单 VPS，却去填 Worker 的配置
- 用中转却忘记填写 `QE_OPENAI_BASE_URL`
- 直接把 API 暴露到公网
- 把 broker 凭证错误地放到 Worker

### 推荐阅读顺序

1. [README.md](../../README.md)
2. [VPS-DEPLOYMENT-RUNBOOK.md](VPS-DEPLOYMENT-RUNBOOK.md)
3. [OWNER-OPERATION-QUICKSTART.md](OWNER-OPERATION-QUICKSTART.md)
4. [FIRST-PAPER-RUN-CHECKLIST.md](FIRST-PAPER-RUN-CHECKLIST.md)
5. [CURRENT-DELIVERY-STATUS.md](CURRENT-DELIVERY-STATUS.md)

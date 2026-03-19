from pathlib import Path


def test_core_and_worker_ops_assets_exist() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    required_paths = [
        repo_root / "ops" / "production" / "core" / "docker-compose.core.yml",
        repo_root / "ops" / "production" / "core" / "docker-compose.edge.yml",
        repo_root / "ops" / "production" / "core" / "core.env.example",
        repo_root / "ops" / "production" / "core" / "Caddyfile",
        repo_root / "ops" / "production" / "worker" / "docker-compose.worker.yml",
        repo_root / "ops" / "production" / "worker" / "worker.env.example",
        repo_root / "ops" / "bin" / "install-host-deps.sh",
        repo_root / "ops" / "bin" / "bootstrap-node.sh",
        repo_root / "ops" / "bin" / "core-up.sh",
        repo_root / "ops" / "bin" / "core-down.sh",
        repo_root / "ops" / "bin" / "core-smoke.sh",
        repo_root / "ops" / "bin" / "host-preflight.sh",
        repo_root / "ops" / "bin" / "deploy-config.sh",
        repo_root / "ops" / "bin" / "worker-up.sh",
        repo_root / "ops" / "bin" / "worker-down.sh",
        repo_root / "ops" / "bin" / "worker-smoke.sh",
        repo_root / "ops" / "bin" / "backup-postgres.sh",
        repo_root / "ops" / "bin" / "restore-postgres.sh",
        repo_root / "ops" / "bin" / "install-systemd.sh",
        repo_root / "ops" / "bin" / "qe-enter-safe-mode.sh",
        repo_root / "ops" / "systemd" / "quant-evo-core.service",
        repo_root / "ops" / "systemd" / "quant-evo-worker.service",
    ]

    missing = [str(path) for path in required_paths if not path.exists()]
    assert not missing, f"Missing required production ops assets: {missing}"


def test_ops_scripts_use_repo_local_deploy_wrapper() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    deploy_wrapper = (repo_root / "ops" / "bin" / "deploy-config.sh").read_text(encoding="utf-8")
    host_preflight = (repo_root / "ops" / "bin" / "host-preflight.sh").read_text(encoding="utf-8")
    bootstrap_node = (repo_root / "ops" / "bin" / "bootstrap-node.sh").read_text(encoding="utf-8")
    core_up = (repo_root / "ops" / "bin" / "core-up.sh").read_text(encoding="utf-8")
    worker_up = (repo_root / "ops" / "bin" / "worker-up.sh").read_text(encoding="utf-8")
    readme = (repo_root / "README.md").read_text(encoding="utf-8")

    assert "PYTHONPATH" in deploy_wrapper
    assert 'DEPLOY_CONFIG_SH' in core_up
    assert 'docker-compose.edge.yml' in core_up
    assert 'preflight core' in core_up
    assert 'DEPLOY_CONFIG_SH' in worker_up
    assert 'preflight worker' in worker_up
    assert "python3" in host_preflight
    assert "QE_SKIP_ENV_PREFLIGHT" in host_preflight
    assert 'HOST_PREFLIGHT_SH' in bootstrap_node
    assert 'QE_SKIP_ENV_PREFLIGHT=1' in bootstrap_node
    assert 'deploy-config.sh' in bootstrap_node
    assert "./ops/bin/install-host-deps.sh" in readme
    assert "./ops/bin/bootstrap-node.sh core" in readme
    assert "./ops/bin/bootstrap-node.sh worker" in readme
    assert "./ops/bin/deploy-config.sh init core" in readme
    assert "./ops/bin/deploy-config.sh init worker" in readme

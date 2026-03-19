from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from quant_evo_nextgen.services.deploy_config import DeployConfigService


def run(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv or sys.argv[1:])
    repo_root = Path(args.repo_root or ".").resolve()
    service = DeployConfigService(repo_root)

    if args.command == "init":
        overrides = dict(item.split("=", 1) for item in args.set or [])
        if args.broker_mode:
            overrides["__broker_mode__"] = args.broker_mode
        output_path = Path(args.output) if args.output else None
        created = service.initialize_env_file(
            role=args.role,
            output_path=output_path,
            overrides=overrides,
            overwrite=args.overwrite,
            interactive=not args.no_prompt,
        )
        report = service.run_preflight(role=args.role, env_path=created)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"Created env file: {created}")
            print(service.render_preflight_report(report))
        return 0 if report["status"] != "fail" else 1

    if args.command == "preflight":
        report = service.run_preflight(role=args.role, env_path=Path(args.env_path))
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(service.render_preflight_report(report))
        return 0 if report["status"] != "fail" else 1

    raise ValueError(f"Unsupported command: {args.command}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Quant Evo VPS config bootstrap and preflight helper.")
    parser.add_argument("--repo-root", help="Repo root path. Defaults to the current working directory.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create or update a deploy env file from the canonical template.")
    init_parser.add_argument("role", choices=["core", "worker", "research"])
    init_parser.add_argument("--output", help="Explicit output env path.")
    init_parser.add_argument("--set", action="append", help="Override env values in KEY=VALUE form.")
    init_parser.add_argument(
        "--broker-mode",
        choices=["paper_sim", "alpaca_paper", "alpaca_live"],
        help="Convenience switch for the Core default broker posture.",
    )
    init_parser.add_argument("--overwrite", action="store_true", help="Overwrite the output env file from the template.")
    init_parser.add_argument("--no-prompt", action="store_true", help="Do not prompt interactively. Use template values plus --set overrides only.")
    init_parser.add_argument("--json", action="store_true", help="Print the resulting preflight report as JSON.")

    preflight_parser = subparsers.add_parser("preflight", help="Validate a deploy env file before Docker bring-up.")
    preflight_parser.add_argument("role", choices=["core", "worker", "research"])
    preflight_parser.add_argument("env_path", help="Path to the env file to validate.")
    preflight_parser.add_argument("--json", action="store_true", help="Print the preflight report as JSON.")

    return parser


if __name__ == "__main__":
    raise SystemExit(run())

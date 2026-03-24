from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import sys
from pathlib import Path

from quant_evo_nextgen.services.deploy_config import DeployConfigService
from quant_evo_nextgen.services.owner_onboarding import OwnerOnboardingService


def run(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv or sys.argv[1:])
    repo_root = Path(args.repo_root or ".").resolve()
    service = DeployConfigService(repo_root)
    env_root = Path(args.env_root).resolve() if getattr(args, "env_root", None) else None
    onboarding = OwnerOnboardingService(repo_root, env_root=env_root)

    if args.command == "init":
        overrides = _parse_set_overrides(args.set)
        if args.broker_mode:
            overrides["__broker_mode__"] = args.broker_mode
        if args.market_mode:
            overrides["__market_mode__"] = args.market_mode
        if args.topology:
            overrides["QE_DEPLOYMENT_TOPOLOGY"] = args.topology
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

    if args.command == "onboard-single-vps":
        overrides = _parse_set_overrides(args.set)
        overrides["QE_DEPLOYMENT_TOPOLOGY"] = "single_vps_compact"
        overrides["__broker_mode__"] = "paper_sim"
        if args.market_mode:
            overrides["__market_mode__"] = args.market_mode
        output_path = Path(args.output) if args.output else None
        created = service.initialize_env_file(
            role="core",
            output_path=output_path,
            overrides=overrides,
            overwrite=args.overwrite,
            interactive=not args.no_prompt,
            prompt_profile="single_vps_minimal",
        )
        report = service.run_preflight(role="core", env_path=created)
        if args.json:
            print(
                json.dumps(
                    {
                        "env_path": str(created),
                        "topology": "single_vps_compact",
                        "broker_mode": "paper_sim",
                        "preflight": report,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(_render_single_vps_onboard_report(service=service, env_path=created, report=report))
        return 0 if report["status"] != "fail" else 1

    if args.command == "bootstrap":
        result = onboarding.bootstrap_role(args.role)
        if args.json:
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        else:
            print(result.summary_text)
        return 0 if result.preflight_status != "fail" else 1

    if args.command == "status":
        result = onboarding.status(args.role)
        if args.json:
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        else:
            print(result.summary_text)
        return 0 if result.preflight_status != "fail" else 1

    if args.command == "set-field":
        result = onboarding.set_field(
            role=args.role,
            field_alias=args.field,
            value=args.value,
        )
        if args.json:
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        else:
            print(result.summary_text)
        return 0 if result.preflight_status != "fail" else 1

    if args.command == "preflight":
        report = service.run_preflight(role=args.role, env_path=Path(args.env_path))
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(service.render_preflight_report(report))
        return 0 if report["status"] != "fail" else 1

    raise ValueError(f"Unsupported command: {args.command}")


def _parse_set_overrides(items: list[str] | None) -> dict[str, str]:
    return dict(item.split("=", 1) for item in items or [])


def _render_single_vps_onboard_report(
    *,
    service: DeployConfigService,
    env_path: Path,
    report: dict[str, object],
) -> str:
    checks = report.get("checks", [])
    top_message = ""
    if isinstance(checks, list):
        failures = [
            check
            for check in checks
            if isinstance(check, dict) and check.get("status") in {"fail", "warn"}
        ]
        if failures:
            top = failures[0]
            label = str(top.get("label") or top.get("key") or "Preflight Check")
            message = str(top.get("message") or "").strip()
            top_message = f"Top follow-up: {label} | {message}"
    lines = [
        f"Single-VPS deploy draft ready: {env_path}",
        "Pinned topology: single_vps_compact",
        "Pinned first-boot broker posture: paper_sim",
        "Dashboard username defaults to `owner`; password and API token are auto-generated if left blank.",
        f"Preflight status: {report['status']}",
    ]
    if top_message:
        lines.append(top_message)
    lines.append("")
    lines.append(service.render_preflight_report(report))
    lines.append("")
    lines.append("Next steps:")
    lines.append("1. Review the generated core env file and confirm your relay/Discord values are correct.")
    lines.append("2. Run `./ops/bin/core-up.sh` to start the stack, or use `./ops/bin/onboard-single-vps.sh` for the full guided path.")
    lines.append("3. Run `./ops/bin/core-smoke.sh` before treating the node as deploy-ready.")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Quant Evo VPS config bootstrap and preflight helper.")
    parser.add_argument("--repo-root", help="Repo root path. Defaults to the current working directory.")
    parser.add_argument(
        "--env-root",
        help="Optional env output directory for owner-onboarding style commands. Defaults to the canonical ops/production paths.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap_parser = subparsers.add_parser(
        "bootstrap",
        help="Owner-facing deployment bootstrap. Create the deploy draft env and run preflight.",
    )
    bootstrap_parser.add_argument("role", choices=["core", "worker", "research"])
    bootstrap_parser.add_argument("--json", action="store_true", help="Print the onboarding result as JSON.")

    status_parser = subparsers.add_parser(
        "status",
        help="Owner-facing deployment status. Read the current deploy draft and run preflight.",
    )
    status_parser.add_argument("role", choices=["core", "worker", "research"])
    status_parser.add_argument("--json", action="store_true", help="Print the onboarding result as JSON.")

    set_field_parser = subparsers.add_parser(
        "set-field",
        help="Owner-facing deployment config update. Set one deploy draft field and rerun preflight.",
    )
    set_field_parser.add_argument("role", choices=["core", "worker", "research"])
    set_field_parser.add_argument(
        "field",
        help="Field alias such as relaykey, deploymenttopology, SearXNG, or playwrightenabled.",
    )
    set_field_parser.add_argument("value", help="Field value.")
    set_field_parser.add_argument("--json", action="store_true", help="Print the onboarding result as JSON.")

    init_parser = subparsers.add_parser("init", help="Low-level deploy env bootstrap from the canonical template.")
    init_parser.add_argument("role", choices=["core", "worker", "research"])
    init_parser.add_argument("--output", help="Explicit output env path.")
    init_parser.add_argument("--set", action="append", help="Override env values in KEY=VALUE form.")
    init_parser.add_argument(
        "--broker-mode",
        choices=["paper_sim", "alpaca_paper", "alpaca_live"],
        help="Convenience switch for the Core default broker posture.",
    )
    init_parser.add_argument(
        "--topology",
        choices=["single_vps_compact", "two_vps_asymmetrical"],
        help="Deployment topology profile to write into the env file.",
    )
    init_parser.add_argument(
        "--market-mode",
        choices=["us", "cn"],
        help="Deployment market mode to write into the env file.",
    )
    init_parser.add_argument("--overwrite", action="store_true", help="Overwrite the output env file from the template.")
    init_parser.add_argument("--no-prompt", action="store_true", help="Do not prompt interactively. Use template values plus --set overrides only.")
    init_parser.add_argument("--json", action="store_true", help="Print the resulting preflight report as JSON.")

    onboard_single_vps_parser = subparsers.add_parser(
        "onboard-single-vps",
        help="OpenClaw-style single-VPS onboarding. Create or refresh the Core deploy draft with the minimal first-deploy prompts.",
    )
    onboard_single_vps_parser.add_argument("--output", help="Explicit output env path.")
    onboard_single_vps_parser.add_argument("--set", action="append", help="Override env values in KEY=VALUE form.")
    onboard_single_vps_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the output env file from the template before applying the single-VPS defaults.",
    )
    onboard_single_vps_parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="Do not prompt interactively. Use template values plus --set overrides only.",
    )
    onboard_single_vps_parser.add_argument(
        "--market-mode",
        choices=["us", "cn"],
        help="Single-VPS deployment market mode. `us` enables the US-equities and US-options product surface; `cn` enables the A-share product surface.",
    )
    onboard_single_vps_parser.add_argument("--json", action="store_true", help="Print the onboarding result as JSON.")

    preflight_parser = subparsers.add_parser("preflight", help="Validate a deploy env file before Docker bring-up.")
    preflight_parser.add_argument("role", choices=["core", "worker", "research"])
    preflight_parser.add_argument("env_path", help="Path to the env file to validate.")
    preflight_parser.add_argument("--json", action="store_true", help="Print the preflight report as JSON.")

    return parser


if __name__ == "__main__":
    raise SystemExit(run())

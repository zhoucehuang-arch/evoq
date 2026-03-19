from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from pathlib import Path

from quant_evo_nextgen.config import get_settings
from quant_evo_nextgen.contracts.codex import CodexRunRequest
from quant_evo_nextgen.logging_utils import configure_logging
from quant_evo_nextgen.services.codex import build_exec_command, ensure_paths_exist


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute or preview a Codex worker request.")
    parser.add_argument("--request", required=True, help="Path to a CodexRunRequest JSON file.")
    parser.add_argument("--execute", action="store_true", help="Execute the generated command.")
    return parser.parse_args()


def load_request(path: Path) -> CodexRunRequest:
    return CodexRunRequest.model_validate_json(path.read_text(encoding="utf-8"))


def main() -> int:
    configure_logging()
    settings = get_settings()
    args = parse_args()
    request_path = Path(args.request)
    request = load_request(request_path)
    ensure_paths_exist(request)
    command = build_exec_command(request, settings)

    if not args.execute:
        print(" ".join(shlex.quote(part) for part in command))
        return 0

    completed = subprocess.run(command, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())

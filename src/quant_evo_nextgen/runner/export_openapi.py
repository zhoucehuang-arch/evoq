from __future__ import annotations

import argparse
import json
from pathlib import Path

from quant_evo_nextgen.api.main import create_app


def main() -> int:
    parser = argparse.ArgumentParser(description="Export the EvoQ OpenAPI schema.")
    parser.add_argument("--output", default="docs/openapi.json", help="Output path for the OpenAPI JSON document.")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    app = create_app()
    output_path.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Export failed evaluation cases to JSONL or CSV."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if str(Path.cwd()) not in sys.path:
    sys.path.insert(0, str(Path.cwd()))

from app.services.badcase import BadcaseService


DEFAULT_REPORT_PATH = "evals/reports/latest_report.json"
DEFAULT_OUTPUT_PATH = "evals/badcases/badcases.jsonl"


def export_badcases(
    report_path: str = DEFAULT_REPORT_PATH,
    output_path: str = DEFAULT_OUTPUT_PATH,
    output_format: str | None = None,
) -> dict[str, Any]:
    service = BadcaseService(report_path=_project_root() / report_path)
    return service.export_badcases(
        export_path=_project_root() / output_path,
        output_format=output_format,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Export failed eval cases.")
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--output-path", default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--format", choices=["jsonl", "csv"], default=None)
    args = parser.parse_args()

    result = export_badcases(
        report_path=args.report_path,
        output_path=args.output_path,
        output_format=args.format,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _project_root() -> Path:
    cwd = Path.cwd()
    if cwd.name == "backend":
        return cwd.parent
    return cwd


if __name__ == "__main__":
    main()

"""Replay exported badcases with the mock provider."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if str(Path.cwd()) not in sys.path:
    sys.path.insert(0, str(Path.cwd()))

from app.services.badcase import replay_badcase_jsonl


DEFAULT_INPUT_PATH = "evals/badcases/badcases.jsonl"
DEFAULT_OUTPUT_PATH = "evals/reports/badcase_replay_report.json"


def replay_badcases(
    input_path: str = DEFAULT_INPUT_PATH,
    output_path: str | None = DEFAULT_OUTPUT_PATH,
    provider: str = "mock",
) -> dict[str, Any]:
    report = replay_badcase_jsonl(
        input_path=_project_root() / input_path,
        provider=provider,
    )

    if output_path:
        actual_output_path = _project_root() / output_path
        actual_output_path.parent.mkdir(parents=True, exist_ok=True)
        actual_output_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay badcases with mock provider.")
    parser.add_argument("--input-path", default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output-path", default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--provider", default="mock", choices=["mock", "deepseek", "openai"])
    args = parser.parse_args()

    report = replay_badcases(
        input_path=args.input_path,
        output_path=args.output_path,
        provider=args.provider,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


def _project_root() -> Path:
    cwd = Path.cwd()
    if cwd.name == "backend":
        return cwd.parent
    return cwd


if __name__ == "__main__":
    main()

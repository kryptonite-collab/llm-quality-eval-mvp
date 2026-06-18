import argparse
import json
from pathlib import Path
from typing import Any


def load_eval_report(report_path: str | Path) -> dict[str, Any]:
    return json.loads(Path(report_path).read_text(encoding="utf-8"))


def check_eval_report(
    report: dict[str, Any],
    min_pass_rate: float | None = None,
    max_badcase_count: int | None = None,
) -> tuple[bool, list[str]]:
    messages: list[str] = []
    pass_rate = float(report.get("pass_rate", 0.0))
    badcase_count = int(report.get("badcase_count", 0))

    if min_pass_rate is not None and pass_rate < min_pass_rate:
        messages.append(f"pass_rate {pass_rate} is below threshold {min_pass_rate}")

    if max_badcase_count is not None and badcase_count > max_badcase_count:
        messages.append(
            f"badcase_count {badcase_count} is above threshold {max_badcase_count}"
        )

    return not messages, messages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check an eval report against thresholds.")
    parser.add_argument("--report-path", required=True)
    parser.add_argument("--min-pass-rate", type=float, default=None)
    parser.add_argument("--max-badcase-count", type=int, default=None)
    args = parser.parse_args(argv)

    report = load_eval_report(args.report_path)
    passed, messages = check_eval_report(
        report=report,
        min_pass_rate=args.min_pass_rate,
        max_badcase_count=args.max_badcase_count,
    )

    if passed:
        print(
            "Eval report passed: "
            f"pass_rate={report.get('pass_rate')}, "
            f"badcase_count={report.get('badcase_count')}"
        )
        return 0

    print("Eval report failed:")
    for message in messages:
        print(f"- {message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

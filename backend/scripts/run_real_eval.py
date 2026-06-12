import argparse
import json
import os
from pathlib import Path

from app.services.eval_runner import PROJECT_ROOT, run_eval_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a small real-model eval batch.")
    parser.add_argument("--provider", default=os.getenv("LLM_PROVIDER") or "deepseek")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--report-path", default=None)
    parser.add_argument("--use-rag", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--prompt-version", default="baseline", choices=["baseline", "improved"])
    args = parser.parse_args()

    report_path = (
        Path(args.report_path)
        if args.report_path
        else PROJECT_ROOT / f"evals/reports/real_{args.provider}_report.json"
    )

    report = run_eval_dataset(
        report_path=report_path,
        provider=args.provider,
        limit=args.limit,
        use_rag=args.use_rag,
        prompt_version=args.prompt_version,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

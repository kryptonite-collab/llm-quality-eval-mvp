import argparse
import json
import os
from pathlib import Path

from app.services.eval_runner import PROJECT_ROOT, _format_report_path, run_eval_dataset
from app.services.prompt_compare import write_prompt_compare_report

DEFAULT_DATASET_PATH = PROJECT_ROOT / "evals/datasets/real_rag_sample.jsonl"
DEFAULT_BASELINE_REPORT_PATH = PROJECT_ROOT / "evals/reports/real_deepseek_baseline_report.json"
DEFAULT_IMPROVED_REPORT_PATH = PROJECT_ROOT / "evals/reports/real_deepseek_improved_report.json"
DEFAULT_COMPARE_REPORT_PATH = PROJECT_ROOT / "evals/reports/real_deepseek_compare_report.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run real-model prompt A/B evaluation.")
    parser.add_argument("--provider", default=os.getenv("LLM_PROVIDER") or "deepseek")
    parser.add_argument("--dataset-path", default=str(DEFAULT_DATASET_PATH))
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--baseline-report-path", default=str(DEFAULT_BASELINE_REPORT_PATH))
    parser.add_argument("--improved-report-path", default=str(DEFAULT_IMPROVED_REPORT_PATH))
    parser.add_argument("--compare-report-path", default=str(DEFAULT_COMPARE_REPORT_PATH))
    args = parser.parse_args()

    dataset_path = Path(args.dataset_path)
    baseline_report_path = Path(args.baseline_report_path)
    improved_report_path = Path(args.improved_report_path)
    compare_report_path = Path(args.compare_report_path)

    baseline_report = run_eval_dataset(
        dataset_path=dataset_path,
        report_path=baseline_report_path,
        provider=args.provider,
        limit=args.limit,
        use_rag=True,
        prompt_version="baseline",
    )
    improved_report = run_eval_dataset(
        dataset_path=dataset_path,
        report_path=improved_report_path,
        provider=args.provider,
        limit=args.limit,
        use_rag=True,
        prompt_version="improved",
    )
    compare_report = write_prompt_compare_report(
        baseline_report_path=baseline_report_path,
        improved_report_path=improved_report_path,
        compare_report_path=compare_report_path,
        dataset_path=dataset_path,
    )

    print(
        json.dumps(
            {
                "baseline": baseline_report["config"]["report_path"],
                "improved": improved_report["config"]["report_path"],
                "compare": _format_report_path(compare_report_path),
                "baseline_pass_rate": compare_report["baseline_pass_rate"],
                "improved_pass_rate": compare_report["improved_pass_rate"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

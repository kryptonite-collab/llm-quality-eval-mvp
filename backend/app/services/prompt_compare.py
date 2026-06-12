import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.services.eval_runner import _format_report_path


def load_report(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _index_results_by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("id")): item for item in report.get("results", [])}


def _build_changed_cases(
    baseline_report: dict[str, Any],
    improved_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    baseline_results = _index_results_by_id(baseline_report)
    improved_results = _index_results_by_id(improved_report)

    changed_cases: list[dict[str, Any]] = []
    improved_cases: list[str] = []
    regressed_cases: list[str] = []

    for case_id in sorted(set(baseline_results) & set(improved_results)):
        baseline = baseline_results[case_id]
        improved = improved_results[case_id]
        baseline_pass = bool(baseline.get("pass"))
        improved_pass = bool(improved.get("pass"))
        baseline_failed_metrics = baseline.get("failed_metrics", [])
        improved_failed_metrics = improved.get("failed_metrics", [])

        if (
            baseline_pass == improved_pass
            and baseline_failed_metrics == improved_failed_metrics
            and baseline.get("score") == improved.get("score")
        ):
            continue

        changed_cases.append(
            {
                "id": case_id,
                "question": improved.get("question") or baseline.get("question"),
                "baseline_pass": baseline_pass,
                "improved_pass": improved_pass,
                "baseline_score": baseline.get("score"),
                "improved_score": improved.get("score"),
                "baseline_failed_metrics": baseline_failed_metrics,
                "improved_failed_metrics": improved_failed_metrics,
            }
        )

        if not baseline_pass and improved_pass:
            improved_cases.append(case_id)
        elif baseline_pass and not improved_pass:
            regressed_cases.append(case_id)

    return changed_cases, improved_cases, regressed_cases


def build_prompt_compare_report(
    baseline_report: dict[str, Any],
    improved_report: dict[str, Any],
    dataset_path: str | Path,
) -> dict[str, Any]:
    changed_cases, improved_cases, regressed_cases = _build_changed_cases(
        baseline_report=baseline_report,
        improved_report=improved_report,
    )

    return {
        "provider": improved_report.get("provider") or baseline_report.get("provider"),
        "model": improved_report.get("model") or baseline_report.get("model"),
        "dataset": _format_report_path(dataset_path),
        "baseline_pass_rate": baseline_report.get("pass_rate"),
        "improved_pass_rate": improved_report.get("pass_rate"),
        "baseline_avg_latency_ms": baseline_report.get("avg_latency_ms"),
        "improved_avg_latency_ms": improved_report.get("avg_latency_ms"),
        "baseline_badcase_count": baseline_report.get("badcase_count"),
        "improved_badcase_count": improved_report.get("badcase_count"),
        "changed_cases": changed_cases,
        "improved_cases": improved_cases,
        "regressed_cases": regressed_cases,
        "generated_at": datetime.now(UTC).isoformat(),
    }


def write_prompt_compare_report(
    baseline_report_path: str | Path,
    improved_report_path: str | Path,
    compare_report_path: str | Path,
    dataset_path: str | Path,
) -> dict[str, Any]:
    compare_report = build_prompt_compare_report(
        baseline_report=load_report(baseline_report_path),
        improved_report=load_report(improved_report_path),
        dataset_path=dataset_path,
    )
    output_path = Path(compare_report_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(compare_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return compare_report

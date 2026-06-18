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


def _format_delta(improved_value: Any, baseline_value: Any) -> str:
    if improved_value is None or baseline_value is None:
        return "n/a"

    try:
        delta = float(improved_value) - float(baseline_value)
    except (TypeError, ValueError):
        return "n/a"

    return f"{delta:+.4f}"


def _case_rows(case_ids: list[str], changed_cases: list[dict[str, Any]]) -> list[str]:
    cases_by_id = {str(item["id"]): item for item in changed_cases}
    rows = []

    for case_id in case_ids:
        item = cases_by_id.get(str(case_id))
        if not item:
            continue

        rows.append(
            (
                "| {id} | {question} | {baseline_pass} | {improved_pass} | "
                "{baseline_metrics} | {improved_metrics} |"
            ).format(
                id=item["id"],
                question=str(item.get("question", "")).replace("|", "\\|"),
                baseline_pass=item["baseline_pass"],
                improved_pass=item["improved_pass"],
                baseline_metrics=", ".join(item.get("baseline_failed_metrics", [])) or "-",
                improved_metrics=", ".join(item.get("improved_failed_metrics", [])) or "-",
            )
        )

    return rows


def render_prompt_compare_markdown(compare_report: dict[str, Any]) -> str:
    changed_cases = compare_report.get("changed_cases", [])
    improved_cases = compare_report.get("improved_cases", [])
    regressed_cases = compare_report.get("regressed_cases", [])

    improved_rows = _case_rows(improved_cases, changed_cases)
    regressed_rows = _case_rows(regressed_cases, changed_cases)

    changed_lines = [
        (
            "- `{id}`: baseline pass={baseline_pass}, "
            "improved pass={improved_pass}, metrics "
            "`{baseline_metrics}` -> `{improved_metrics}`"
        ).format(
            id=item["id"],
            baseline_pass=item["baseline_pass"],
            improved_pass=item["improved_pass"],
            baseline_metrics=", ".join(item.get("baseline_failed_metrics", [])) or "-",
            improved_metrics=", ".join(item.get("improved_failed_metrics", [])) or "-",
        )
        for item in changed_cases
    ]

    return "\n".join(
        [
            "# DeepSeek Prompt A/B Evaluation Report",
            "",
            f"- Provider: `{compare_report.get('provider')}`",
            f"- Model: `{compare_report.get('model')}`",
            f"- Dataset: `{compare_report.get('dataset')}`",
            f"- Generated at: `{compare_report.get('generated_at')}`",
            "",
            "## Metric Comparison",
            "",
            "| Metric | Baseline | Improved | Delta |",
            "| --- | ---: | ---: | ---: |",
            "| Pass rate | {baseline} | {improved} | {delta} |".format(
                baseline=compare_report.get("baseline_pass_rate"),
                improved=compare_report.get("improved_pass_rate"),
                delta=_format_delta(
                    compare_report.get("improved_pass_rate"),
                    compare_report.get("baseline_pass_rate"),
                ),
            ),
            "| Badcase count | {baseline} | {improved} | {delta} |".format(
                baseline=compare_report.get("baseline_badcase_count"),
                improved=compare_report.get("improved_badcase_count"),
                delta=_format_delta(
                    compare_report.get("improved_badcase_count"),
                    compare_report.get("baseline_badcase_count"),
                ),
            ),
            "| Avg latency ms | {baseline} | {improved} | {delta} |".format(
                baseline=compare_report.get("baseline_avg_latency_ms"),
                improved=compare_report.get("improved_avg_latency_ms"),
                delta=_format_delta(
                    compare_report.get("improved_avg_latency_ms"),
                    compare_report.get("baseline_avg_latency_ms"),
                ),
            ),
            "",
            "## Improved Cases",
            "",
            (
                "| Case | Question | Baseline pass | Improved pass | "
                "Baseline failed metrics | Improved failed metrics |"
            ),
            "| --- | --- | --- | --- | --- | --- |",
            *(improved_rows or ["| - | - | - | - | - | - |"]),
            "",
            "## Regressed Cases",
            "",
            (
                "| Case | Question | Baseline pass | Improved pass | "
                "Baseline failed metrics | Improved failed metrics |"
            ),
            "| --- | --- | --- | --- | --- | --- |",
            *(regressed_rows or ["| - | - | - | - | - | - |"]),
            "",
            "## Changed Cases",
            "",
            *(changed_lines or ["- No changed cases."]),
            "",
            "## Metric Notes",
            "",
            "- `answer_keyword_recall` measures keyword coverage only.",
            "- `source_hit_at_k` checks whether the expected context source was retrieved.",
            (
                "- `refusal_when_answer_expected` prevents a no-context answer "
                "from passing only because it repeats expected keywords."
            ),
            "- This project does not include a full LLM-as-a-Judge pipeline yet.",
            (
                "- Future extensions can add faithfulness, answer relevancy, "
                "context precision, and context recall."
            ),
            "",
        ]
    )


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
    markdown_path = output_path.with_suffix(".md")
    markdown_path.write_text(
        render_prompt_compare_markdown(compare_report),
        encoding="utf-8",
    )
    return compare_report

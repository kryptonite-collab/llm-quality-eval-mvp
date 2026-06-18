"""Run the minimal mock agent evaluation and write reports."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any

if str(Path.cwd()) not in sys.path:
    sys.path.insert(0, str(Path.cwd()))

from app.services.agent_metrics import evaluate_agent_case
from app.services.agent_runner import (
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    AgentRunConfig,
    build_agent_runner,
)


DEFAULT_DATASET = "evals/datasets/agent_eval_sample.jsonl"
DEFAULT_JSON_REPORT = "evals/reports/agent_eval_report.json"
DEFAULT_MD_REPORT = "evals/reports/agent_eval_report.md"


def run_agent_eval(
    dataset: str = DEFAULT_DATASET,
    json_report: str = DEFAULT_JSON_REPORT,
    markdown_report: str | None = DEFAULT_MD_REPORT,
    provider: str = DEFAULT_PROVIDER,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    root = _project_root()
    dataset_path = root / dataset
    cases = _load_jsonl(dataset_path)

    runner = build_agent_runner(AgentRunConfig(provider=provider, model=model))
    results = []
    for case in cases:
        run_result = runner.run_case(case)
        metrics = evaluate_agent_case(case, run_result)
        results.append({**case, **run_result, **metrics})

    total_cases = len(results)
    passed_count = sum(1 for result in results if result["passed"])
    badcase_count = total_cases - passed_count
    report = {
        "provider": provider,
        "model": model,
        "dataset": dataset,
        "total_cases": total_cases,
        "pass_rate": passed_count / total_cases if total_cases else 0.0,
        "badcase_count": badcase_count,
        "avg_latency_ms": mean(result["latency_ms"] for result in results)
        if results
        else 0.0,
        "tool_call_accuracy_avg": mean(
            result["tool_call_accuracy"] for result in results
        )
        if results
        else 0.0,
        "source_hit_rate": mean(result["agent_source_hit"] for result in results)
        if results
        else 0.0,
        "results": results,
        "generated_at": datetime.now(UTC).isoformat(),
    }

    json_report_path = root / json_report
    json_report_path.parent.mkdir(parents=True, exist_ok=True)
    json_report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if markdown_report:
        markdown_report_path = root / markdown_report
        markdown_report_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_report_path.write_text(_to_markdown(report), encoding="utf-8")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run mock agent tool-call eval.")
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--json-report", default=DEFAULT_JSON_REPORT)
    parser.add_argument("--markdown-report", default=DEFAULT_MD_REPORT)
    parser.add_argument("--provider", default=DEFAULT_PROVIDER)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    run_agent_eval(
        dataset=args.dataset,
        json_report=args.json_report,
        markdown_report=args.markdown_report,
        provider=args.provider,
        model=args.model,
    )


def _project_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "backend").exists() and (cwd / "evals").exists():
        return cwd
    if cwd.name == "backend":
        return cwd.parent
    return cwd


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    cases = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            cases.append(json.loads(line))
    return cases


def _to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Agent Evaluation Report",
        "",
        f"- provider: {report['provider']}",
        f"- model: {report['model']}",
        f"- dataset: {report['dataset']}",
        f"- total_cases: {report['total_cases']}",
        f"- pass_rate: {report['pass_rate']:.2%}",
        f"- badcase_count: {report['badcase_count']}",
        f"- avg_latency_ms: {report['avg_latency_ms']:.2f}",
        f"- tool_call_accuracy_avg: {report['tool_call_accuracy_avg']:.2f}",
        f"- source_hit_rate: {report['source_hit_rate']:.2f}",
        "",
        "| case_id | category | passed | latency_ms | failure_reasons |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for result in report["results"]:
        reasons = ", ".join(result["failure_reasons"])
        lines.append(
            "| {case_id} | {category} | {passed} | {latency_ms} | {reasons} |".format(
                case_id=result["case_id"],
                category=result["category"],
                passed=result["passed"],
                latency_ms=result["latency_ms"],
                reasons=reasons,
            )
        )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()

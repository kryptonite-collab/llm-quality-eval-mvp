import argparse
import json
import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.services.llm_qa import LLMQAService
from app.services.metrics import evaluate_qa_result
from app.services.prompt_templates import normalize_prompt_version

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "evals/config.yaml"


def _format_report_path(path: str | Path) -> str:
    input_path = Path(path)
    if not input_path.is_absolute():
        return input_path.as_posix()

    resolved_path = input_path.resolve()
    project_root = PROJECT_ROOT.resolve()

    try:
        return resolved_path.relative_to(project_root).as_posix()
    except ValueError:
        return str(path)


def _parse_config_value(raw_value: str) -> str | bool | int | float:
    value = raw_value.strip().strip('"').strip("'")

    if value.lower() == "true":
        return True

    if value.lower() == "false":
        return False

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        return value


def load_eval_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load simple key-value evaluation config from a YAML-like file."""
    path = Path(config_path)

    config: dict[str, Any] = {
        "dataset_path": PROJECT_ROOT / "evals/datasets/rag_qa_sample.jsonl",
        "report_path": PROJECT_ROOT / "evals/reports/latest_report.json",
        "use_rag": True,
        "top_k": 3,
        "min_keyword_score": 1.0,
    }

    if not path.exists():
        return config

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            stripped_line = line.strip()

            if not stripped_line or stripped_line.startswith("#"):
                continue

            if ":" not in stripped_line:
                continue

            key, raw_value = stripped_line.split(":", 1)
            config[key.strip()] = _parse_config_value(raw_value)

    for key in ("dataset_path", "report_path"):
        value = Path(str(config[key]))
        if not value.is_absolute():
            config[key] = PROJECT_ROOT / value

    return config


def load_eval_dataset(dataset_path: str | Path) -> list[dict[str, Any]]:
    """Load evaluation samples from a JSONL dataset file."""
    path = Path(dataset_path)

    samples: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped_line = line.strip()

            if not stripped_line:
                continue

            try:
                sample = json.loads(stripped_line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {line_number}: {exc}") from exc

            samples.append(sample)

    return samples


def _extract_retrieved_sources(contexts: list[dict[str, Any]]) -> list[str]:
    sources: list[str] = []

    for context in contexts:
        source = str(context.get("source", "")).strip()

        if source and source not in sources:
            sources.append(source)

    return sources


def _infer_badcase_type(sample: dict[str, Any], eval_result: dict[str, Any]) -> str | None:
    sample_badcase_type = sample.get("badcase_type")

    if sample_badcase_type:
        return str(sample_badcase_type)

    if eval_result["pass"]:
        return None

    failed_metrics = eval_result["failed_metrics"]

    if failed_metrics == ["source_hit_at_k"]:
        return "source_miss"

    if failed_metrics == ["answer_keyword_recall"]:
        return "keyword_miss"

    if failed_metrics == ["refusal_when_answer_expected"]:
        return "refusal_when_answer_expected"

    if len(failed_metrics) > 1:
        return "multiple_metrics_failed"

    return "unknown"


def _build_badcase_type_distribution(
    badcases: list[dict[str, Any]],
) -> dict[str, int]:
    counter = Counter(str(badcase.get("badcase_type") or "unknown") for badcase in badcases)

    return dict(sorted(counter.items()))


def _build_top_failed_cases(
    badcases: list[dict[str, Any]],
    limit: int = 10,
) -> list[dict[str, Any]]:
    sorted_badcases = sorted(
        badcases,
        key=lambda item: (
            float(item.get("score", 0.0)),
            str(item.get("id") or ""),
        ),
    )

    return [
        {
            "id": item.get("id"),
            "question_id": item.get("question_id"),
            "question": item.get("question"),
            "category": item.get("category"),
            "badcase_type": item.get("badcase_type"),
            "score": item.get("score"),
            "failed_metrics": item.get("failed_metrics", []),
            "reason": item.get("reason"),
        }
        for item in sorted_badcases[:limit]
    ]


def run_eval_dataset(
    dataset_path: str | Path | None = None,
    report_path: str | Path | None = None,
    use_rag: bool | None = None,
    top_k: int | None = None,
    min_keyword_score: float | None = None,
    provider: str | None = None,
    limit: int | None = None,
    prompt_version: str | None = None,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    """Run QA evaluation dataset and write a structured report."""
    config = load_eval_config(config_path)

    actual_dataset_path = dataset_path or config["dataset_path"]
    actual_report_path = report_path or config["report_path"]
    actual_use_rag = bool(config["use_rag"] if use_rag is None else use_rag)
    actual_top_k = int(config["top_k"] if top_k is None else top_k)
    actual_min_keyword_score = float(
        config["min_keyword_score"] if min_keyword_score is None else min_keyword_score
    )

    samples = load_eval_dataset(actual_dataset_path)
    if limit is not None:
        samples = samples[:limit]

    actual_prompt_version = normalize_prompt_version(
        prompt_version or os.getenv("LLM_PROMPT_VERSION")
    )
    qa_service = LLMQAService(
        provider=provider,
        prompt_version=actual_prompt_version,
    )
    provider_config = qa_service.provider.config

    results: list[dict[str, Any]] = []
    badcases: list[dict[str, Any]] = []

    total_latency = 0.0

    for sample in samples:
        qa_result = qa_service.ask(
            question=sample["question"],
            use_rag=actual_use_rag,
            top_k=actual_top_k,
        )

        expected_keywords = sample.get("expected_keywords", [])
        expected_source = sample.get("expected_source")
        retrieved_sources = _extract_retrieved_sources(qa_result["contexts"])

        eval_result = evaluate_qa_result(
            answer=qa_result["answer"],
            contexts=qa_result["contexts"],
            expected_keywords=expected_keywords,
            expected_source=expected_source,
            latency_ms=qa_result["latency_ms"],
            min_keyword_score=actual_min_keyword_score,
            expected_behavior=sample.get("expected_behavior"),
        )
        badcase_type = _infer_badcase_type(sample, eval_result)

        total_latency += float(qa_result["latency_ms"])

        item_result = {
            "id": sample.get("id"),
            "question_id": sample.get("id"),
            "question": sample["question"],
            "category": sample.get("category"),
            "expected_behavior": sample.get("expected_behavior"),
            "badcase_type": badcase_type,
            "answer": qa_result["answer"],
            "expected_keywords": expected_keywords,
            "matched_keywords": eval_result["matched_keywords"],
            "missing_keywords": eval_result["missing_keywords"],
            "expected_source": expected_source,
            "retrieved_sources": retrieved_sources,
            "contexts": qa_result["contexts"],
            "model": qa_result["model"],
            "score": eval_result["keyword_score"],
            **eval_result,
        }

        results.append(item_result)

        if not eval_result["pass"]:
            badcases.append(
                {
                    "id": sample.get("id"),
                    "question_id": sample.get("id"),
                    "question": sample["question"],
                    "category": sample.get("category"),
                    "expected_behavior": sample.get("expected_behavior"),
                    "badcase_type": badcase_type,
                    "answer": qa_result["answer"],
                    "expected_keywords": expected_keywords,
                    "missing_keywords": eval_result["missing_keywords"],
                    "expected_source": expected_source,
                    "retrieved_sources": retrieved_sources,
                    "score": eval_result["keyword_score"],
                    "answer_keyword_recall": eval_result["answer_keyword_recall"],
                    "source_hit_at_k": eval_result["source_hit_at_k"],
                    "failed_metrics": eval_result["failed_metrics"],
                    "reason": eval_result["reason"],
                    "created_at": datetime.now(UTC).isoformat(),
                }
            )

    total = len(results)
    passed = sum(1 for item in results if item["pass"])
    failed = total - passed
    pass_rate = passed / total if total else 0.0
    avg_latency_ms = total_latency / total if total else 0.0

    source_expected_results = [item for item in results if item.get("expected_source")]
    source_hit_count = sum(1 for item in source_expected_results if item["source_hit_at_k"])
    source_hit_rate = (
        source_hit_count / len(source_expected_results) if source_expected_results else 0.0
    )

    badcase_type_distribution = _build_badcase_type_distribution(badcases)
    top_failed_cases = _build_top_failed_cases(badcases)

    report = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round(pass_rate, 4),
        "avg_latency_ms": round(avg_latency_ms, 2),
        "source_hit_rate": round(source_hit_rate, 4),
        "badcase_count": len(badcases),
        "badcase_type_distribution": badcase_type_distribution,
        "top_failed_cases": top_failed_cases,
        "badcases": badcases,
        "results": results,
        "provider": provider_config.provider,
        "model": provider_config.model,
        "generated_at": datetime.now(UTC).isoformat(),
        "config": {
            "dataset_path": _format_report_path(actual_dataset_path),
            "report_path": _format_report_path(actual_report_path),
            "use_rag": actual_use_rag,
            "top_k": actual_top_k,
            "min_keyword_score": actual_min_keyword_score,
            "provider": provider_config.provider,
            "model": provider_config.model,
            "limit": limit,
            "prompt_version": actual_prompt_version,
        },
    }

    output_path = Path(actual_report_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run an LLM QA evaluation dataset.")
    parser.add_argument("--dataset-path", default=None)
    parser.add_argument("--report-path", default=None)
    parser.add_argument("--provider", default=None, choices=["mock", "deepseek", "openai"])
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--use-rag", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--min-keyword-score", type=float, default=None)
    parser.add_argument("--prompt-version", default=None, choices=["baseline", "improved"])
    args = parser.parse_args()

    report_path = args.report_path
    if args.provider and args.provider != "mock" and report_path is None:
        report_path = PROJECT_ROOT / f"evals/reports/real_{args.provider}_report.json"

    report = run_eval_dataset(
        dataset_path=args.dataset_path,
        report_path=report_path,
        provider=args.provider,
        limit=args.limit,
        use_rag=args.use_rag,
        top_k=args.top_k,
        min_keyword_score=args.min_keyword_score,
        prompt_version=args.prompt_version,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))

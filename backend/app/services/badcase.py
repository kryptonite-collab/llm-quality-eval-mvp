import json
from pathlib import Path
from typing import Any

from app.services.llm_qa import LLMQAService
from app.services.metrics import evaluate_qa_result

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REPORT_PATH = PROJECT_ROOT / "evals/reports/latest_report.json"
DEFAULT_EXPORT_PATH = PROJECT_ROOT / "evals/badcases/badcases.jsonl"

BADCASE_EXPORT_FIELDS = (
    "id",
    "question_id",
    "question",
    "answer",
    "expected_keywords",
    "missing_keywords",
    "expected_source",
    "retrieved_sources",
    "score",
    "failed_metrics",
    "badcase_type",
    "reason",
    "created_at",
    "replay_status",
)


class BadcaseService:
    def __init__(
        self,
        report_path: str | Path | None = None,
        export_path: str | Path | None = None,
    ) -> None:
        self.report_path = Path(report_path) if report_path else DEFAULT_REPORT_PATH
        self.export_path = Path(export_path) if export_path else DEFAULT_EXPORT_PATH

    def _load_report(self) -> dict[str, Any]:
        if not self.report_path.exists():
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0.0,
                "badcases": [],
                "results": [],
            }

        return json.loads(self.report_path.read_text(encoding="utf-8"))

    def _normalize_badcase(self, badcase: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(badcase)

        normalized.setdefault("id", normalized.get("question_id"))
        normalized.setdefault("question_id", normalized.get("id"))
        normalized.setdefault("answer", None)
        normalized.setdefault("expected_keywords", [])
        normalized.setdefault("missing_keywords", [])
        normalized.setdefault("expected_source", None)
        normalized.setdefault("retrieved_sources", [])
        normalized.setdefault("score", None)
        normalized.setdefault("failed_metrics", [])
        normalized.setdefault("badcase_type", None)
        normalized.setdefault("reason", "")
        normalized.setdefault("created_at", None)
        normalized.setdefault("replay_status", "not_replayed")

        return normalized

    def list_badcases(self) -> list[dict[str, Any]]:
        report = self._load_report()
        return [self._normalize_badcase(badcase) for badcase in report.get("badcases", [])]

    def get_badcase(self, badcase_id: str) -> dict[str, Any] | None:
        for badcase in self.list_badcases():
            if str(badcase.get("id")) == str(badcase_id):
                return badcase

        return None

    def replay_badcase(
        self,
        badcase_id: str,
        use_rag: bool = True,
        top_k: int = 3,
    ) -> dict[str, Any] | None:
        badcase = self.get_badcase(badcase_id)

        if badcase is None:
            return None

        qa_service = LLMQAService()
        qa_result = qa_service.ask(
            question=badcase["question"],
            use_rag=use_rag,
            top_k=top_k,
        )
        eval_result = evaluate_qa_result(
            answer=qa_result["answer"],
            contexts=qa_result["contexts"],
            expected_keywords=badcase.get("expected_keywords", []),
            expected_source=badcase.get("expected_source"),
            latency_ms=qa_result["latency_ms"],
        )
        replay_status = {
            "replayed": True,
            "pass_after_replay": eval_result["pass"],
            "still_failed_metrics": eval_result["failed_metrics"],
        }

        return {
            "id": badcase.get("id"),
            "question": badcase["question"],
            "answer": qa_result["answer"],
            "contexts": qa_result["contexts"],
            "latency_ms": qa_result["latency_ms"],
            "model": qa_result["model"],
            "replay_status": replay_status,
            "metrics": eval_result,
            "original_badcase": badcase,
        }

    def export_badcases(
        self,
        export_path: str | Path | None = None,
    ) -> dict[str, Any]:
        output_path = Path(export_path) if export_path else self.export_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        badcases = [
            {field: self._normalize_badcase(badcase).get(field) for field in BADCASE_EXPORT_FIELDS}
            for badcase in self.list_badcases()
        ]

        with output_path.open("w", encoding="utf-8") as file:
            for badcase in badcases:
                file.write(json.dumps(badcase, ensure_ascii=False) + "\n")

        return {
            "total": len(badcases),
            "path": str(output_path),
            "items": badcases,
        }


def load_badcase_jsonl(path: str | Path) -> list[dict[str, Any]]:
    badcases: list[dict[str, Any]] = []

    with Path(path).open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped_line = line.strip()

            if not stripped_line:
                continue

            try:
                badcases.append(json.loads(stripped_line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid badcase JSONL at line {line_number}: {exc}") from exc

    return badcases

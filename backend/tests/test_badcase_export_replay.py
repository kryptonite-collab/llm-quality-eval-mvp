import csv
import json

import pytest

from app.services.badcase import BadcaseService, replay_badcase_jsonl

REQUIRED_EXPORT_FIELDS = {
    "case_id",
    "category",
    "question",
    "answer",
    "expected_keywords",
    "expected_sources",
    "keyword_recall",
    "source_hit",
    "refusal_when_answer_expected",
    "failure_reasons",
    "latency_ms",
    "provider",
    "model",
    "prompt_version",
}


def _write_report_with_failed_result(report_path):
    report = {
        "provider": "mock",
        "model": "mock-llm-local",
        "results": [
            {
                "case_id": "real-rag-x01",
                "question_id": "real-rag-x01",
                "category": "fact_qa",
                "question": "test missing keyword",
                "answer": "Mock answer for question: test missing keyword",
                "expected_keywords": ["impossible_keyword"],
                "expected_sources": ["mock_policy.md"],
                "expected_source": "mock_policy.md",
                "keyword_recall": 0.0,
                "source_hit": True,
                "source_hit_at_k": True,
                "refusal_when_answer_expected": False,
                "failure_reasons": ["answer_keyword_recall"],
                "failed_metrics": ["answer_keyword_recall"],
                "latency_ms": 1.2,
                "provider": "mock",
                "model": "mock-llm-local",
                "prompt_version": "baseline",
                "passed": False,
            }
        ],
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")


def test_badcase_export_jsonl_from_failed_results(tmp_path) -> None:
    report_path = tmp_path / "report.json"
    output_path = tmp_path / "badcases.jsonl"
    _write_report_with_failed_result(report_path)

    result = BadcaseService(report_path=report_path).export_badcases(output_path)

    assert result["total"] == 1
    exported = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(exported) == 1
    assert REQUIRED_EXPORT_FIELDS.issubset(exported[0])
    assert exported[0]["case_id"] == "real-rag-x01"
    assert exported[0]["failure_reasons"] == ["answer_keyword_recall"]


def test_badcase_export_csv_from_failed_results(tmp_path) -> None:
    report_path = tmp_path / "report.json"
    output_path = tmp_path / "badcases.csv"
    _write_report_with_failed_result(report_path)

    result = BadcaseService(report_path=report_path).export_badcases(
        output_path,
        output_format="csv",
    )

    assert result["format"] == "csv"
    rows = list(csv.DictReader(output_path.open(encoding="utf-8")))
    assert len(rows) == 1
    assert REQUIRED_EXPORT_FIELDS.issubset(rows[0])
    assert rows[0]["case_id"] == "real-rag-x01"
    assert rows[0]["provider"] == "mock"


def test_badcase_replay_jsonl_defaults_to_mock(tmp_path) -> None:
    report_path = tmp_path / "report.json"
    badcase_path = tmp_path / "badcases.jsonl"
    _write_report_with_failed_result(report_path)
    BadcaseService(report_path=report_path).export_badcases(badcase_path)

    replay_report = replay_badcase_jsonl(badcase_path)

    assert replay_report["provider"] == "mock"
    assert replay_report["model"] == "mock-llm-local"
    assert replay_report["total_cases"] == 1
    assert replay_report["results"][0]["provider"] == "mock"


def test_badcase_replay_rejects_real_provider(tmp_path) -> None:
    badcase_path = tmp_path / "badcases.jsonl"
    badcase_path.write_text(
        json.dumps(
            {
                "case_id": "real-rag-x01",
                "question": "test",
                "expected_keywords": ["test"],
                "expected_sources": ["mock_policy.md"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="mock only"):
        replay_badcase_jsonl(badcase_path, provider="deepseek")

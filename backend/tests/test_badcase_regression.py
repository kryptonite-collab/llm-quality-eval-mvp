import json

import pytest

from app.services.badcase import load_badcase_jsonl
from app.services.llm_qa import LLMQAService
from app.services.metrics import evaluate_qa_result


BADCASE_SAMPLES = [
    {
        "id": "q101",
        "question_id": "q101",
        "question": "regression keyword miss",
        "answer": "Mock answer for question: regression keyword miss",
        "expected_keywords": ["impossible_keyword"],
        "missing_keywords": ["impossible_keyword"],
        "expected_source": "mock_policy.md",
        "retrieved_sources": ["mock_policy.md"],
        "score": 0.0,
        "failed_metrics": ["answer_keyword_recall"],
        "badcase_type": "keyword_miss",
        "reason": "missing keywords: impossible_keyword",
        "created_at": "2026-05-26T00:00:00+00:00",
        "replay_status": "not_replayed",
    },
    {
        "id": "q102",
        "question_id": "q102",
        "question": "regression refusal expected",
        "answer": "Mock answer for question: regression refusal expected",
        "expected_keywords": ["cannot assist"],
        "missing_keywords": ["cannot assist"],
        "expected_source": None,
        "retrieved_sources": ["mock_policy.md"],
        "score": 0.0,
        "failed_metrics": ["answer_keyword_recall"],
        "badcase_type": "refusal_expected",
        "reason": "missing keywords: cannot assist",
        "created_at": "2026-05-26T00:00:00+00:00",
        "replay_status": "not_replayed",
    },
]


def _write_badcases_jsonl(path):
    path.write_text(
        "\n".join(
            json.dumps(sample, ensure_ascii=False)
            for sample in BADCASE_SAMPLES
        )
        + "\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize("case_index", [0, 1])
def test_badcase_jsonl_can_drive_regression_eval(tmp_path, case_index):
    badcases_path = tmp_path / "badcases.jsonl"
    _write_badcases_jsonl(badcases_path)
    badcase = load_badcase_jsonl(badcases_path)[case_index]

    qa_service = LLMQAService()
    qa_result = qa_service.ask(
        question=badcase["question"],
        use_rag=True,
        top_k=3,
    )

    eval_result = evaluate_qa_result(
        answer=qa_result["answer"],
        contexts=qa_result["contexts"],
        expected_keywords=badcase["expected_keywords"],
        expected_source=badcase["expected_source"],
        latency_ms=qa_result["latency_ms"],
    )

    assert badcase["id"]
    assert qa_result["model"] == "mock-llm-local"
    assert "pass" in eval_result
    assert "failed_metrics" in eval_result
    assert eval_result["failed_metrics"] == badcase["failed_metrics"]

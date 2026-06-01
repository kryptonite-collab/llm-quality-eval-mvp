from app.services.metrics import (
    calculate_keyword_score,
    check_source_hit,
    check_source_hit_at_k,
    evaluate_qa_result,
)


def test_calculate_keyword_score_all_match():
    result = calculate_keyword_score(
        answer="Mock answer for question: test rag mode",
        expected_keywords=["Mock answer", "test rag mode"],
    )

    assert result["keyword_score"] == 1.0
    assert result["matched_keywords"] == ["Mock answer", "test rag mode"]
    assert result["missing_keywords"] == []


def test_calculate_keyword_score_missing_keyword():
    result = calculate_keyword_score(
        answer="Mock answer for question: test rag mode",
        expected_keywords=["Mock answer", "refund"],
    )

    assert result["keyword_score"] == 0.5
    assert result["matched_keywords"] == ["Mock answer"]
    assert result["missing_keywords"] == ["refund"]


def test_check_source_hit_true():
    contexts = [
        {
            "source": "mock_policy.md",
            "content": "This is a mock RAG context.",
            "score": 1.0,
        }
    ]

    assert check_source_hit(
        contexts=contexts,
        expected_source="mock_policy.md",
    ) is True


def test_check_source_hit_false():
    contexts = [
        {
            "source": "other_file.md",
            "content": "This is another context.",
            "score": 0.8,
        }
    ]

    assert check_source_hit(
        contexts=contexts,
        expected_source="mock_policy.md",
    ) is False


def test_check_source_hit_at_k_alias():
    contexts = [
        {
            "source": "mock_policy.md",
            "content": "This is a mock RAG context.",
            "score": 1.0,
        }
    ]

    assert check_source_hit_at_k(
        contexts=contexts,
        expected_source="mock_policy.md",
    ) is True


def test_evaluate_qa_result_pass():
    result = evaluate_qa_result(
        answer="Mock answer for question: test rag mode",
        contexts=[
            {
                "source": "mock_policy.md",
                "content": "This is a mock RAG context.",
                "score": 1.0,
            }
        ],
        expected_keywords=["Mock answer", "test rag mode"],
        expected_source="mock_policy.md",
        latency_ms=10.5,
    )

    assert result["pass"] is True
    assert result["keyword_score"] == 1.0
    assert result["answer_keyword_recall"] == 1.0
    assert result["source_hit"] is True
    assert result["source_hit_at_k"] is True
    assert result["failed_metrics"] == []
    assert result["reason"] == "passed"


def test_evaluate_qa_result_fail_missing_keyword():
    result = evaluate_qa_result(
        answer="Mock answer for question: test rag mode",
        contexts=[
            {
                "source": "mock_policy.md",
                "content": "This is a mock RAG context.",
                "score": 1.0,
            }
        ],
        expected_keywords=["refund"],
        expected_source="mock_policy.md",
        latency_ms=10.5,
    )

    assert result["pass"] is False
    assert result["keyword_score"] == 0.0
    assert result["answer_keyword_recall"] == 0.0
    assert result["source_hit"] is True
    assert result["source_hit_at_k"] is True
    assert result["failed_metrics"] == ["answer_keyword_recall"]
    assert "missing keywords: refund" in result["reason"]

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_agent_eval_retrieval_question_calls_retriever():
    response = client.post(
        "/api/v1/agent/eval",
        json={
            "question": "What is the refund policy?",
            "expected_tool": "retriever",
            "expected_source": "mock_policy.md",
            "expected_keywords": ["refund", "policy"],
            "max_steps": 3,
            "timeout_ms": 2000,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert data["tool_calls"][0]["tool_name"] == "retriever"
    assert data["retrieval_trace"][0]["source"] == "mock_policy.md"
    assert data["metrics"]["pass"] is True


def test_agent_eval_plain_question_skips_retriever():
    response = client.post(
        "/api/v1/agent/eval",
        json={
            "question": "hello",
            "expected_keywords": ["Direct mock answer"],
            "max_steps": 3,
            "timeout_ms": 2000,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["tool_calls"] == []
    assert data["retrieval_trace"] == []
    assert "skip_tool" in data["reasoning_trace"]
    assert data["metrics"]["tool_called"] is False
    assert data["metrics"]["pass"] is True


def test_agent_eval_metrics_fields_exist():
    response = client.post(
        "/api/v1/agent/eval",
        json={
            "question": "Show the source document for the refund policy",
            "expected_tool": "retriever",
            "expected_source": "mock_policy.md",
            "expected_keywords": ["refund", "policy"],
        },
    )

    assert response.status_code == 200

    metrics = response.json()["metrics"]
    assert "tool_called" in metrics
    assert "tool_name_correct" in metrics
    assert "source_hit_at_k" in metrics
    assert "answer_keyword_recall" in metrics


def test_agent_eval_wrong_expected_tool_fails():
    response = client.post(
        "/api/v1/agent/eval",
        json={
            "question": "What is the refund policy?",
            "expected_tool": "calculator",
            "expected_source": "mock_policy.md",
            "expected_keywords": ["refund", "policy"],
        },
    )

    assert response.status_code == 200

    metrics = response.json()["metrics"]
    assert metrics["tool_called"] is True
    assert metrics["tool_name_correct"] is False
    assert metrics["pass"] is False


def test_agent_eval_empty_question_should_fail():
    response = client.post(
        "/api/v1/agent/eval",
        json={
            "question": "",
            "expected_tool": "retriever",
            "expected_source": "mock_policy.md",
            "expected_keywords": ["refund", "policy"],
        },
    )

    assert response.status_code == 422

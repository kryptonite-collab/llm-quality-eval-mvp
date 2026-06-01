from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_eval_ask_success_without_rag():
    response = client.post(
        "/api/v1/eval/ask",
        json={
            "question": "test question",
            "use_rag": False,
            "top_k": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert "answer" in data
    assert "contexts" in data
    assert "latency_ms" in data
    assert "model" in data

    assert data["answer"] == "Mock answer for question: test question"
    assert data["contexts"] == []
    assert isinstance(data["latency_ms"], int | float)
    assert data["model"] == "mock-llm-local"


def test_eval_ask_success_with_rag():
    response = client.post(
        "/api/v1/eval/ask",
        json={
            "question": "test rag mode",
            "use_rag": True,
            "top_k": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["answer"] == "Mock answer for question: test rag mode"
    assert len(data["contexts"]) == 1
    assert data["contexts"][0]["source"] == "mock_policy.md"
    assert data["contexts"][0]["score"] == 1.0
    assert data["model"] == "mock-llm-local"


def test_eval_ask_empty_question_should_fail():
    response = client.post(
        "/api/v1/eval/ask",
        json={
            "question": "",
            "use_rag": False,
            "top_k": 3,
        },
    )

    assert response.status_code == 422
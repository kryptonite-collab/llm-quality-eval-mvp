from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_eval_ask_qa_mode_returns_common_response_shape() -> None:
    response = client.post(
        "/api/v1/eval/ask",
        json={
            "question": "test qa mode",
            "mode": "qa",
            "use_rag": False,
            "provider": "mock",
            "prompt_version": "baseline",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Mock answer for question: test qa mode"
    assert data["contexts"] == []
    assert isinstance(data["latency_ms"], int | float)
    assert data["model"] == "mock-llm-local"
    assert data["provider"] == "mock"
    assert data["prompt_version"] == "baseline"
    assert data["mode"] == "qa"


def test_eval_ask_rag_mode_returns_chroma_contexts() -> None:
    response = client.post(
        "/api/v1/eval/ask",
        json={
            "question": "What is the refund policy?",
            "mode": "rag",
            "provider": "mock",
            "prompt_version": "baseline",
            "top_k": 2,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "rag"
    assert data["provider"] == "mock"
    assert data["prompt_version"] == "baseline"
    assert data["contexts"]
    assert data["contexts"][0]["source"] == "policy_sample.md"
    assert {"content", "source", "score", "rank"}.issubset(data["contexts"][0])


def test_eval_ask_agent_mode_returns_agent_trace() -> None:
    response = client.post(
        "/api/v1/eval/ask",
        json={
            "question": "用户询问 ORD-1001 是否还能退款, 请给出依据。",
            "mode": "agent",
            "provider": "mock",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "agent"
    assert data["provider"] == "mock"
    assert data["final_answer"] == data["answer"]
    assert [call["name"] for call in data["tool_calls"]] == [
        "lookup_order",
        "search_policy",
        "calculate_refund_window",
    ]
    assert data["retrieval_trace"]
    assert data["reasoning_trace"]


def test_eval_ask_agent_mode_ignores_real_provider_request() -> None:
    response = client.post(
        "/api/v1/eval/ask",
        json={
            "question": "用户询问 ORD-1001 是否还能退款, 请给出依据。",
            "mode": "agent",
            "provider": "deepseek",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "agent"
    assert data["provider"] == "mock"
    assert data["model"] == "mock-agent-v1"
    assert data["tool_calls"]

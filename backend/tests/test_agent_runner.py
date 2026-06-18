import pytest

from app.services.agent_runner import (
    DEFAULT_PROVIDER,
    AgentRunConfig,
    build_agent_runner,
)


def test_mock_agent_runner_records_expected_trace() -> None:
    runner = build_agent_runner()
    result = runner.run_case(
        {
            "case_id": "agent-test",
            "task": "用户询问 ORD-1001 是否还能退款, 请给出依据。",
        }
    )

    assert result["provider"] == DEFAULT_PROVIDER
    assert [call["name"] for call in result["tool_calls"]] == [
        "lookup_order",
        "search_policy",
        "calculate_refund_window",
    ]
    assert result["retrieval_trace"][0]["source"] == "evals/knowledge/policy_sample.md"
    assert "生成最终回答" in result["reasoning_trace"]
    assert "可退款" in result["final_answer"]
    assert result["latency_ms"] >= 0


def test_agent_runner_skips_real_providers_by_default() -> None:
    with pytest.raises(ValueError, match="mock only"):
        build_agent_runner(AgentRunConfig(provider="deepseek", model="deepseek-chat"))

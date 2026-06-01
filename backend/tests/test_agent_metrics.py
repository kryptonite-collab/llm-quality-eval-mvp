from app.services.agent_metrics import (
    calculate_answer_keyword_recall,
    check_reasoning_trace_valid,
    check_source_hit_at_k,
    check_timeout,
    check_tool_called,
    check_tool_name_correct,
    evaluate_agent_result,
)


def test_check_tool_called():
    assert check_tool_called([{"tool_name": "retriever"}]) is True
    assert check_tool_called([]) is False


def test_check_tool_name_correct():
    assert check_tool_name_correct([{"tool_name": "retriever"}], "retriever") is True
    assert check_tool_name_correct([{"tool_name": "retriever"}], "calculator") is False


def test_check_source_hit_at_k():
    trace = [{"source": "mock_policy.md", "content": "refund policy"}]

    assert check_source_hit_at_k(trace, "mock_policy.md") is True
    assert check_source_hit_at_k(trace, "missing.md") is False


def test_calculate_answer_keyword_recall():
    recall = calculate_answer_keyword_recall(
        final_answer="The refund policy is available.",
        expected_keywords=["refund", "policy", "pricing"],
    )

    assert recall == 0.6667


def test_check_reasoning_trace_valid():
    assert (
        check_reasoning_trace_valid(
            [
                "received_question",
                "decide_tool",
                "tool_call",
                "generate_final_answer",
            ]
        )
        is True
    )
    assert check_reasoning_trace_valid(["received_question", "tool_call"]) is False


def test_check_timeout():
    assert check_timeout(latency_ms=2001, timeout_ms=2000) is True
    assert check_timeout(latency_ms=10, timeout_ms=2000) is False


def test_evaluate_agent_result_pass():
    result = evaluate_agent_result(
        final_answer="The refund policy is available.",
        tool_calls=[{"tool_name": "retriever"}],
        retrieval_trace=[{"source": "mock_policy.md"}],
        reasoning_trace=[
            "received_question",
            "decide_tool",
            "tool_call",
            "generate_final_answer",
        ],
        expected_tool="retriever",
        expected_source="mock_policy.md",
        expected_keywords=["refund", "policy"],
        latency_ms=10,
        timeout_ms=2000,
    )

    assert result["pass"] is True


def test_evaluate_agent_result_fail():
    result = evaluate_agent_result(
        final_answer="Direct answer only.",
        tool_calls=[],
        retrieval_trace=[],
        reasoning_trace=[
            "received_question",
            "decide_tool",
            "skip_tool",
            "generate_final_answer",
        ],
        expected_tool="retriever",
        expected_source="mock_policy.md",
        expected_keywords=["refund"],
        latency_ms=10,
        timeout_ms=2000,
    )

    assert result["tool_called"] is False
    assert result["source_hit_at_k"] is False
    assert result["answer_keyword_recall"] == 0.0
    assert result["pass"] is False

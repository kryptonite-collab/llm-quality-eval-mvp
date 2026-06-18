from app.services.agent_metrics import evaluate_agent_case


def test_evaluate_agent_case_passes_when_expected_items_are_covered() -> None:
    case = {
        "case_id": "agent-test",
        "expected_tools": ["lookup_order", "search_policy"],
        "expected_keywords": ["可退款"],
        "expected_sources": ["evals/knowledge/policy_sample.md"],
        "max_latency_ms": 1000,
        "category": "refund",
    }
    run_result = {
        "tool_calls": [{"name": "lookup_order"}, {"name": "search_policy"}],
        "retrieval_trace": [{"source": "evals/knowledge/policy_sample.md"}],
        "final_answer": "该订单可退款。",
        "latency_ms": 5,
    }

    metrics = evaluate_agent_case(case, run_result)

    assert metrics["tool_call_accuracy"] == 1.0
    assert metrics["agent_source_hit"] == 1.0
    assert metrics["final_answer_keyword_recall"] == 1.0
    assert metrics["timeout"] is False
    assert metrics["passed"] is True
    assert metrics["failure_reasons"] == []


def test_evaluate_agent_case_reports_failures() -> None:
    case = {
        "case_id": "agent-test",
        "expected_tools": ["lookup_order", "search_policy"],
        "expected_keywords": ["可退款"],
        "expected_sources": ["evals/knowledge/policy_sample.md"],
        "max_latency_ms": 1,
        "category": "refund",
    }
    run_result = {
        "tool_calls": [{"name": "lookup_order"}],
        "retrieval_trace": [],
        "final_answer": "无法处理。",
        "latency_ms": 5,
    }

    metrics = evaluate_agent_case(case, run_result)

    assert metrics["passed"] is False
    assert set(metrics["failure_reasons"]) == {
        "missing_expected_tools",
        "missing_expected_sources",
        "missing_expected_keywords",
        "timeout",
    }

from app.services.agent_tools import (
    calculate_refund_window,
    lookup_order,
    search_policy,
)


def test_lookup_order_returns_mock_order() -> None:
    order = lookup_order("ORD-1001")

    assert order["status"] == "completed"
    assert order["completed_days"] == 2
    assert order["member_status"] == "standard"


def test_lookup_order_not_found() -> None:
    order = lookup_order("ORD-9999")

    assert order["status"] == "not_found"
    assert order["completed_days"] is None


def test_calculate_refund_window() -> None:
    within = calculate_refund_window(7)
    expired = calculate_refund_window(8)

    assert within["eligible"] is True
    assert within["days_remaining"] == 0
    assert expired["eligible"] is False
    assert expired["reason"] == "outside_refund_window"


def test_search_policy_returns_local_source() -> None:
    result = search_policy("refund policy")

    assert result["source"] == "evals/knowledge/policy_sample.md"
    assert result["snippets"]

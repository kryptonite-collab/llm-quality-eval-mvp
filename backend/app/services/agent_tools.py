"""Small deterministic tools used by the mock agent evaluation."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

POLICY_SOURCE = "evals/knowledge/policy_sample.md"
REFUND_WINDOW_DAYS = 7

_FALLBACK_POLICY = """# Refund and membership policy sample

- Refunds are available within 7 days after order completion.
- Orders completed more than 7 days ago are outside the refund window.
- VIP members can receive priority support, but the refund window is still 7 days
  in this local sample policy.
- Completed orders must include the order id and completion time when requesting
  a refund review.
- Cancelled or unfinished orders should be checked by customer support before a
  refund decision is made.
"""

_MOCK_ORDERS: dict[str, dict[str, Any]] = {
    "ORD-1001": {
        "order_id": "ORD-1001",
        "status": "completed",
        "completed_at": "2026-06-15",
        "completed_days": 2,
        "member_status": "standard",
        "item": "AI course subscription",
    },
    "ORD-1002": {
        "order_id": "ORD-1002",
        "status": "completed",
        "completed_at": "2026-06-07",
        "completed_days": 10,
        "member_status": "standard",
        "item": "LLM evaluation report",
    },
    "ORD-1003": {
        "order_id": "ORD-1003",
        "status": "completed",
        "completed_at": "2026-06-13",
        "completed_days": 4,
        "member_status": "vip",
        "item": "RAG knowledge base package",
    },
    "ORD-1004": {
        "order_id": "ORD-1004",
        "status": "processing",
        "completed_at": None,
        "completed_days": None,
        "member_status": "standard",
        "item": "Prompt evaluation service",
    },
    "ORD-1005": {
        "order_id": "ORD-1005",
        "status": "completed",
        "completed_at": "2026-06-10",
        "completed_days": 7,
        "member_status": "vip",
        "item": "Agent quality audit",
    },
}


def _project_root() -> Path:
    """Resolve project root from common script/test working directories."""

    cwd = Path.cwd()
    candidates = [cwd, cwd.parent]
    for candidate in candidates:
        if (candidate / "evals").exists() or (candidate / "backend").exists():
            return candidate
    return cwd


def _load_policy_text() -> str:
    policy_path = _project_root() / POLICY_SOURCE
    if not policy_path.exists():
        return _FALLBACK_POLICY
    return policy_path.read_text(encoding="utf-8")


def search_policy(query: str) -> dict[str, Any]:
    """Return local policy snippets for a query."""

    policy_text = _load_policy_text()
    query_terms = [term.lower() for term in query.replace("?", " ").split() if term]
    lines = [line.strip() for line in policy_text.splitlines() if line.strip()]

    snippets = [
        line
        for line in lines
        if not query_terms or any(term in line.lower() for term in query_terms)
    ]
    if not snippets:
        snippets = lines[:3]

    return {
        "source": POLICY_SOURCE,
        "query": query,
        "snippets": snippets[:5],
    }


def mock_retriever(query: str) -> dict[str, Any]:
    """Backward-compatible retriever tool used by the existing Agent QA route."""

    started = time.perf_counter()
    result = search_policy(query)
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    return {
        "tool_name": "retriever",
        "input": query,
        "output": {
            "contexts": [
                {
                    "source": "mock_policy.md",
                    "content": snippet,
                }
                for snippet in result["snippets"]
            ]
        },
        "latency_ms": latency_ms,
    }


def lookup_order(order_id: str) -> dict[str, Any]:
    """Look up an order from fixed mock data."""

    order = _MOCK_ORDERS.get(order_id.upper())
    if order is None:
        return {
            "order_id": order_id,
            "status": "not_found",
            "completed_at": None,
            "completed_days": None,
            "member_status": None,
            "item": None,
        }
    return dict(order)


def calculate_refund_window(completed_days: int | None) -> dict[str, Any]:
    """Apply the local 7-day refund-window rule."""

    if completed_days is None:
        return {
            "eligible": False,
            "limit_days": REFUND_WINDOW_DAYS,
            "days_remaining": None,
            "reason": "order_not_completed",
        }

    days_remaining = REFUND_WINDOW_DAYS - completed_days
    eligible = days_remaining >= 0
    return {
        "eligible": eligible,
        "limit_days": REFUND_WINDOW_DAYS,
        "days_remaining": max(days_remaining, 0),
        "reason": "within_refund_window" if eligible else "outside_refund_window",
    }

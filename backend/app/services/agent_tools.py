import time
from typing import Any


def mock_retriever(query: str) -> dict[str, Any]:
    """Return a deterministic local retrieval result for Agent evaluation."""
    start = time.perf_counter()

    contexts = [
        {
            "source": "mock_policy.md",
            "content": (
                "Mock policy document: the refund policy allows eligible refunds "
                "after support reviews the request."
            ),
            "score": 1.0,
        }
    ]

    latency_ms = (time.perf_counter() - start) * 1000

    return {
        "tool_name": "retriever",
        "input": query,
        "output": {"contexts": contexts},
        "latency_ms": round(latency_ms, 2),
    }

import time
from typing import Any


class LLMQAService:
    def ask(self, question: str, use_rag: bool = False, top_k: int = 3) -> dict[str, Any]:
        start = time.perf_counter()

        contexts: list[dict[str, Any]] = []
        if use_rag:
            contexts = [
                {
                    "source": "mock_policy.md",
                    "content": "This is a mock RAG context for local MVP testing.",
                    "score": 1.0,
                }
            ][:top_k]

        answer = f"Mock answer for question: {question}"

        latency_ms = (time.perf_counter() - start) * 1000

        return {
            "answer": answer,
            "contexts": contexts,
            "latency_ms": round(latency_ms, 2),
            "model": "mock-llm-local",
        }
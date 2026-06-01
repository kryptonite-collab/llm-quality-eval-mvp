import time
from typing import Any

from app.services.agent_metrics import evaluate_agent_result
from app.services.agent_tools import mock_retriever


RETRIEVAL_KEYWORDS = (
    "policy",
    "refund",
    "source",
    "knowledge",
    "document",
    "rag",
)


class AgentQAService:
    def run_eval(
        self,
        question: str,
        expected_tool: str | None = None,
        expected_source: str | None = None,
        expected_keywords: list[str] | None = None,
        max_steps: int = 3,
        timeout_ms: int = 2000,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        reasoning_trace = ["received_question", "decide_tool"]
        tool_calls: list[dict[str, Any]] = []
        retrieval_trace: list[dict[str, Any]] = []

        should_retrieve = self._should_call_retriever(question)

        if should_retrieve and max_steps >= 2:
            tool_call = mock_retriever(question)
            tool_calls.append(tool_call)
            retrieval_trace = tool_call["output"]["contexts"]
            reasoning_trace.append("tool_call")
        else:
            reasoning_trace.append("skip_tool")

        final_answer = self._build_final_answer(
            question=question,
            contexts=retrieval_trace,
        )
        reasoning_trace.append("generate_final_answer")

        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        metrics = evaluate_agent_result(
            final_answer=final_answer,
            tool_calls=tool_calls,
            retrieval_trace=retrieval_trace,
            reasoning_trace=reasoning_trace,
            expected_tool=expected_tool,
            expected_source=expected_source,
            expected_keywords=expected_keywords or [],
            latency_ms=latency_ms,
            timeout_ms=timeout_ms,
        )

        return {
            "final_answer": final_answer,
            "tool_calls": tool_calls,
            "retrieval_trace": retrieval_trace,
            "reasoning_trace": reasoning_trace,
            "latency_ms": latency_ms,
            "status": "success",
            "metrics": metrics,
        }

    def _should_call_retriever(self, question: str) -> bool:
        normalized_question = question.lower()
        return any(keyword in normalized_question for keyword in RETRIEVAL_KEYWORDS)

    def _build_final_answer(
        self,
        question: str,
        contexts: list[dict[str, Any]],
    ) -> str:
        if not contexts:
            return f"Direct mock answer for question: {question}"

        source = contexts[0]["source"]
        return (
            f"Based on {source}, the answer to '{question}' is: "
            "the refund policy is available in the mock policy document."
        )

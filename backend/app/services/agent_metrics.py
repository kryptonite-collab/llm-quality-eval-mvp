from typing import Any


REQUIRED_TRACE_START = ("received_question", "decide_tool")
REQUIRED_TRACE_END = "generate_final_answer"


def check_tool_called(tool_calls: list[dict[str, Any]]) -> bool:
    return bool(tool_calls)


def check_tool_name_correct(
    tool_calls: list[dict[str, Any]],
    expected_tool: str | None,
) -> bool:
    if not expected_tool:
        return True

    normalized_expected_tool = expected_tool.lower().strip()

    return any(
        str(tool_call.get("tool_name", "")).lower().strip() == normalized_expected_tool
        for tool_call in tool_calls
    )


def check_source_hit_at_k(
    retrieval_trace: list[dict[str, Any]],
    expected_source: str | None,
) -> bool:
    if not expected_source:
        return True

    normalized_expected_source = expected_source.lower().strip()

    for item in retrieval_trace:
        source = str(item.get("source", "")).lower().strip()
        if normalized_expected_source in source:
            return True

    return False


def calculate_answer_keyword_recall(
    final_answer: str,
    expected_keywords: list[str],
) -> float:
    if not expected_keywords:
        return 1.0

    normalized_answer = final_answer.lower()
    matched_count = sum(
        1
        for keyword in expected_keywords
        if keyword.lower().strip() in normalized_answer
    )

    return round(matched_count / len(expected_keywords), 4)


def check_reasoning_trace_valid(reasoning_trace: list[str]) -> bool:
    if len(reasoning_trace) < 4:
        return False

    if reasoning_trace[:2] != list(REQUIRED_TRACE_START):
        return False

    if "tool_call" not in reasoning_trace and "skip_tool" not in reasoning_trace:
        return False

    return reasoning_trace[-1] == REQUIRED_TRACE_END


def check_timeout(latency_ms: float, timeout_ms: int) -> bool:
    return latency_ms > timeout_ms


def evaluate_agent_result(
    final_answer: str,
    tool_calls: list[dict[str, Any]],
    retrieval_trace: list[dict[str, Any]],
    reasoning_trace: list[str],
    expected_tool: str | None,
    expected_source: str | None,
    expected_keywords: list[str],
    latency_ms: float,
    timeout_ms: int,
) -> dict[str, Any]:
    tool_called = check_tool_called(tool_calls)
    tool_name_correct = check_tool_name_correct(
        tool_calls=tool_calls,
        expected_tool=expected_tool,
    )
    source_hit_at_k = check_source_hit_at_k(
        retrieval_trace=retrieval_trace,
        expected_source=expected_source,
    )
    answer_keyword_recall = calculate_answer_keyword_recall(
        final_answer=final_answer,
        expected_keywords=expected_keywords,
    )
    reasoning_trace_valid = check_reasoning_trace_valid(reasoning_trace)
    timeout = check_timeout(latency_ms=latency_ms, timeout_ms=timeout_ms)

    passed = (
        tool_name_correct
        and source_hit_at_k
        and answer_keyword_recall >= 1.0
        and reasoning_trace_valid
        and not timeout
    )

    if expected_tool:
        passed = passed and tool_called

    return {
        "tool_called": tool_called,
        "tool_name_correct": tool_name_correct,
        "source_hit_at_k": source_hit_at_k,
        "answer_keyword_recall": answer_keyword_recall,
        "reasoning_trace_valid": reasoning_trace_valid,
        "timeout": timeout,
        "pass": passed,
    }

"""Metrics for the minimal agent tool-calling evaluation."""

from __future__ import annotations

from typing import Any


def evaluate_agent_case(case: dict[str, Any], run_result: dict[str, Any]) -> dict[str, Any]:
    expected_tools = case.get("expected_tools", [])
    expected_sources = case.get("expected_sources", [])
    expected_keywords = case.get("expected_keywords", [])

    actual_tools = [call["name"] for call in run_result.get("tool_calls", [])]
    actual_sources = [trace.get("source", "") for trace in run_result.get("retrieval_trace", [])]
    final_answer = run_result.get("final_answer", "")

    tool_call_accuracy = _coverage(expected_tools, actual_tools)
    agent_source_hit = _coverage(expected_sources, actual_sources)
    final_answer_keyword_recall = _keyword_recall(expected_keywords, final_answer)
    timeout = run_result.get("latency_ms", 0) > case.get("max_latency_ms", 0)

    failure_reasons: list[str] = []
    if tool_call_accuracy < 1.0:
        failure_reasons.append("missing_expected_tools")
    if agent_source_hit < 1.0:
        failure_reasons.append("missing_expected_sources")
    if final_answer_keyword_recall < 1.0:
        failure_reasons.append("missing_expected_keywords")
    if timeout:
        failure_reasons.append("timeout")

    return {
        "case_id": case.get("case_id"),
        "category": case.get("category"),
        "tool_call_accuracy": tool_call_accuracy,
        "agent_source_hit": agent_source_hit,
        "final_answer_keyword_recall": final_answer_keyword_recall,
        "timeout": timeout,
        "passed": not failure_reasons,
        "failure_reasons": failure_reasons,
    }


def evaluate_agent_result(
    final_answer: str,
    tool_calls: list[dict[str, Any]],
    retrieval_trace: list[dict[str, Any]],
    reasoning_trace: list[str],
    expected_tool: str | None = None,
    expected_source: str | None = None,
    expected_keywords: list[str] | None = None,
    latency_ms: float = 0,
    timeout_ms: int = 2000,
) -> dict[str, Any]:
    """Backward-compatible metrics for the existing Agent QA API."""

    actual_tools = [call.get("name") or call.get("tool_name") or "" for call in tool_calls]
    actual_sources = [trace.get("source", "") for trace in retrieval_trace]
    expected_keywords = expected_keywords or []

    tool_called = bool(tool_calls)
    tool_name_correct = True if expected_tool is None else expected_tool in actual_tools
    source_hit_at_k = (
        True
        if expected_source is None
        else any(expected_source in source for source in actual_sources)
    )
    answer_keyword_recall = _keyword_recall(expected_keywords, final_answer)
    reasoning_trace_valid = bool(reasoning_trace) and all(
        isinstance(step, str) and step for step in reasoning_trace
    )
    timeout = latency_ms > timeout_ms
    passed = (
        tool_name_correct
        and source_hit_at_k
        and answer_keyword_recall >= 1.0
        and reasoning_trace_valid
        and not timeout
    )

    return {
        "tool_called": tool_called,
        "tool_name_correct": tool_name_correct,
        "source_hit_at_k": source_hit_at_k,
        "answer_keyword_recall": answer_keyword_recall,
        "reasoning_trace_valid": reasoning_trace_valid,
        "timeout": timeout,
        "pass": passed,
    }


def _coverage(expected: list[str], actual: list[str]) -> float:
    if not expected:
        return 1.0
    matched = 0
    for item in expected:
        if any(item == value or item in value for value in actual):
            matched += 1
    return matched / len(expected)


def _keyword_recall(expected_keywords: list[str], final_answer: str) -> float:
    if not expected_keywords:
        return 1.0
    normalized_answer = final_answer.lower()
    matched = sum(1 for keyword in expected_keywords if keyword.lower() in normalized_answer)
    return matched / len(expected_keywords)

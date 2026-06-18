"""Deterministic mock agent runner for tool-calling evaluation."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any

from app.services.agent_tools import (
    calculate_refund_window,
    lookup_order,
    search_policy,
)

DEFAULT_PROVIDER = "mock"
DEFAULT_MODEL = "mock-agent-v1"


@dataclass
class AgentRunConfig:
    provider: str = DEFAULT_PROVIDER
    model: str = DEFAULT_MODEL


def build_agent_runner(config: AgentRunConfig | None = None) -> MockAgentRunner:
    """Build the default runner.

    Real model providers are intentionally unsupported in this minimal eval path.
    """

    config = config or AgentRunConfig()
    if config.provider != DEFAULT_PROVIDER:
        raise ValueError("Agent eval defaults to mock only; real providers are skipped.")
    return MockAgentRunner(config=config)


class MockAgentRunner:
    """A predictable agent that emits tool traces without calling any real LLM."""

    def __init__(self, config: AgentRunConfig | None = None) -> None:
        self.config = config or AgentRunConfig()

    def run_case(self, case: dict[str, Any]) -> dict[str, Any]:
        started = time.perf_counter()
        task = case["task"]

        tool_calls: list[dict[str, Any]] = []
        retrieval_trace: list[dict[str, Any]] = []
        reasoning_steps: list[str] = []

        order_id = _extract_order_id(task)
        order_result: dict[str, Any] | None = None
        refund_result: dict[str, Any] | None = None
        policy_result: dict[str, Any] | None = None

        if order_id:
            order_result = lookup_order(order_id)
            tool_calls.append(
                {
                    "name": "lookup_order",
                    "arguments": {"order_id": order_id},
                    "result": order_result,
                }
            )
            reasoning_steps.append("先查订单状态和完成时间")

        if _needs_policy(task):
            policy_result = search_policy(task)
            tool_calls.append(
                {
                    "name": "search_policy",
                    "arguments": {"query": task},
                    "result": policy_result,
                }
            )
            retrieval_trace.append(
                {
                    "tool": "search_policy",
                    "source": policy_result["source"],
                    "snippets": policy_result["snippets"],
                }
            )
            reasoning_steps.append("再检索本地政策资料")

        if _needs_refund_window(task) and order_result is not None:
            refund_result = calculate_refund_window(order_result.get("completed_days"))
            tool_calls.append(
                {
                    "name": "calculate_refund_window",
                    "arguments": {"completed_days": order_result.get("completed_days")},
                    "result": refund_result,
                }
            )
            reasoning_steps.append("根据完成天数计算退款期限")

        final_answer = _compose_final_answer(
            task=task,
            order_result=order_result,
            refund_result=refund_result,
            policy_result=policy_result,
        )
        reasoning_steps.append("生成最终回答")

        latency_ms = int((time.perf_counter() - started) * 1000)
        return {
            "case_id": case.get("case_id"),
            "provider": self.config.provider,
            "model": self.config.model,
            "tool_calls": tool_calls,
            "retrieval_trace": retrieval_trace,
            "reasoning_trace": reasoning_steps,
            "final_answer": final_answer,
            "latency_ms": latency_ms,
        }


def _extract_order_id(task: str) -> str | None:
    match = re.search(r"\bORD-\d+\b", task, flags=re.IGNORECASE)
    return match.group(0).upper() if match else None


def _needs_policy(task: str) -> bool:
    lowered = task.lower()
    keywords = ["policy", "refund", "退款", "会员", "member", "support", "期限"]
    return any(keyword in lowered for keyword in keywords)


def _needs_refund_window(task: str) -> bool:
    lowered = task.lower()
    keywords = ["refund", "退款", "期限", "window"]
    return any(keyword in lowered for keyword in keywords)


def _compose_final_answer(
    task: str,
    order_result: dict[str, Any] | None,
    refund_result: dict[str, Any] | None,
    policy_result: dict[str, Any] | None,
) -> str:
    if order_result is None:
        if policy_result is not None:
            return "已检索本地政策资料: 退款期限为订单完成后7天内, VIP会员可获得优先支持。"
        return f"已处理任务: {task}"

    status = order_result["status"]
    if status == "not_found":
        return f"订单{order_result['order_id']}未找到, 请核对订单号后再申请人工支持。"

    if status != "completed":
        return (
            f"订单{order_result['order_id']}当前状态为{status}, 尚未完成; "
            "退款判断需要先完成订单或联系人工支持。"
        )

    base = (
        f"订单{order_result['order_id']}已完成, 完成时间为{order_result['completed_at']}, "
        f"会员状态为{order_result['member_status']}。"
    )
    if refund_result is None:
        return base

    if refund_result["eligible"]:
        return (
            f"{base} 按本地政策, 退款期限为完成后7天内; 该订单仍在退款期限内, "
            f"剩余{refund_result['days_remaining']}天, 可退款。"
        )
    return f"{base} 按本地政策, 退款期限为完成后7天内; 该订单已超过退款期限, 建议转人工支持复核。"

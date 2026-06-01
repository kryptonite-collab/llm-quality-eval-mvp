from typing import Any

from pydantic import BaseModel, Field


class AgentEvalRequest(BaseModel):
    question: str = Field(..., min_length=1)
    expected_tool: str | None = None
    expected_source: str | None = None
    expected_keywords: list[str] = Field(default_factory=list)
    max_steps: int = Field(default=3, ge=1)
    timeout_ms: int = Field(default=2000, ge=1)


class AgentToolCall(BaseModel):
    tool_name: str
    input: str
    output: dict[str, Any]
    latency_ms: float


class AgentEvalMetrics(BaseModel):
    tool_called: bool
    tool_name_correct: bool
    source_hit_at_k: bool
    answer_keyword_recall: float
    reasoning_trace_valid: bool
    timeout: bool
    pass_: bool = Field(alias="pass")


class AgentEvalResponse(BaseModel):
    final_answer: str
    tool_calls: list[AgentToolCall]
    retrieval_trace: list[dict[str, Any]]
    reasoning_trace: list[str]
    latency_ms: float
    status: str
    metrics: AgentEvalMetrics

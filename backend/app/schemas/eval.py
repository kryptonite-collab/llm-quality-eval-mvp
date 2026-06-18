from typing import Any

from pydantic import BaseModel, Field


class EvalAskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    use_rag: bool = False
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    top_k: int = Field(default=3, ge=1, le=10)
    mode: str = Field(default="qa", pattern="^(qa|rag|agent)$")


class EvalAskResponse(BaseModel):
    answer: str
    contexts: list[dict[str, Any]]
    latency_ms: float
    model: str
    provider: str
    prompt_version: str
    mode: str
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    retrieval_trace: list[dict[str, Any]] = Field(default_factory=list)
    reasoning_trace: list[str] = Field(default_factory=list)
    final_answer: str | None = None

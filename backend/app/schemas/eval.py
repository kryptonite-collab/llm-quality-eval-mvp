from typing import Any

from pydantic import BaseModel, Field


class EvalAskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    use_rag: bool = False
    top_k: int = Field(default=3, ge=1, le=10)


class EvalAskResponse(BaseModel):
    answer: str
    contexts: list[dict[str, Any]]
    latency_ms: float
    model: str
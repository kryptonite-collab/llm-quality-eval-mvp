from typing import Any

from pydantic import BaseModel, Field


class BadcaseItem(BaseModel):
    id: str | None = None
    question_id: str | None = None
    question: str
    category: str | None = None
    answer: str | None = None
    expected_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    expected_source: str | None = None
    retrieved_sources: list[str] = Field(default_factory=list)
    score: float | None = None
    failed_metrics: list[str] = Field(default_factory=list)
    badcase_type: str | None = None
    reason: str
    created_at: str | None = None
    replay_status: str | dict[str, Any] | None = "not_replayed"


class BadcaseListResponse(BaseModel):
    total: int
    items: list[BadcaseItem]


class BadcaseReplayResponse(BaseModel):
    id: str | None = None
    question: str
    answer: str
    contexts: list[dict[str, Any]]
    latency_ms: float
    model: str
    replay_status: dict[str, Any]
    metrics: dict[str, Any]
    original_badcase: BadcaseItem


class BadcaseExportResponse(BaseModel):
    total: int
    path: str
    items: list[BadcaseItem]

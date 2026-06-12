import os
from pathlib import Path
from typing import Any

from app.services.llm_provider import get_llm_provider
from app.services.prompt_templates import load_prompt_template, normalize_prompt_version

PROJECT_ROOT = Path(__file__).resolve().parents[3]
POLICY_SAMPLE_PATH = PROJECT_ROOT / "evals/knowledge/policy_sample.md"


def build_mock_contexts(top_k: int) -> list[dict[str, Any]]:
    return [
        {
            "source": "mock_policy.md",
            "content": "This is a mock RAG context for local MVP testing.",
            "score": 1.0,
        }
    ][:top_k]


def build_local_policy_contexts(top_k: int) -> list[dict[str, Any]]:
    if not POLICY_SAMPLE_PATH.exists():
        return []

    return [
        {
            "source": "policy_sample.md",
            "content": POLICY_SAMPLE_PATH.read_text(encoding="utf-8"),
            "score": 1.0,
        }
    ][:top_k]


class LLMQAService:
    def __init__(
        self,
        provider: str | None = None,
        prompt_version: str | None = None,
    ) -> None:
        self.provider = get_llm_provider(provider=provider)
        self.prompt_version = normalize_prompt_version(
            prompt_version or os.getenv("LLM_PROMPT_VERSION")
        )
        self.prompt_template = load_prompt_template(self.prompt_version)

    def ask(self, question: str, use_rag: bool = False, top_k: int = 3) -> dict[str, Any]:
        contexts: list[dict[str, Any]] = []
        if use_rag:
            if self.provider.config.provider == "mock":
                contexts = build_mock_contexts(top_k=top_k)
            else:
                contexts = build_local_policy_contexts(top_k=top_k)

        result = self.provider.generate(
            question=question,
            contexts=contexts,
            prompt_template=self.prompt_template,
        )
        return {
            "answer": result["answer"],
            "contexts": contexts,
            "latency_ms": result["latency_ms"],
            "model": result["model"],
            "provider": result["provider"],
        }

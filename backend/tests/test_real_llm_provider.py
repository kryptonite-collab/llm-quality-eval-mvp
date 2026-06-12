import os

import pytest

from app.services.llm_provider import get_llm_provider

RUN_REAL_LLM_TESTS = os.getenv("RUN_REAL_LLM_TESTS", "").lower() == "true"
HAS_REAL_LLM_KEY = bool(os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"))

pytestmark = pytest.mark.skipif(
    not RUN_REAL_LLM_TESTS or not HAS_REAL_LLM_KEY,
    reason="Real LLM tests require RUN_REAL_LLM_TESTS=true and an API key.",
)


def test_real_llm_provider_can_generate_answer():
    provider_name = os.getenv("LLM_PROVIDER")
    if not provider_name:
        provider_name = "deepseek" if os.getenv("LLM_API_KEY") else "openai"
    provider = get_llm_provider(provider=provider_name)

    result = provider.generate(
        question="Answer with the single word: ok",
        contexts=[],
    )

    assert result["provider"] in {"deepseek", "openai"}
    assert result["model"]
    assert result["answer"]
    assert isinstance(result["latency_ms"], int | float)

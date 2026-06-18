import os
import time
from dataclasses import dataclass
from typing import Any, Protocol

DEFAULT_MOCK_MODEL = "mock-llm-local"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_SYSTEM_PROMPT = (
    "You are answering QA evaluation samples. "
    "Use the provided context when it is present, and answer concisely. "
    "If the context does not contain the answer, say it is not provided in the context."
)


@dataclass(frozen=True)
class LLMProviderConfig:
    provider: str
    model: str
    api_key: str | None = None
    base_url: str | None = None


class LLMProvider(Protocol):
    config: LLMProviderConfig

    def generate(
        self,
        question: str,
        contexts: list[dict[str, Any]],
        prompt_template: str | None = None,
    ) -> dict[str, Any]:
        """Generate an answer for one QA evaluation request."""


class MockLLMProvider:
    def __init__(self) -> None:
        self.config = LLMProviderConfig(
            provider="mock",
            model=DEFAULT_MOCK_MODEL,
        )

    def generate(
        self,
        question: str,
        contexts: list[dict[str, Any]],
        prompt_template: str | None = None,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        answer = f"Mock answer for question: {question}"
        latency_ms = (time.perf_counter() - start) * 1000

        return {
            "answer": answer,
            "latency_ms": round(latency_ms, 2),
            "model": self.config.model,
            "provider": self.config.provider,
        }


class OpenAICompatibleProvider:
    def __init__(self, config: LLMProviderConfig) -> None:
        self.config = config

        if not config.api_key:
            raise ValueError(f"LLM_API_KEY is required when LLM_PROVIDER={config.provider!r}")

    def generate(
        self,
        question: str,
        contexts: list[dict[str, Any]],
        prompt_template: str | None = None,
    ) -> dict[str, Any]:
        from openai import OpenAI

        start = time.perf_counter()
        client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
        )
        prompt = build_qa_prompt(question=question, contexts=contexts)
        response = client.chat.completions.create(
            model=self.config.model,
            messages=[
                {
                    "role": "system",
                    "content": prompt_template or DEFAULT_SYSTEM_PROMPT,
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        answer = response.choices[0].message.content or ""
        latency_ms = (time.perf_counter() - start) * 1000

        return {
            "answer": answer.strip(),
            "latency_ms": round(latency_ms, 2),
            "model": f"{self.config.provider}/{self.config.model}",
            "provider": self.config.provider,
        }


def build_qa_prompt(question: str, contexts: list[dict[str, Any]]) -> str:
    if not contexts:
        return f"Question:\n{question}"

    context_lines = []
    for index, context in enumerate(contexts, start=1):
        source = context.get("source", "unknown")
        content = context.get("content", "")
        context_lines.append(f"[{index}] source: {source}\ncontent: {content}")

    return (
        "Answer the question using the context below.\n\n"
        "Context:\n" + "\n\n".join(context_lines) + f"\n\nQuestion:\n{question}"
    )


def load_llm_provider_config(provider: str | None = None) -> LLMProviderConfig:
    provider_name = (provider or os.getenv("LLM_PROVIDER") or "mock").lower().strip()
    testing = os.getenv("TESTING", "").lower() == "true"
    run_real_tests = os.getenv("RUN_REAL_LLM_TESTS", "").lower() == "true"

    if testing and not run_real_tests:
        provider_name = "mock"

    if provider_name in {"", "mock", "deterministic"}:
        return LLMProviderConfig(provider="mock", model=DEFAULT_MOCK_MODEL)

    api_key = get_env_value("LLM_API_KEY")

    if provider_name == "deepseek":
        return LLMProviderConfig(
            provider="deepseek",
            model=get_env_value("LLM_MODEL") or DEFAULT_DEEPSEEK_MODEL,
            api_key=api_key,
            base_url=get_env_value("LLM_BASE_URL") or DEFAULT_DEEPSEEK_BASE_URL,
        )

    if provider_name == "openai":
        return LLMProviderConfig(
            provider="openai",
            model=get_env_value("LLM_MODEL") or DEFAULT_OPENAI_MODEL,
            api_key=api_key or get_env_value("OPENAI_API_KEY"),
            base_url=get_env_value("LLM_BASE_URL"),
        )

    raise ValueError("Unsupported LLM_PROVIDER. Expected one of: mock, deepseek, openai.")


def get_env_value(key: str) -> str | None:
    value = os.getenv(key)
    if value is None:
        return None

    value = value.strip()
    return value or None


def get_llm_provider(provider: str | None = None) -> LLMProvider:
    config = load_llm_provider_config(provider=provider)

    if config.provider == "mock":
        return MockLLMProvider()

    return OpenAICompatibleProvider(config=config)

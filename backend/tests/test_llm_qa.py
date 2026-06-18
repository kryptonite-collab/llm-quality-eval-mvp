from app.services.llm_qa import LLMQAService
from app.services.prompt_templates import load_prompt_template


class StubProvider:
    def __init__(self, provider):
        self.config = type("Config", (), {"provider": provider})()

    def generate(self, question, contexts, prompt_template=None):
        return {
            "answer": f"answer for {question}",
            "contexts": contexts,
            "latency_ms": 0.0,
            "model": "stub-model",
            "provider": self.config.provider,
        }


def test_mock_provider_uses_deterministic_mock_context():
    service = LLMQAService.__new__(LLMQAService)
    service.provider = StubProvider(provider="mock")
    service.prompt_template = load_prompt_template("baseline")

    result = service.ask(question="What is the refund policy?", use_rag=True)

    assert result["contexts"][0]["source"] == "mock_policy.md"


def test_real_provider_uses_local_policy_sample_context():
    service = LLMQAService.__new__(LLMQAService)
    service.provider = StubProvider(provider="deepseek")
    service.prompt_template = load_prompt_template("baseline")

    result = service.ask(question="What is the refund policy?", use_rag=True)

    assert result["contexts"][0]["source"] == "policy_sample.md"
    assert "7 days" in result["contexts"][0]["content"]

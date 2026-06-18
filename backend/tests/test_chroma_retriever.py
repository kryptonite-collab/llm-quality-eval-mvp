from app.services import chroma_retriever
from app.services.chroma_retriever import (
    PolicyChromaIndex,
    build_policy_chroma_index,
    query_policy_contexts,
)


def test_policy_chroma_retriever_returns_sourced_contexts() -> None:
    index = build_policy_chroma_index()
    contexts = query_policy_contexts("What is the refund policy?", top_k=2)

    assert index.chunks
    assert contexts
    assert contexts[0]["source"] == "policy_sample.md"
    assert contexts[0]["content"]
    assert isinstance(contexts[0]["score"], float)
    assert contexts[0]["rank"] == 1


def test_policy_retriever_fallback_returns_same_context_shape(monkeypatch) -> None:
    monkeypatch.setattr(
        chroma_retriever,
        "_INDEX_CACHE",
        PolicyChromaIndex(
            chunks=[
                {
                    "id": "fallback-1",
                    "content": "Refunds are available within 7 days after purchase.",
                    "source": "policy_sample.md",
                    "rank": 1,
                }
            ],
            collection=None,
            using_chroma=False,
        ),
    )

    contexts = query_policy_contexts("refunds window", top_k=1)

    assert contexts == [
        {
            "content": "Refunds are available within 7 days after purchase.",
            "source": "policy_sample.md",
            "score": 0.5,
            "rank": 1,
        }
    ]

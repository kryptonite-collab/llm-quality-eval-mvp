"""Minimal local ChromaDB retriever for the policy sample knowledge base."""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
POLICY_SAMPLE_PATH = PROJECT_ROOT / "evals/knowledge/policy_sample.md"
POLICY_SOURCE = "policy_sample.md"
VECTOR_SIZE = 64

_INDEX_CACHE: PolicyChromaIndex | None = None


@dataclass
class PolicyChromaIndex:
    chunks: list[dict[str, Any]]
    collection: Any | None = None
    using_chroma: bool = False


def build_policy_chroma_index() -> PolicyChromaIndex:
    """Build a tiny local index from `evals/knowledge/policy_sample.md`."""

    global _INDEX_CACHE

    if _INDEX_CACHE is not None:
        return _INDEX_CACHE

    chunks = _build_policy_chunks()
    try:
        import chromadb
        from chromadb.config import Settings

        client = chromadb.Client(
            Settings(
                anonymized_telemetry=False,
                is_persistent=False,
            )
        )
        collection = client.get_or_create_collection("policy_sample")
        collection.add(
            ids=[chunk["id"] for chunk in chunks],
            documents=[chunk["content"] for chunk in chunks],
            metadatas=[{"source": chunk["source"], "rank": chunk["rank"]} for chunk in chunks],
            embeddings=[_embed_text(chunk["content"]) for chunk in chunks],
        )
        _INDEX_CACHE = PolicyChromaIndex(
            chunks=chunks,
            collection=collection,
            using_chroma=True,
        )
    except Exception:
        _INDEX_CACHE = PolicyChromaIndex(chunks=chunks, collection=None, using_chroma=False)

    return _INDEX_CACHE


def query_policy_contexts(question: str, top_k: int) -> list[dict[str, Any]]:
    """Query local policy contexts and return content/source/score/rank."""

    index = build_policy_chroma_index()
    actual_top_k = max(1, top_k)

    if index.using_chroma and index.collection is not None:
        try:
            result = index.collection.query(
                query_embeddings=[_embed_text(question)],
                n_results=min(actual_top_k, len(index.chunks)),
            )
            return _format_chroma_results(result)
        except Exception:
            pass

    return _fallback_query(question=question, chunks=index.chunks, top_k=actual_top_k)


def _build_policy_chunks() -> list[dict[str, Any]]:
    if not POLICY_SAMPLE_PATH.exists():
        return [
            {
                "id": "policy-sample-fallback",
                "content": "Refunds are available within 7 days after purchase.",
                "source": POLICY_SOURCE,
                "rank": 1,
            }
        ]

    text = POLICY_SAMPLE_PATH.read_text(encoding="utf-8")
    sections = re.split(r"\n(?=## )", text)
    chunks: list[dict[str, Any]] = []

    for index, section in enumerate(sections, start=1):
        content = section.strip()
        if not content or content.startswith("# Policy Sample Knowledge Base"):
            continue
        heading = content.splitlines()[0].replace("#", "").strip()
        chunks.append(
            {
                "id": f"policy-sample-{index}",
                "content": content,
                "source": POLICY_SOURCE,
                "rank": len(chunks) + 1,
                "heading": heading,
            }
        )

    return chunks


def _embed_text(text: str) -> list[float]:
    vector = [0.0] * VECTOR_SIZE
    tokens = _tokenize(text)

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % VECTOR_SIZE
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        vector[index] += sign

    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def _fallback_query(
    question: str,
    chunks: list[dict[str, Any]],
    top_k: int,
) -> list[dict[str, Any]]:
    query_terms = set(_tokenize(question))
    scored = []

    for chunk in chunks:
        chunk_terms = set(_tokenize(chunk["content"]))
        overlap = len(query_terms & chunk_terms)
        score = overlap / max(len(query_terms), 1)
        scored.append((score, chunk))

    scored.sort(key=lambda item: (-item[0], item[1]["rank"]))
    return [
        {
            "content": chunk["content"],
            "source": chunk["source"],
            "score": round(float(score), 4),
            "rank": rank,
        }
        for rank, (score, chunk) in enumerate(scored[:top_k], start=1)
    ]


def _format_chroma_results(result: dict[str, Any]) -> list[dict[str, Any]]:
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    contexts = []

    for rank, document in enumerate(documents, start=1):
        metadata = metadatas[rank - 1] if rank - 1 < len(metadatas) else {}
        distance = distances[rank - 1] if rank - 1 < len(distances) else 0.0
        contexts.append(
            {
                "content": document,
                "source": metadata.get("source", POLICY_SOURCE),
                "score": round(1.0 / (1.0 + float(distance)), 4),
                "rank": rank,
            }
        )

    return contexts


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())

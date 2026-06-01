from typing import Any


def _normalize_text(value: str) -> str:
    return value.lower().strip()


def calculate_keyword_score(
    answer: str,
    expected_keywords: list[str],
) -> dict[str, Any]:
    """Calculate keyword match score for an LLM answer."""
    if not expected_keywords:
        return {
            "keyword_score": 1.0,
            "matched_keywords": [],
            "missing_keywords": [],
        }

    normalized_answer = _normalize_text(answer)

    matched_keywords: list[str] = []
    missing_keywords: list[str] = []

    for keyword in expected_keywords:
        normalized_keyword = _normalize_text(keyword)

        if normalized_keyword in normalized_answer:
            matched_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)

    keyword_score = len(matched_keywords) / len(expected_keywords)

    return {
        "keyword_score": round(keyword_score, 4),
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
    }


def check_source_hit(
    contexts: list[dict[str, Any]],
    expected_source: str | None,
) -> bool:
    """Check whether retrieved contexts contain the expected source."""
    if not expected_source:
        return True

    normalized_expected_source = _normalize_text(expected_source)

    for context in contexts:
        source = str(context.get("source", ""))
        normalized_source = _normalize_text(source)

        if normalized_expected_source in normalized_source:
            return True

    return False


def check_source_hit_at_k(
    contexts: list[dict[str, Any]],
    expected_source: str | None,
) -> bool:
    """Check source hit using the retrieved top-k contexts."""
    return check_source_hit(
        contexts=contexts,
        expected_source=expected_source,
    )


def _collect_failed_metrics(
    keyword_score: float,
    source_hit_at_k: bool,
    min_keyword_score: float,
) -> list[str]:
    failed_metrics: list[str] = []

    if keyword_score < min_keyword_score:
        failed_metrics.append("answer_keyword_recall")

    if not source_hit_at_k:
        failed_metrics.append("source_hit_at_k")

    return failed_metrics


def evaluate_qa_result(
    answer: str,
    contexts: list[dict[str, Any]],
    expected_keywords: list[str],
    expected_source: str | None,
    latency_ms: float | None = None,
    min_keyword_score: float = 1.0,
) -> dict[str, Any]:
    """Evaluate a single QA result using keyword and source rules."""
    keyword_result = calculate_keyword_score(
        answer=answer,
        expected_keywords=expected_keywords,
    )

    source_hit = check_source_hit(
        contexts=contexts,
        expected_source=expected_source,
    )
    source_hit_at_k = check_source_hit_at_k(
        contexts=contexts,
        expected_source=expected_source,
    )

    passed = (
        keyword_result["keyword_score"] >= min_keyword_score
        and source_hit_at_k
    )
    failed_metrics = _collect_failed_metrics(
        keyword_score=keyword_result["keyword_score"],
        source_hit_at_k=source_hit_at_k,
        min_keyword_score=min_keyword_score,
    )

    reasons: list[str] = []

    if keyword_result["missing_keywords"]:
        reasons.append(
            "missing keywords: "
            + ", ".join(keyword_result["missing_keywords"])
        )

    if not source_hit:
        reasons.append(f"expected source not hit: {expected_source}")

    if not reasons:
        reasons.append("passed")

    return {
        "pass": passed,
        "keyword_score": keyword_result["keyword_score"],
        "answer_keyword_recall": keyword_result["keyword_score"],
        "matched_keywords": keyword_result["matched_keywords"],
        "missing_keywords": keyword_result["missing_keywords"],
        "source_hit": source_hit,
        "source_hit_at_k": source_hit_at_k,
        "latency_ms": latency_ms,
        "failed_metrics": failed_metrics,
        "reason": "; ".join(reasons),
    }

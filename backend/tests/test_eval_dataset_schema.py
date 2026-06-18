import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REAL_RAG_DATASET = PROJECT_ROOT / "evals/datasets/real_rag_sample.jsonl"
ALLOWED_EXPECTED_BEHAVIORS = {"answer", "refuse"}
REQUIRED_REAL_RAG_FIELDS = {
    "case_id",
    "category",
    "question",
    "expected_keywords",
    "expected_sources",
    "should_answer",
    "expected_refusal",
    "notes",
}
EXPECTED_CATEGORIES = {
    "fact_qa",
    "source_hit",
    "multi_doc",
    "no_answer",
    "irrelevant_answer",
    "abnormal_input",
    "keyword_distractor",
    "refusal_error",
}


def _load_jsonl(path: Path) -> list[dict]:
    samples = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped_line = line.strip()
            if not stripped_line:
                continue

            try:
                samples.append(json.loads(stripped_line))
            except json.JSONDecodeError as exc:
                raise AssertionError(f"Invalid JSONL at line {line_number}: {exc}") from exc

    return samples


def _get_case_id(sample: dict) -> str | None:
    return sample.get("case_id") or sample.get("id")


def _get_expected_sources(sample: dict) -> list[str]:
    if "expected_sources" in sample:
        return sample["expected_sources"]

    expected_source = sample.get("expected_source")
    return [expected_source] if expected_source else []


def test_real_rag_dataset_jsonl_is_parseable():
    samples = _load_jsonl(REAL_RAG_DATASET)

    assert samples


def test_real_rag_dataset_has_required_fields_and_valid_values():
    samples = _load_jsonl(REAL_RAG_DATASET)

    for sample in samples:
        assert REQUIRED_REAL_RAG_FIELDS.issubset(sample)

        case_id = _get_case_id(sample)
        expected_sources = _get_expected_sources(sample)

        assert case_id
        assert isinstance(sample.get("question"), str)
        assert sample["question"].strip()
        assert isinstance(sample.get("expected_keywords"), list)
        assert sample["expected_keywords"]
        assert isinstance(expected_sources, list)
        assert expected_sources
        assert all(isinstance(source, str) and source for source in expected_sources)
        assert sample["category"] in EXPECTED_CATEGORIES
        assert isinstance(sample.get("should_answer"), bool)
        assert isinstance(sample.get("expected_refusal"), bool)
        assert sample["should_answer"] is not sample["expected_refusal"]
        assert isinstance(sample.get("notes"), str)
        assert sample["notes"].strip()

        expected_behavior = sample.get("expected_behavior")
        if expected_behavior is not None:
            assert expected_behavior in ALLOWED_EXPECTED_BEHAVIORS


def test_real_rag_dataset_case_ids_are_unique():
    samples = _load_jsonl(REAL_RAG_DATASET)
    case_ids = [_get_case_id(sample) for sample in samples]

    assert len(case_ids) == len(set(case_ids))


def test_real_rag_dataset_questions_are_unique():
    samples = _load_jsonl(REAL_RAG_DATASET)
    questions = [sample["question"].strip().lower() for sample in samples]

    assert len(questions) == len(set(questions))


def test_real_rag_dataset_has_50_samples():
    samples = _load_jsonl(REAL_RAG_DATASET)

    assert len(samples) == 50


def test_real_rag_dataset_no_answer_cases_are_refuse_behavior():
    samples = _load_jsonl(REAL_RAG_DATASET)

    for sample in samples:
        if sample["category"] == "no_answer":
            assert sample["should_answer"] is False
            assert sample["expected_refusal"] is True
            assert "context has no" in sample["notes"].lower()


def test_real_rag_dataset_covers_expected_categories():
    samples = _load_jsonl(REAL_RAG_DATASET)
    categories = {sample["category"] for sample in samples}

    assert categories == EXPECTED_CATEGORIES

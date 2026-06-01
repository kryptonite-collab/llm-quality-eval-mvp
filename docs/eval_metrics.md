# Evaluation Metrics

This MVP uses deterministic rule-based metrics. The goal is to build a stable evaluation pipeline before adding semantic or model-judge scoring.

## keyword_score

`keyword_score` measures how many expected keywords appear in the answer.

```text
keyword_score = matched_keywords / expected_keywords
```

If no expected keywords are provided, the score is `1.0`.

Implemented in:

```text
app/services/metrics.py
```

## answer_keyword_recall

`answer_keyword_recall` is currently compatible with `keyword_score`.

It exists as a clearer metric name for report consumers:

- `keyword_score`: legacy/simple score name
- `answer_keyword_recall`: quality metric name

Current meaning:

```text
answer_keyword_recall = keyword_score
```

## source_hit_at_k

`source_hit_at_k` checks whether retrieved contexts include the expected source.

Current rule:

```text
expected_source is contained in any context["source"]
```

If `expected_source` is empty, the source check passes.

The older field `source_hit` is still kept for compatibility.

## source_hit_rate

`source_hit_rate` is a report-level metric.

Current rule:

```text
source_hit_rate =
  number of source-expected samples with source_hit_at_k=true
  / number of samples with expected_source
```

In the current sample report it is `1.0`, because the mock retriever always returns `mock_policy.md` for RAG mode. This does not represent real production RAG quality.

## latency_ms

`latency_ms` records mock QA service latency.

Because the current service is deterministic and local, the value is usually very small. It is useful for preserving the report contract, not for real performance analysis yet.

## pass_rate

`pass_rate` is a report-level metric:

```text
pass_rate = passed / total
```

Current sample report:

```text
total = 50
passed = 33
failed = 17
pass_rate = 0.66
```

## badcase_type_distribution

`badcase_type_distribution` groups failed samples by badcase type.

Current report distribution:

```json
{
  "invalid_input": 3,
  "irrelevant_answer": 4,
  "keyword_miss": 5,
  "refusal_expected": 5
}
```

Badcase type can come from the sample field `badcase_type`, or be inferred by the runner from failed metrics.

## failed_metrics

`failed_metrics` lists the metrics that caused the sample to fail.

Examples:

```json
["answer_keyword_recall"]
```

```json
["source_hit_at_k"]
```

This field is important for debugging because it tells the tester why a sample became a badcase.

## top_failed_cases

`top_failed_cases` contains a small subset of low-scoring failed cases.

Current sorting rule:

```text
score ascending, then id ascending
```

This gives a quick triage view in the report.

## Strengths of Current Rule Metrics

- Deterministic and reproducible
- No external model dependency
- Easy to debug
- Fast enough for local tests
- Useful for testing report structure and badcase flow
- Good fit for CI once environment setup is stable

## Limitations of Current Rule Metrics

- Keyword matching is not semantic.
- Correct paraphrases can fail.
- Answers can contain keywords but still be wrong.
- Source hit checks only filenames, not whether the answer is grounded.
- Refusal quality is represented by expected keywords, not a true safety classifier.
- Latency is mock latency, not production latency.

## Future Metric Extensions

These are planned extensions, not current implemented capabilities:

- Context precision
- Context recall
- Faithfulness
- Answer relevancy
- Citation correctness
- Refusal correctness
- LLM-as-judge scoring
- Prompt version comparison
- Evaluation result diffing across runs

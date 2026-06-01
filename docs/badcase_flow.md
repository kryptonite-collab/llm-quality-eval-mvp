# Badcase Flow

Badcase handling turns failed evaluation samples into regression assets.

## Badcase Source

Badcases come from:

```text
evals/reports/latest_report.json
```

The eval runner writes this report after processing:

```text
evals/datasets/rag_qa_sample.jsonl
```

Any result with `pass=false` is added to the report's `badcases` list.

## Badcase Fields

Exported badcases contain:

| Field | Meaning |
| --- | --- |
| `id` | Badcase id |
| `question_id` | Original question/sample id |
| `question` | Original input question |
| `answer` | Actual answer from the mock QA service |
| `expected_keywords` | Expected answer keywords |
| `missing_keywords` | Keywords missing from the answer |
| `expected_source` | Expected retrieved source |
| `retrieved_sources` | Actual retrieved source list |
| `score` | Keyword score |
| `failed_metrics` | Metrics that failed |
| `badcase_type` | Failure category |
| `reason` | Human-readable failure reason |
| `created_at` | Report generation timestamp |
| `replay_status` | Export-time replay state |

## List Badcases

Endpoint:

```http
GET /api/v1/badcases
```

Call chain:

```text
badcases.py route
  -> BadcaseService.list_badcases()
  -> latest_report.json
  -> BadcaseListResponse
```

## Get Badcase Detail

Endpoint:

```http
GET /api/v1/badcases/{badcase_id}
```

The service searches the report-backed badcase list by `id`.

If the id does not exist, the API returns 404.

## Replay Badcase

Endpoint:

```http
POST /api/v1/badcases/{badcase_id}/replay
```

Replay flow:

```text
load badcase
  -> LLMQAService.ask(question)
  -> evaluate_qa_result()
  -> replay_status
```

Replay response includes:

```json
{
  "replayed": true,
  "pass_after_replay": false,
  "still_failed_metrics": ["answer_keyword_recall"]
}
```

This answers the question: "Does this badcase still fail with the current implementation?"

## Export to badcases.jsonl

Endpoint:

```http
POST /api/v1/badcases/export
```

Output file:

```text
evals/badcases/badcases.jsonl
```

Each line is one badcase JSON object. The current exported file contains 17 badcases from the latest sample report.

## Pytest Parameterized Regression

Implemented in:

```text
tests/test_badcase_regression.py
```

Regression flow:

```text
construct temporary badcases.jsonl
  -> load_badcase_jsonl()
  -> pytest.mark.parametrize()
  -> LLMQAService.ask()
  -> evaluate_qa_result()
  -> assert failed metrics are reproducible
```

The test uses `tmp_path` so it does not depend on absolute paths.

## Why This Matches Testing Development

This flow maps directly to testing work:

1. Run evaluation.
2. Detect failed cases.
3. Classify failures.
4. Replay failures.
5. Export failures as regression data.
6. Add parameterized tests to prevent repeated quality regressions.

The value is not only in detecting bad answers, but in converting them into repeatable tests.

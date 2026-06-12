# Dataset Design

## Why `real_rag_sample.jsonl` Exists

`evals/datasets/real_rag_sample.jsonl` is a small, explainable RAG evaluation set for interview and portfolio demos.

The goal is not to claim production-grade retrieval. The goal is to show a realistic quality loop:

```text
local policy knowledge
  -> real model answer
  -> rule-based scoring
  -> report
  -> badcase analysis
  -> prompt comparison
```

The dataset uses `evals/knowledge/policy_sample.md` as the only knowledge source, so the expected answers are easy to inspect and reproduce.

## Current Coverage

The current dataset has 10 samples:

- 6 normal fact QA cases
- 2 source-hit cases
- 2 unknown-knowledge refusal cases

The fact QA cases check whether the model can answer questions about refund rules, support review timelines, billing contact paths, cancellation rules, and eligibility windows.

The source-hit cases check whether the retrieved context source is present and usable for answer grounding.

The unknown-knowledge cases check whether the model refuses when the answer is not in `policy_sample.md`.

## What Each Sample Tests

Each JSONL row includes:

- `id`: stable sample id
- `question`: user-facing question
- `expected_keywords`: required terms for lightweight keyword recall
- `expected_source`: expected context source, currently `policy_sample.md`
- `category`: scenario grouping, such as `facts_qa`, `source_hit`, or `unknown_knowledge`
- `expected_behavior`: `answer` or `refuse`

`expected_behavior=answer` means a direct answer is expected. If the model says the context has no information, the `refusal_when_answer_expected` metric fails the case even when keywords are repeated.

`expected_behavior=refuse` means the knowledge base does not contain the answer, so a grounded refusal is expected.

## How To Add Samples

Add one JSON object per line to `evals/datasets/real_rag_sample.jsonl`.

Use this shape:

```json
{"id":"real-rag-011","question":"...","expected_keywords":["..."],"expected_source":"policy_sample.md","category":"facts_qa","expected_behavior":"answer"}
```

Keep each question focused on one business rule. Add only keywords that are necessary for judging the answer.

## Avoiding Duplicate Samples

Before adding a sample, check whether an existing question already tests the same rule and behavior.

Prefer new samples that vary one dimension:

- a different business rule
- a different wording of the same user intent
- a different failure mode
- a different expected behavior

Do not add several rows that only rephrase the same question with the same keywords and category.

## Current Limitations

This dataset is intentionally small. It is useful for explaining the evaluation loop, but it is not enough to measure production quality.

Current limitations:

- The knowledge base is one local Markdown file.
- Retrieval is a simple local context injection, not vector search.
- Metrics are rule-based, not semantic judges.
- Keyword recall does not fully prove correctness or faithfulness.
- There is no full LLM-as-a-Judge pipeline yet.

## Scaling To 50 Or 100 RAG Samples

To expand the dataset, group cases by scenario:

- factual policy lookup
- source grounding
- missing knowledge refusal
- ambiguous user questions
- multi-rule questions
- edge cases around time windows and eligibility
- prompt-injection style requests
- citation/source wording checks

For each group, keep stable ids and review expected keywords carefully. After 50 or 100 samples, add summary reporting by category so prompt and RAG changes can be compared without manually reading every answer.

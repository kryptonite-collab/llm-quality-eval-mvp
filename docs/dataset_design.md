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

## Why Expand To 50 Samples

The first small sample set proved that the RAG path works. For interview use, a tiny dataset is easy to question because it only demonstrates a happy-path mini demo.

The expanded dataset has 50 samples so it can show testing design, not just API connectivity. The cases cover grounded fact QA, source hits, multi-section questions, no-answer behavior, irrelevant questions, abnormal inputs, keyword distractors, and wrong-refusal risk.

This is still small enough for manual DeepSeek evaluation, but large enough to discuss test coverage.

## Current Coverage

The current dataset has 50 samples:

- `fact_qa`: direct policy questions grounded in `policy_sample.md`
- `source_hit`: checks that the answer can be grounded to `policy_sample.md`
- `multi_doc`: questions that combine multiple policy sections
- `no_answer`: questions where the policy context has no answer
- `irrelevant_answer`: unrelated user requests that should not be answered from policy context
- `abnormal_input`: punctuation, repetition, mixed language, or malformed input
- `keyword_distractor`: questions that contain misleading numbers or nearby policy terms
- `refusal_error`: answerable questions where a refusal would be a regression

The fact QA cases check whether the model can answer questions about refund rules, support review timelines, billing contact paths, cancellation rules, eligibility windows, invoice correction, refund method limits, escalation, and usage-based services.

The source-hit cases check whether the retrieved context source is present and usable for answer grounding.

The no-answer and irrelevant-answer cases check whether the model refuses when the answer is not in `policy_sample.md`. Each no-answer row explicitly records in `notes` that the context has no answer.

The multi-condition cases check whether the model can combine multiple rules in one answer, such as collecting order id, invoice id, account email, and escalation urgency.

The keyword-distractor cases check whether the model can distinguish refund method limits, billing support, general support, cancellation, invoice correction, and misleading numbers such as 30 days versus the actual 7 day refund window.

The refusal-error cases check whether the model answers when the context does contain the answer.

The boundary-condition cases check exact values such as 7 days, 14 days, 2 business days, and processing-start limits.

## What Each Sample Tests

Each JSONL row includes:

- `case_id`: stable sample id
- `category`: scenario grouping
- `question`: user-facing question
- `expected_keywords`: required terms for lightweight keyword recall
- `expected_sources`: expected context sources, currently `policy_sample.md`
- `should_answer`: whether the context contains enough information to answer
- `expected_refusal`: whether a grounded refusal is expected
- `notes`: short human explanation of the case design

`should_answer=true` means a direct answer is expected. If the model says the context has no information, the `refusal_when_answer_expected` metric fails the case even when keywords are repeated.

`expected_refusal=true` means the knowledge base does not contain the answer, so a grounded refusal is expected.

## Why No-Answer Samples Matter

No-answer samples prevent a model from inventing policy details that are not in the context. In production RAG systems, a safe "not provided in the context" answer is often better than a confident but unsupported answer.

## Why Hallucination-Pressure Samples Matter

Hallucination-pressure samples ask the model to invent a rule, such as a VIP refund exception or an enterprise cancellation right. These samples test whether the prompt and evaluation metrics discourage unsupported claims.

## Why Multi-Condition Samples Matter

Many support and billing questions require more than one condition. For example, escalation requires both a delayed review and an order id plus an urgency reason. Multi-condition samples check whether the answer covers all required parts instead of matching only one keyword.

## How To Add Samples

Add one JSON object per line to `evals/datasets/real_rag_sample.jsonl`.

Use this shape:

```json
{"case_id":"real-rag-051","category":"fact_qa","question":"...","expected_keywords":["..."],"expected_sources":["policy_sample.md"],"should_answer":true,"expected_refusal":false,"notes":"Grounded in Refund Policy."}
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

## Scaling Beyond 50 RAG Samples

To expand the dataset, group cases by scenario:

- factual policy lookup
- source grounding
- missing knowledge refusal
- hallucination pressure
- similar-rule interference
- wrong refusal
- boundary conditions
- ambiguous user questions
- multi-rule questions
- edge cases around time windows and eligibility
- prompt-injection style requests
- citation/source wording checks

For each group, keep stable ids and review expected keywords carefully. After 50 or 100 samples, add summary reporting by category so prompt and RAG changes can be compared without manually reading every answer.

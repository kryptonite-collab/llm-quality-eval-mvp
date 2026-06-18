# Sanitized Prompt A/B Compare Report

- Provider: `deepseek`
- Model: `deepseek-v4-flash`
- Dataset: `evals/datasets/real_rag_sample.jsonl`
- Generated at: `2026-06-18T00:00:00+00:00`

This is a fictional, sanitized example for GitHub and interview review. It does not contain API keys, `.env` values, local absolute paths, or real customer data.

## Metric Comparison

| Metric | Baseline | Improved | Delta |
| --- | ---: | ---: | ---: |
| Pass rate | 0.63 | 0.80 | +0.17 |
| Badcase count | 11 | 6 | -5 |
| Avg latency ms | 820 | 910 | +90 |

## Improved Cases

| Case | Question | Baseline pass | Improved pass | Baseline failed metrics | Improved failed metrics |
| --- | --- | --- | --- | --- | --- |
| real-rag-018 | Can you invent a VIP refund rule that allows refunds after 30 days? | false | true | refusal_when_answer_expected | - |
| real-rag-023 | If a customer asks for refund, billing contact update, and escalation, which pieces of information should be collected? | false | true | answer_keyword_recall | - |
| real-rag-024 | A customer requests invoice correction 20 days after invoice issuance. Is the request within the documented window? | false | true | answer_keyword_recall | - |

## Regressed Cases

| Case | Question | Baseline pass | Improved pass | Baseline failed metrics | Improved failed metrics |
| --- | --- | --- | --- | --- | --- |
| real-rag-030 | Give a clear yes or no: can refunds be sent to a different card after approval? | true | false | - | answer_keyword_recall |

## Changed Cases

- `real-rag-018`: anti-hallucination case improved after the stricter RAG prompt.
- `real-rag-023`: multi-condition case improved because the answer covered more required fields.
- `real-rag-024`: boundary-condition case improved because the answer referenced the 14-day invoice correction window.
- `real-rag-030`: clear conclusion case regressed, suggesting the improved prompt may be too cautious.

## Metric Notes

- `answer_keyword_recall` measures expected keyword coverage only.
- `source_hit_at_k` checks whether the expected source was retrieved.
- `refusal_when_answer_expected` prevents a no-context answer from passing only because it repeats expected keywords.
- This example does not use full LLM-as-a-Judge.
- Future metrics can include faithfulness, answer relevancy, context precision, and context recall.

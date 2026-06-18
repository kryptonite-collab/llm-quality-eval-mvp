# Report Example Guide

This page explains how to read the evaluation reports without running a real model.

The examples below use sanitized, fictional values. They do not contain API keys, `.env` content, or local machine paths.

## What A Compare Report Is

A compare report summarizes a Prompt A/B evaluation run.

The project runs the same dataset twice:

```text
baseline prompt + same dataset -> baseline report
improved RAG prompt + same dataset -> improved report
baseline report + improved report -> compare report
```

The compare report answers one practical question:

```text
Did the prompt/RAG configuration change improve measurable quality?
```

The JSON report is useful for automation. The Markdown report is useful for GitHub review, interview discussion, and quick human reading.

## How To Read `pass_rate`

`pass_rate` is the percentage of cases that passed the current rule-based checks.

Example:

| Version | Pass rate |
| --- | ---: |
| baseline | 0.63 |
| improved | 0.80 |

This means the improved prompt passed more evaluation cases on the same dataset.

Important limitation: `pass_rate` is only as good as the dataset and metrics. A higher pass rate does not prove the model is perfect. It means the model performed better against the current evaluation rules.

## How To Read `badcase_count`

`badcase_count` is the number of failed cases.

Example:

| Version | Badcase count |
| --- | ---: |
| baseline | 11 |
| improved | 6 |

This means fewer cases failed after the prompt change. For testing work, this is useful because failed cases can be converted into regression assets.

## How To Read `improved_cases` And `regressed_cases`

`improved_cases` are cases that failed in baseline but passed in improved.

`regressed_cases` are cases that passed in baseline but failed in improved.

The goal is not only to improve the overall pass rate. A prompt can improve some cases while breaking others, so regression tracking matters.

Example:

| Field | Meaning |
| --- | --- |
| `improved_cases=["real-rag-018"]` | The improved prompt fixed a hallucination-pressure case. |
| `regressed_cases=["real-rag-030"]` | The improved prompt made a clear yes/no case worse. |

## How To Read `avg_latency_ms`

`avg_latency_ms` is average response latency across evaluated cases.

Example:

| Version | Avg latency ms |
| --- | ---: |
| baseline | 820 |
| improved | 910 |

If quality improves but latency also increases, this tradeoff should be discussed. In an MVP, latency mainly helps preserve a report contract. In production, it can become a release gate.

## Metric Meanings And Limits

| Metric | Meaning | Limitation |
| --- | --- | --- |
| `answer_keyword_recall` | Checks whether expected keywords appear in the answer. | It is not semantic. A wrong answer can still repeat keywords. |
| `source_hit_at_k` | Checks whether the expected source appears in retrieved contexts. | It checks source presence, not full grounding or faithfulness. |
| `refusal_when_answer_expected` | Fails cases where an answer is expected but the model says the context has no answer. | It only catches explicit no-context phrases, not every bad refusal. |

This project does not include a full LLM-as-a-Judge pipeline yet. Future metrics can include faithfulness, answer relevancy, context precision, and context recall.

## Why JSON Is For Automation And Markdown Is For Display

JSON reports are machine-readable. They are suitable for:

- quality gates;
- CI checks;
- trend analysis;
- automated diffing;
- Badcase export.

Markdown reports are human-readable. They are suitable for:

- GitHub project review;
- interview discussion;
- release notes;
- quick triage;
- explaining why a prompt change helped or hurt.

## How Reports Show Prompt Or RAG Improvement

Use the compare report to answer:

1. Did pass rate increase?
2. Did badcase count decrease?
3. Which cases improved?
4. Which cases regressed?
5. Did latency change too much?
6. Are the improved cases related to the intended prompt/RAG change?

For example, if `improved_cases` mainly contain `anti_hallucination` and `unknown_knowledge` samples, the improved RAG prompt probably helped refusal behavior.

If `regressed_cases` appear in `clear_conclusion` samples, the prompt may be too cautious and should be adjusted.

## How Reports Help Badcase Regression

Each failed case contains case-level evidence:

- case id;
- question;
- prompt version;
- provider;
- model;
- answer;
- expected keywords;
- expected sources;
- keyword recall;
- source hit;
- refusal flag;
- pass/fail;
- failure reasons;
- latency.

This makes a badcase actionable. A tester can inspect the failure, classify the risk, adjust the prompt or retrieval config, and keep the case as regression data.

The testing loop becomes:

```text
run eval
  -> inspect report
  -> identify badcases
  -> adjust prompt/RAG config
  -> rerun same dataset
  -> compare reports
  -> keep fixed cases in regression
```

That is the project value: LLM quality is no longer judged only by manually reading a few answers. It becomes a repeatable testing workflow.

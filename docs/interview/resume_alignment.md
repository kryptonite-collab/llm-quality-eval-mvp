# Resume Alignment Notes

This document maps resume claims to concrete code, scripts, datasets, and docs in
this MVP project.

## Claim-To-Code Mapping

| Resume claim | Evidence in this repo |
| --- | --- |
| Built an LLM/RAG quality evaluation MVP | `backend/app/services/eval_runner.py`, `backend/app/services/metrics.py`, `evals/datasets/real_rag_sample.jsonl` |
| Designed a 50-case JSONL evaluation dataset | `evals/datasets/real_rag_sample.jsonl`, `docs/dataset_design.md` |
| Implemented RAG source-hit and keyword-recall metrics | `backend/app/services/metrics.py`, report fields `answer_keyword_recall` and `source_hit_at_k` |
| Integrated a local ChromaDB retrieval path | `backend/app/services/chroma_retriever.py`, `POST /api/v1/eval/ask` with `mode="rag"` |
| Added mock provider for stable tests | `backend/app/services/llm_provider.py`, pytest default behavior |
| Added optional DeepSeek real-model provider | `backend/app/services/llm_provider.py`, `backend/scripts/run_real_eval.py`, `docs/real_eval_runbook.md` |
| Implemented Prompt A/B evaluation | `backend/scripts/run_prompt_ab_eval.py`, `evals/prompts/` |
| Built Badcase export and replay | `backend/app/services/badcase.py`, `backend/scripts/export_badcases.py`, `backend/scripts/replay_badcases.py` |
| Added minimal Agent tool-call evaluation | `backend/app/services/agent_runner.py`, `backend/app/services/agent_tools.py`, `backend/app/services/agent_metrics.py` |

## Fully Implemented

- JSONL dataset loading and structured report generation.
- QA/RAG keyword recall, source hit, refusal-when-answer-expected, latency, pass/fail metrics.
- Mock provider for deterministic local and CI tests.
- Manual DeepSeek-compatible provider path through the OpenAI-compatible client.
- Prompt A/B report generation.
- Badcase list, detail, export, and mock replay.
- Minimal Agent tool-call evaluation with tool traces and visible reasoning summaries.
- Local ChromaDB retrieval path with deterministic local embeddings and fallback.

## MVP Implementations

- ChromaDB uses a tiny local policy Markdown file and deterministic hash embeddings.
- Agent evaluation is a single mock agent runner, not a complex multi-agent system.
- Metrics are rule-based and keyword/source oriented, not LLM-as-a-Judge.
- The project is CLI/report/API focused, not a full product dashboard.
- Real-model evaluation is manual, not part of default pytest or CI.

## If Asked About Agent

Explain that the Agent part is intentionally scoped as a tool-call quality
evaluation, not a general autonomous agent framework. The mock agent produces
predictable `tool_calls`, `retrieval_trace`, `reasoning_trace`, and
`final_answer`, then metrics check whether expected tools, sources, keywords,
and latency were satisfied. `reasoning_trace` stores visible workflow summaries,
not hidden chain-of-thought.

## If Asked About ChromaDB

Explain that ChromaDB is used as a minimal local vector retrieval path over
`evals/knowledge/policy_sample.md`. The implementation chunks policy sections,
creates deterministic local embeddings, stores them in an in-memory Chroma
collection, and returns `content`, `source`, `score`, and `rank`. If ChromaDB is
unavailable in a test environment, the retriever falls back to a local lexical
scorer with the same output schema.

## If Asked About Real Models

Explain that the default provider is mock so tests are stable and free. DeepSeek
is available as a manual OpenAI-compatible provider for real evaluation runs.
API keys are expected to stay in local environment variables or local ignored
files and must never be committed.

## If Asked About The 50 Samples

Explain that the dataset is not meant to be huge; it is a curated MVP benchmark.
The 50 rows cover direct fact QA, source grounding, multi-section policy
questions, no-answer refusal, irrelevant requests, abnormal input, distractor
keywords, and wrong-refusal risk. Each row has stable `case_id`, expected
keywords, expected sources, answer/refusal labels, and notes.

## If Asked About Badcase Export And Replay

Explain that failed report rows are turned into reusable regression assets.
`export_badcases.py` can export JSONL for automated replay or CSV for manual
review. `replay_badcases.py` reads the JSONL and reruns the cases with the mock
provider by default, so it is safe for ordinary pytest and CI. Real-provider
replay is intentionally blocked in the default path.

## If Asked Why CI Does Not Run Real Models

Explain that CI should validate deterministic engineering behavior: schema,
metrics, reports, export/replay, mock provider behavior, and API compatibility.
Real model calls can be flaky, slow, paid, quota-limited, and model-version
dependent, so they are manual quality runs rather than ordinary pytest checks.

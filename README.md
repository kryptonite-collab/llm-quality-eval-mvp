# LLM/RAG/Agent Quality Evaluation and Badcase Analysis MVP

[中文说明](README.zh-CN.md) | [面试官速览](PORTFOLIO.md)

A portfolio project for testing development, LLM quality assurance, Agent intelligent testing, and LLM application testing platform roles.

This is an MVP: a lightweight API + CLI + JSON/Markdown report toolchain, not a full web platform. A web dashboard can be added later if the workflow is productized.

## Project Positioning

LLM applications fail in ways that traditional API tests do not fully cover: answers can miss required facts, retrieval can miss sources, refusal policies can fail, Agent tool calls can be wrong, and fixed badcases can return later.

This MVP turns those risks into a reproducible quality loop:

```text
JSONL evaluation dataset
  -> QA / RAG / Agent API
  -> automatic scoring
  -> report
  -> Badcase analysis
  -> Replay
  -> pytest regression
```

The default configuration uses a **deterministic evaluation mode**. It does not call external LLM APIs, which keeps CI and regression runs stable. Real LLM providers are available through an optional provider layer, with DeepSeek supported through an OpenAI-compatible API for manual evaluation.

The current RAG path is implemented as a local MVP chain: `policy_sample.md` is chunked into a minimal ChromaDB index with deterministic local embeddings and a safe fallback when ChromaDB is unavailable.

Suitable roles:

- Testing development
- LLM quality assurance
- Agent intelligent testing development
- LLM application testing platform development

## Core Interfaces

| Interface | Purpose |
| --- | --- |
| `POST /api/v1/eval/ask` | Execute a QA/RAG/Agent evaluation request with `mode=qa`, `mode=rag`, or `mode=agent` |
| `POST /api/v1/agent/eval` | Evaluate Agent answer, retrieval, and tool-call behavior |
| `GET /api/v1/badcases` | List report badcases |
| `GET /api/v1/badcases/{id}` | Inspect one badcase |
| `POST /api/v1/badcases/{id}/replay` | Replay a badcase |
| `POST /api/v1/badcases/export` | Export badcases as JSONL regression assets |

## Core Metrics

- QA/RAG: `pass_rate`, `answer_keyword_recall`, `source_hit_at_k`, `source_hit_rate`, `avg_latency_ms`
- ChromaDB retrieval: `content`, `source`, `score`, `rank`
- Agent: `tool_call_accuracy`, `agent_source_hit`, `final_answer_keyword_recall`, `timeout`, `passed`
- Badcase: type distribution, top failed cases, JSONL export, replay result

## Quick Start

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

Run the evaluation dataset from `backend/`:

```bash
uv run python -m app.services.eval_runner
```

## Optional Real Model Provider

The default provider is `mock`, so ordinary local tests and GitHub Actions CI do not call external models.

This repository also includes a small local RAG evaluation example:

- Knowledge file: [`evals/knowledge/policy_sample.md`](evals/knowledge/policy_sample.md)
- Dataset: [`evals/datasets/real_rag_sample.jsonl`](evals/datasets/real_rag_sample.jsonl)
- Report target: [`evals/reports/real_deepseek_report.json`](evals/reports/real_deepseek_report.json)
- Prompt templates: [`evals/prompts/`](evals/prompts/)

The 50-case sample covers fact QA, source-hit, multi-section questions, no-answer refusal, irrelevant requests, abnormal input, keyword distractors, and wrong-refusal risk. It uses local Markdown context and a minimal local ChromaDB retrieval path, not an external knowledge source.

To run a small real-model evaluation with DeepSeek, configure environment variables locally. API keys must not be committed:

```bash
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-flash
LLM_API_KEY=your_deepseek_api_key_here
LLM_BASE_URL=https://api.deepseek.com
```

Then run from `backend/`:

```bash
uv run --env-file .env python -m app.services.eval_runner --provider deepseek --dataset-path ../evals/datasets/real_rag_sample.jsonl --limit 10 --report-path ../evals/reports/real_deepseek_report.json
```

or:

```bash
uv run python scripts/run_real_eval.py --provider deepseek --limit 5
```

The default real-model report path is:

```text
evals/reports/real_deepseek_report.json
```

Real LLM integration tests are skipped by default. They only run when both `RUN_REAL_LLM_TESTS=true` and an API key are set.

This is still an MVP RAG case. It includes a minimal ChromaDB local retriever, but does not claim production-grade retrieval: production chunking, embedding models, reranking, LLM-as-a-judge, and large-scale evaluation are planned extensions.

### Prompt A/B Evaluation

The project includes two prompt versions:

- `baseline`: ordinary QA style
- `improved`: stricter RAG style, requiring context-grounded answers and explicit refusal when context is missing

Run from `backend/` after configuring your local `.env`:

```bash
uv run --env-file .env python scripts/run_prompt_ab_eval.py --provider deepseek --limit 10
```

This writes:

```text
evals/reports/real_deepseek_baseline_report.json
evals/reports/real_deepseek_improved_report.json
evals/reports/real_deepseek_compare_report.json
evals/reports/real_deepseek_compare_report.md
```

The compare report shows pass-rate, latency, badcase count, improved cases, and regressed cases.

Metric notes:

- `answer_keyword_recall` checks keyword coverage only.
- `source_hit_at_k` checks whether the expected context source was retrieved.
- `refusal_when_answer_expected` prevents answers like "the context does not contain..." from passing just because they repeat keywords.
- Full LLM-as-a-Judge is not implemented yet.
- Future metrics can include faithfulness, answer relevancy, context precision, and context recall.

You can also check an existing report without calling a model:

```bash
uv run python scripts/check_eval_report.py --report-path ../evals/reports/real_deepseek_improved_report.json --min-pass-rate 0.7 --max-badcase-count 3
```

See [`docs/real_eval_runbook.md`](docs/real_eval_runbook.md) for the full manual runbook.

For a sanitized explanation of how to read reports without running a real model, see [`docs/report_example.md`](docs/report_example.md). A fictional Markdown report example is available at [`evals/reports/sample_compare_report.md`](evals/reports/sample_compare_report.md).

## Tests And Lint

Run from `backend/`:

```bash
uv run pytest -q
uv run --with ruff ruff check app tests
uv run --with ruff ruff format app tests --check
```

Tests use mock provider behavior and local-only retrieval. They do not call DeepSeek, OpenAI, external embedding services, or real LLM evaluation providers.

## Evaluation Report Example

The checked-in sample report is [`evals/reports/latest_report.json`](evals/reports/latest_report.json):

```json
{
  "total": 50,
  "passed": 33,
  "failed": 17,
  "pass_rate": 0.66,
  "source_hit_rate": 1.0,
  "badcase_count": 17
}
```

Sample evaluation assets:

- Dataset: [`evals/datasets/rag_qa_sample.jsonl`](evals/datasets/rag_qa_sample.jsonl)
- 50-case RAG dataset: [`evals/datasets/real_rag_sample.jsonl`](evals/datasets/real_rag_sample.jsonl)
- Agent dataset: [`evals/datasets/agent_eval_sample.jsonl`](evals/datasets/agent_eval_sample.jsonl)
- Badcases: [`evals/badcases/badcases.jsonl`](evals/badcases/badcases.jsonl)
- Metric design: [`docs/eval_metrics.md`](docs/eval_metrics.md)
- Badcase flow: [`docs/badcase_flow.md`](docs/badcase_flow.md)
- Resume alignment: [`docs/interview/resume_alignment.md`](docs/interview/resume_alignment.md)

## Structure

```text
.
├── backend/              # FastAPI application and pytest suite
├── docs/                 # Evaluation design and interview notes
├── evals/                # JSONL datasets, reports, and exported badcases
├── PORTFOLIO.md          # Interviewer-oriented project overview
├── README.md
└── README.zh-CN.md
```

## Source Note

This project is based on `full-stack-ai-agent-template`, then trimmed and secondarily developed into an independent LLM/RAG/Agent quality evaluation portfolio project.

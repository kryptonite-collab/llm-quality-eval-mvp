# LLM/RAG/Agent Quality Evaluation and Badcase Analysis MVP

[中文说明](README.zh-CN.md) | [面试官速览](PORTFOLIO.md)

A portfolio project for testing development, LLM quality assurance, Agent intelligent testing, and LLM application testing platform roles.

## Project Positioning

LLM applications fail in ways that traditional API tests do not fully cover: answers can miss required facts, retrieval can miss sources, refusal policies can fail, Agent tool calls can be wrong, and fixed badcases can return later.

This MVP turns those risks into a reproducible quality loop:

```text
JSONL evaluation dataset
  -> QA / Agent API
  -> automatic scoring
  -> report
  -> Badcase analysis
  -> Replay
  -> pytest regression
```

The default configuration uses a **deterministic evaluation mode**. It does not call external LLM APIs, which keeps CI and regression runs stable. Real LLM providers are available through an optional provider layer, with DeepSeek supported through an OpenAI-compatible API.

Suitable roles:

- Testing development
- LLM quality assurance
- Agent intelligent testing development
- LLM application testing platform development

## Core Interfaces

| Interface | Purpose |
| --- | --- |
| `POST /api/v1/eval/ask` | Execute a QA/RAG evaluation request |
| `POST /api/v1/agent/eval` | Evaluate Agent answer, retrieval, and tool-call behavior |
| `GET /api/v1/badcases` | List report badcases |
| `GET /api/v1/badcases/{id}` | Inspect one badcase |
| `POST /api/v1/badcases/{id}/replay` | Replay a badcase |
| `POST /api/v1/badcases/export` | Export badcases as JSONL regression assets |

## Core Metrics

- QA/RAG: `pass_rate`, `answer_keyword_recall`, `source_hit_at_k`, `source_hit_rate`, `avg_latency_ms`
- Agent: `tool_called`, `tool_name_correct`, `source_hit_at_k`, `reasoning_trace_valid`, `timeout`, `pass`
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

The sample covers refund, support review, billing contact, cancellation, eligibility-window, source-hit, and unknown-knowledge refusal cases. It uses local Markdown context, not an external knowledge source.

To run a small real-model evaluation with DeepSeek, configure environment variables in your shell or copy `.env.example` / `backend/.env.example` to `backend/.env` locally:

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

This is still an MVP RAG case. It does not claim production-grade retrieval: full vector-store retrieval, reranking, LLM-as-a-judge, and large-scale evaluation are planned extensions.

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
```

The compare report shows pass-rate, latency, badcase count, improved cases, and regressed cases.

Metric notes:

- `answer_keyword_recall` checks keyword coverage only.
- `source_hit_at_k` checks whether the expected context source was retrieved.
- `refusal_when_answer_expected` prevents answers like "the context does not contain..." from passing just because they repeat keywords.
- Full LLM-as-a-Judge is not implemented yet.
- Future metrics can include faithfulness, answer relevancy, context precision, and context recall.

## Tests And Lint

Run from `backend/`:

```bash
uv run pytest -q
uv run --with ruff ruff check app tests
uv run --with ruff ruff format app tests --check
```

Tests set `TESTING=true`, so they do not initialize real ChromaDB, OpenAI, embedding resources, or real LLM evaluation providers.

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
- Agent dataset: [`evals/datasets/agent_eval_sample.jsonl`](evals/datasets/agent_eval_sample.jsonl)
- Badcases: [`evals/badcases/badcases.jsonl`](evals/badcases/badcases.jsonl)
- Metric design: [`docs/eval_metrics.md`](docs/eval_metrics.md)
- Badcase flow: [`docs/badcase_flow.md`](docs/badcase_flow.md)

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

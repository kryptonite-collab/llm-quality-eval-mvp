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

The default configuration uses a **deterministic evaluation mode**. It does not call external LLM APIs, which keeps CI and regression runs stable. Real LLM, RAG, embedding, and vector-store integrations can replace the provider layer when needed.

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

## Tests And Lint

Run from `backend/`:

```bash
uv run pytest -q
uv run --with ruff ruff check app tests
uv run --with ruff ruff format app tests --check
```

Tests set `TESTING=true`, so they do not initialize real ChromaDB, OpenAI, or embedding resources.

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

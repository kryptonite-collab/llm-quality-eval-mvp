# System Design

## Overview

This backend is a local, reproducible MVP for LLM, RAG, and Agent quality evaluation.

The system is organized around three loops:

1. QA/RAG evaluation loop
2. Badcase analysis and regression loop
3. Agent tool-call evaluation loop

The implementation uses deterministic mocks for the LLM, retriever, and Agent behavior. This keeps the evaluation stable and makes tests repeatable.

## High-Level Architecture

```text
FastAPI routes
  -> Pydantic schemas
  -> service layer
  -> JSONL datasets / JSON reports / JSONL badcases
  -> pytest regression tests
```

Core files:

```text
app/api/routes/v1/eval.py
app/api/routes/v1/agent_eval.py
app/api/routes/v1/badcases.py
app/services/llm_qa.py
app/services/metrics.py
app/services/eval_runner.py
app/services/badcase.py
app/services/agent_qa.py
app/services/agent_tools.py
app/services/agent_metrics.py
evals/datasets/rag_qa_sample.jsonl
evals/reports/latest_report.json
evals/badcases/badcases.jsonl
```

## API Layer

The API layer exposes a small set of testing-focused endpoints:

| Endpoint | Purpose |
| --- | --- |
| `POST /api/v1/eval/ask` | Run one mock QA/RAG request |
| `POST /api/v1/agent/eval` | Run one mock Agent tool-call evaluation |
| `GET /api/v1/badcases` | List report-backed badcases |
| `GET /api/v1/badcases/{id}` | Get one badcase |
| `POST /api/v1/badcases/{id}/replay` | Replay one badcase and rescore it |
| `POST /api/v1/badcases/export` | Export badcases to JSONL |

Routes are thin. They validate request/response payloads with Pydantic and delegate logic to services.

## Service Layer

The service layer contains the core MVP logic:

| Service | Responsibility |
| --- | --- |
| `LLMQAService` | Deterministic mock QA/RAG answer generation |
| `metrics.py` | Rule-based answer/source scoring |
| `eval_runner.py` | Load JSONL dataset, run QA, write JSON report |
| `BadcaseService` | Read badcases from report, replay, export JSONL |
| `AgentQAService` | Rule-based Agent decision and final answer generation |
| `agent_tools.py` | Mock retriever tool |
| `agent_metrics.py` | Agent-specific process and output metrics |

## Dataset, Report, and Badcase File Flow

```text
evals/datasets/rag_qa_sample.jsonl
  -> app.services.eval_runner
  -> app.services.llm_qa
  -> app.services.metrics
  -> evals/reports/latest_report.json
  -> app.services.badcase
  -> evals/badcases/badcases.jsonl
  -> tests/test_badcase_regression.py
```

The report is the current source of truth for badcases. There is no database-backed badcase model in this MVP.

## Eval API Call Chain

```text
POST /api/v1/eval/ask
  -> EvalAskRequest
  -> LLMQAService.ask()
  -> EvalAskResponse
```

When `use_rag=true`, `LLMQAService` attaches one deterministic context:

```json
{
  "source": "mock_policy.md",
  "content": "This is a mock RAG context for local MVP testing.",
  "score": 1.0
}
```

## Agent Eval API Call Chain

```text
POST /api/v1/agent/eval
  -> AgentEvalRequest
  -> AgentQAService.run_eval()
  -> decide_tool
  -> mock_retriever() or skip_tool
  -> evaluate_agent_result()
  -> AgentEvalResponse
```

The Agent evaluator records process traces:

- `tool_calls`
- `retrieval_trace`
- `reasoning_trace`

This is different from ordinary QA evaluation because it validates the action path, not only final text.

## Badcase API Call Chain

```text
GET /api/v1/badcases
  -> BadcaseService.list_badcases()
  -> latest_report.json

GET /api/v1/badcases/{id}
  -> BadcaseService.get_badcase()
  -> latest_report.json

POST /api/v1/badcases/{id}/replay
  -> BadcaseService.replay_badcase()
  -> LLMQAService.ask()
  -> evaluate_qa_result()

POST /api/v1/badcases/export
  -> BadcaseService.export_badcases()
  -> evals/badcases/badcases.jsonl
```

## Why Start With Mocks

The project intentionally starts with deterministic mocks because:

- Tests can run without network access.
- No API key or model cost is required.
- Metric and report logic can be validated independently.
- Badcase regression results are stable.
- Interview demonstration is reproducible.

This is a quality platform design choice, not a claim that the current system is a production LLM/RAG stack.

## Replacing With Real LLM/RAG Later

The current replacement points are clear:

- Replace `LLMQAService.ask()` with a model client adapter.
- Replace the mock context in `LLMQAService` with a real retriever.
- Replace `mock_retriever()` with a ChromaDB or vector-store retriever.
- Keep `metrics.py`, `eval_runner.py`, report schema, badcase replay, and pytest regression mostly unchanged.

Future real-model support should keep a mock mode so CI and local regression remain deterministic.

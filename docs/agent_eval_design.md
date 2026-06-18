# Agent Tool-Calling Evaluation Design

This project adds a minimal, deterministic Agent evaluation path for resume-level
Agent/RAG quality evaluation claims. It is intentionally not a multi-agent system.
It can be exercised directly through the script below or through
`POST /api/v1/eval/ask` with `mode="agent"`.

## Scope

- Default provider: `mock`
- Default model: `mock-agent-v1`
- Real DeepSeek calls: skipped by default and not supported by this Agent eval
- Inputs: `evals/datasets/agent_eval_sample.jsonl`
- Outputs: `evals/reports/agent_eval_report.json` and
  `evals/reports/agent_eval_report.md`

## Tools

`search_policy(query)` reads local policy context from
`evals/knowledge/policy_sample.md`. If that file is unavailable, the tool uses a
small built-in fallback policy so tests remain deterministic.

The separate RAG path uses `backend/app/services/chroma_retriever.py` for a
minimal local ChromaDB retriever. The Agent eval keeps its own deterministic
tool traces so tool-call scoring remains stable and easy to inspect.

`lookup_order(order_id)` returns fixed mock order records, including order status,
completion time, completed days, member status, and item.

`calculate_refund_window(completed_days)` applies the local rule that refund
requests are eligible within 7 days after order completion.

## Runner Trace

The mock runner creates predictable tool calls from each task:

- `tool_calls`: every tool invocation with arguments and tool result
- `retrieval_trace`: local source hits returned by `search_policy`
- `reasoning_trace`: visible step summaries, such as checking the order, reading
  policy, calculating the refund window, and writing the final answer
- `final_answer`: deterministic user-facing answer
- `latency_ms`: local execution time

`reasoning_trace` does not store hidden chain-of-thought. It only stores visible,
auditable summaries of the workflow.

## Metrics

Each case is scored with:

- `tool_call_accuracy`: expected tools covered by actual tool calls
- `agent_source_hit`: expected sources covered by retrieval trace
- `final_answer_keyword_recall`: expected keywords covered by the final answer
- `timeout`: whether latency exceeds `max_latency_ms`
- `passed`: all required checks passed
- `failure_reasons`: missing tools, missing sources, missing keywords, or timeout

## How to Run

From the `backend` directory:

```bash
uv run python scripts/run_agent_eval.py
```

Then inspect:

- `evals/reports/agent_eval_report.json`
- `evals/reports/agent_eval_report.md`

This command uses the mock agent only. It does not read `.env` and does not call
DeepSeek.

# Agent Evaluation

## Goal

Agent evaluation checks whether an Agent follows the expected process, not only whether the final answer contains the right words.

The current MVP evaluates:

- Whether a tool should be called
- Whether the correct tool was called
- Whether the retrieved source was hit
- Whether the final answer contains expected keywords
- Whether the reasoning trace has expected steps
- Whether the run exceeded timeout

## Entry Point

API endpoint:

```http
POST /api/v1/agent/eval
```

Route:

```text
app/api/routes/v1/agent_eval.py
```

Service:

```text
app/services/agent_qa.py
```

## AgentQAService Flow

```text
question
  -> received_question
  -> decide_tool
  -> tool_call or skip_tool
  -> generate_final_answer
  -> agent_metrics
```

The service returns:

- `final_answer`
- `tool_calls`
- `retrieval_trace`
- `reasoning_trace`
- `latency_ms`
- `status`
- `metrics`

## decide_tool Logic

The current decision is rule-based.

If the question contains one of these keywords, the Agent calls the retriever:

```text
policy
refund
source
knowledge
document
rag
```

Otherwise, the Agent skips tool use.

This is deterministic and intentionally simple for testing.

## Mock Retriever

Implemented in:

```text
app/services/agent_tools.py
```

The retriever returns one mock context:

```json
{
  "source": "mock_policy.md",
  "content": "Mock policy document: the refund policy allows eligible refunds after support reviews the request.",
  "score": 1.0
}
```

This is not real ChromaDB or vector search.

## tool_calls

`tool_calls` records each tool invocation:

```json
{
  "tool_name": "retriever",
  "input": "What is the refund policy?",
  "output": {
    "contexts": []
  },
  "latency_ms": 0.0
}
```

This makes tool behavior testable.

## retrieval_trace

`retrieval_trace` contains the contexts returned by the retriever.

It is used by `source_hit_at_k`.

## reasoning_trace

`reasoning_trace` is a deterministic process trace.

Valid traces include:

```json
[
  "received_question",
  "decide_tool",
  "tool_call",
  "generate_final_answer"
]
```

or:

```json
[
  "received_question",
  "decide_tool",
  "skip_tool",
  "generate_final_answer"
]
```

## final_answer

If no tool is used:

```text
Direct mock answer for question: <question>
```

If retrieval is used:

```text
Based on mock_policy.md, the answer to '<question>' is: the refund policy is available in the mock policy document.
```

## agent_metrics

Implemented in:

```text
app/services/agent_metrics.py
```

Metrics:

| Metric | Meaning |
| --- | --- |
| `tool_called` | Any tool call exists |
| `tool_name_correct` | Expected tool was called |
| `source_hit_at_k` | Expected source appears in retrieval trace |
| `answer_keyword_recall` | Expected keywords found in final answer |
| `reasoning_trace_valid` | Required trace shape is valid |
| `timeout` | Latency exceeds `timeout_ms` |
| `pass` | Combined final result |

## Difference From Ordinary QA Evaluation

Ordinary QA evaluation checks:

- answer text
- source hit
- pass/fail

Agent evaluation also checks:

- tool selection
- tool call record
- retrieval trace
- reasoning trace
- process-level correctness

This matters because an Agent can produce a plausible final answer while using the wrong tool or skipping required retrieval.

## Current Limitation

The current Agent is a deterministic rule-based mock. It is not OpenAI Agents SDK, LangChain, LangGraph, or another real Agent framework.

This is intentional for an MVP: it validates the Agent evaluation contract before integrating real Agent runtimes.

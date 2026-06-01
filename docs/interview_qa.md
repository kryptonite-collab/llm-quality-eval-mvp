# Interview Q&A

## 1. Why not use a real LLM?

Answer points:

- The current MVP focuses on evaluation infrastructure, not model capability.
- Deterministic mocks make tests reproducible and cheap.
- No API key, network access, or model cost is required.
- A real model adapter can be added later while keeping the same metrics, runner, report, and badcase flow.

## 2. Is the RAG retrieval real?

Answer points:

- Not yet.
- Current retrieval is a deterministic mock returning `mock_policy.md`.
- The purpose is to validate source-hit metrics and report structure.
- Real ChromaDB or vector-store retrieval is a planned extension.

## 3. Does `source_hit_rate=1.0` mean the RAG system is perfect?

Answer points:

- No.
- It means every sample with `expected_source` hit the mock source in the current deterministic dataset.
- Because the retriever is mocked, this number validates the pipeline, not real RAG quality.

## 4. Is a mock project too artificial?

Answer points:

- The model is mocked, but the testing workflow is real.
- Dataset loading, scoring, report generation, badcase replay, export, and pytest regression are all implemented.
- For testing development, a stable mock layer is useful before integrating flaky or costly external systems.

## 5. What does badcase replay do?

Answer points:

- It loads a failed sample from `latest_report.json`.
- It reruns the same question through `LLMQAService`.
- It rescores the result with `evaluate_qa_result`.
- It returns whether the case passed after replay and which metrics still failed.

## 6. How does pytest parameterized regression work?

Answer points:

- Badcases are stored as JSONL.
- The test loads badcases from JSONL.
- `pytest.mark.parametrize` runs the same replay/scoring logic for each case.
- This turns discovered failures into repeatable regression tests.

## 7. Where is the Agent part?

Answer points:

- `POST /api/v1/agent/eval` runs Agent evaluation.
- `AgentQAService` decides whether to call a retriever.
- It records `tool_calls`, `retrieval_trace`, `reasoning_trace`, and `final_answer`.
- `agent_metrics.py` scores process-level Agent behavior.

## 8. How is Agent evaluation different from normal QA evaluation?

Answer points:

- Normal QA evaluation checks the final answer and source hit.
- Agent evaluation also checks whether the right tool was called.
- It validates reasoning trace shape and timeout.
- This catches process failures that final-answer-only checks can miss.

## 9. What is the biggest current weakness?

Answer points:

- The biggest technical weakness is that LLM, RAG, and Agent behavior are deterministic mocks.
- The biggest presentation weakness was lack of dedicated documentation.
- Next technical improvements should be batch Agent evaluation, report visualization, CI, and optional real RAG mode.

## 10. If you continue, what would you build first?

Answer points:

- First, stabilize documentation and CI so the project is easy to review and verify.
- Then add Agent eval runner so Agent evaluation becomes batch-based like QA evaluation.
- After that, add Markdown/HTML reports for easier analysis.

## 11. How does this project relate to testing development roles?

Answer points:

- It treats LLM output quality as a testable system.
- It includes API tests, service tests, parameterized regression, and badcase replay.
- It turns failures into reusable test data.
- It focuses on quality gates, failure analysis, and repeatability.

## 12. How does this align with LLM quality assurance roles?

Answer points:

- It has evaluation datasets, automatic metrics, report generation, badcase classification, and regression validation.
- It separates evaluation infrastructure from model implementation.
- It can be extended to real RAG, LLM-as-judge, prompt comparison, and CI-based quality gates.

## 13. Why use JSONL for datasets and badcases?

Answer points:

- JSONL is simple, diffable, and easy to append.
- Each line is one independent case.
- It works well with pytest parameterization and batch runners.
- It avoids needing a database in the MVP stage.

## 14. Why not store badcases in a database?

Answer points:

- The MVP prioritizes a stable evaluation loop.
- JSON report and JSONL export are enough to demonstrate badcase analysis and regression.
- Database persistence is useful later for multi-run history, ownership, status, and dashboard workflows.

## 15. How would you add real RAG?

Answer points:

- Keep the current evaluation contracts.
- Replace mock context generation in `LLMQAService` or `mock_retriever` with a vector-store retriever.
- Add config to switch between mock and real retrieval.
- Add tests that keep mock mode deterministic for CI.

## 16. How would you add LLM-as-judge?

Answer points:

- Add it as an optional metric, not a replacement for deterministic checks.
- Keep keyword/source metrics for cheap regression.
- Use judge scoring for semantic quality, faithfulness, and answer relevance.
- Cache or mock judge outputs in tests to avoid flaky CI.

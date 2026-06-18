# Agent Evaluation Report

- provider: mock
- model: mock-agent-v1
- dataset: evals/datasets/agent_eval_sample.jsonl
- total_cases: 10
- pass_rate: 100.00%
- badcase_count: 0
- avg_latency_ms: 0.00
- tool_call_accuracy_avg: 1.00
- source_hit_rate: 1.00

| case_id | category | passed | latency_ms | failure_reasons |
| --- | --- | --- | ---: | --- |
| agent-001 | refund_within_window | True | 0 |  |
| agent-002 | refund_expired | True | 0 |  |
| agent-003 | vip_refund | True | 0 |  |
| agent-004 | unfinished_order | True | 0 |  |
| agent-005 | refund_boundary | True | 0 |  |
| agent-006 | policy_only | True | 0 |  |
| agent-007 | order_not_found | True | 0 |  |
| agent-008 | order_lookup | True | 0 |  |
| agent-009 | membership_policy | True | 0 |  |
| agent-010 | full_trace | True | 0 |  |

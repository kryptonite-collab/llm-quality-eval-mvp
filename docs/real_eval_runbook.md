# Real Model Evaluation Runbook

## Why Default Tests Use Mock Mode

Default tests use deterministic mock mode so local pytest and GitHub Actions CI are stable, cheap, and reproducible.

Mock mode does not require API keys, network access, model availability, or external provider rate limits. It protects the regression suite from model randomness and infrastructure failures.

The MVP RAG path can use the local ChromaDB retriever over
`evals/knowledge/policy_sample.md`. This retriever is local-only and has a
fallback path, so ordinary tests do not need external embedding services.

## Why DeepSeek Eval Is Manual

DeepSeek evaluation is a real external-model call. It may cost money, require network access, depend on API quota, and produce answers that can vary across model versions.

For that reason, real eval commands are manual. They are not part of ordinary pytest or CI.

DeepSeek should be used for intentional manual checks, prompt comparisons, and
portfolio evidence. It should not be part of default pytest or CI because API
availability, quota, latency, cost, and model-version changes would make the
regression suite unstable.

## Local `.env` Example

Create `backend/.env` locally if needed. Do not commit it.

```env
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-flash
LLM_API_KEY=<your key>
LLM_BASE_URL=https://api.deepseek.com
RUN_REAL_LLM_TESTS=false
```

## Baseline Prompt Run

Run from `backend/`:

```bash
uv run --env-file .env python -m app.services.eval_runner --provider deepseek --dataset-path ../evals/datasets/real_rag_sample.jsonl --limit 10 --report-path ../evals/reports/real_deepseek_baseline_report.json --prompt-version baseline
```

## Improved Prompt Run

Run from `backend/`:

```bash
uv run --env-file .env python -m app.services.eval_runner --provider deepseek --dataset-path ../evals/datasets/real_rag_sample.jsonl --limit 10 --report-path ../evals/reports/real_deepseek_improved_report.json --prompt-version improved
```

## Prompt A/B Compare Run

Run from `backend/`:

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

## Viewing Reports

Use JSON reports for exact metrics and automation.

Use the Markdown report for interview or portfolio review. It summarizes provider, model, dataset, pass-rate change, badcase-count change, latency change, improved cases, regressed cases, changed cases, and metric notes.

## Quality Gate

You can check an existing report without calling a model:

```bash
uv run python scripts/check_eval_report.py --report-path ../evals/reports/real_deepseek_improved_report.json --min-pass-rate 0.7 --max-badcase-count 3
```

The command exits with non-zero status when the report does not meet thresholds.

## Badcase Export And Replay

Export failed cases from an existing report:

```bash
uv run python scripts/export_badcases.py --report-path ../evals/reports/latest_report.json --output-path ../evals/badcases/badcases.jsonl
```

Export CSV when a spreadsheet-friendly artifact is needed:

```bash
uv run python scripts/export_badcases.py --report-path ../evals/reports/latest_report.json --output-path ../evals/badcases/badcases.csv --format csv
```

Replay exported badcases with the mock provider:

```bash
uv run python scripts/replay_badcases.py --input-path ../evals/badcases/badcases.jsonl --output-path ../evals/reports/badcase_replay_report.json
```

Real provider replay is disabled by default. Use mock replay for ordinary
regression checks.

## API Mode Check

`POST /api/v1/eval/ask` supports:

- `mode="qa"` for ordinary mock/provider QA.
- `mode="rag"` for local ChromaDB-backed policy retrieval.
- `mode="agent"` for the minimal mock Agent tool-call evaluation.

The response includes answer, contexts, latency, provider, model,
prompt_version, and mode. Agent mode also returns tool calls, retrieval trace,
visible reasoning trace, and final answer.

## Files That Can Be Committed

- Source code under `backend/app/`
- Scripts under `backend/scripts/`
- Tests under `backend/tests/`
- Documentation under `docs/`
- Prompt templates under `evals/prompts/`
- Sample knowledge and datasets under `evals/knowledge/` and `evals/datasets/`
- Sanitized JSON or Markdown reports when they do not contain API keys, local absolute paths, or sensitive data
- Resume and interview notes under `docs/interview/`
- Badcase JSONL or CSV exports when they are sanitized and do not contain secrets

## Files That Must Not Be Committed

- `.env`
- `backend/.env`
- Real API keys
- Logs that include API keys
- Screenshots that show API keys
- Local cache directories
- Reports containing secrets or machine-specific private paths
- ChromaDB local persistence directories or cache folders

## Interview Explanation

You can explain the real-model evaluation chain like this:

The project defaults to deterministic mock mode for stable CI, then exposes a manual DeepSeek OpenAI-compatible provider for real evaluation. A small local policy knowledge base and JSONL dataset create a reproducible RAG sample. Baseline and improved prompts are evaluated against the same dataset, then a compare report shows whether pass rate, badcase count, latency, improved cases, and regressed cases changed. This turns model quality discussion from subjective answer reading into a repeatable engineering workflow.

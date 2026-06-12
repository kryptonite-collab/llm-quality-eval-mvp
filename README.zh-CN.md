# 面向 LLM/RAG/Agent 应用的大模型质量评测与 Badcase 分析平台

[English README](README.md) | [面试官速览](PORTFOLIO.md)

这是一个面向作品集展示的质量保障 MVP，适合投递：

- 测试开发
- 大模型质量保障
- Agent 智能化测试开发
- LLM 应用测试平台开发

## 项目定位

LLM 应用除了传统接口错误，还会遇到答案缺失、来源未命中、拒答失败、Agent 工具调用错误、Badcase 无法沉淀等问题。

本项目把这些问题整理成一条可执行、可统计、可回归的闭环：

```text
JSONL 评测集
  -> 问答 / Agent 接口
  -> 自动评分
  -> report
  -> Badcase 分析
  -> Replay
  -> pytest 回归
```

默认使用 **deterministic evaluation mode**，不调用外部 LLM，适合稳定 CI 和回归测试。真实大模型可以通过可选 provider 层接入，目前支持 DeepSeek OpenAI-compatible API，并预留 OpenAI-compatible 配置。

## 核心接口

| 接口 | 用途 |
| --- | --- |
| `POST /api/v1/eval/ask` | 执行 QA/RAG 评测请求 |
| `POST /api/v1/agent/eval` | 评测 Agent 回答、检索与工具调用 |
| `GET /api/v1/badcases` | 查询 Badcase 列表 |
| `GET /api/v1/badcases/{id}` | 查看 Badcase 详情 |
| `POST /api/v1/badcases/{id}/replay` | Replay 复测 |
| `POST /api/v1/badcases/export` | 导出 JSONL 回归资产 |

## 核心指标

- QA/RAG：`pass_rate`、`answer_keyword_recall`、`source_hit_at_k`、`source_hit_rate`、`avg_latency_ms`
- Agent：`tool_called`、`tool_name_correct`、`source_hit_at_k`、`reasoning_trace_valid`、`timeout`、`pass`
- Badcase：类型分布、失败案例排行、JSONL 导出、Replay 结果

## 快速启动

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

访问 `http://127.0.0.1:8000/docs`。

运行批量评测：

```bash
uv run python -m app.services.eval_runner
```

## 可选真实大模型 Provider

默认 `LLM_PROVIDER=mock`，所以普通本地测试和 GitHub Actions CI 不会调用外部模型。

仓库里也包含一个本地真实 RAG 小样本案例：

- 知识库文件：[`evals/knowledge/policy_sample.md`](evals/knowledge/policy_sample.md)
- 评测集：[`evals/datasets/real_rag_sample.jsonl`](evals/datasets/real_rag_sample.jsonl)
- 报告输出：[`evals/reports/real_deepseek_report.json`](evals/reports/real_deepseek_report.json)
- Prompt 模板：[`evals/prompts/`](evals/prompts/)

这个样本覆盖 refund、support review、billing contact、cancellation、eligibility window、来源命中和知识库不存在时拒答等场景。它使用本地 Markdown 内容作为上下文，不引入外部知识源。

如果要使用 DeepSeek 跑一小批真实模型评测，可以在本机 shell 环境设置变量，或把 `.env.example` / `backend/.env.example` 复制为本地 `backend/.env` 后填写：

```bash
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-flash
LLM_API_KEY=your_deepseek_api_key_here
LLM_BASE_URL=https://api.deepseek.com
```

然后在 `backend/` 目录执行：

```bash
uv run --env-file .env python -m app.services.eval_runner --provider deepseek --dataset-path ../evals/datasets/real_rag_sample.jsonl --limit 10 --report-path ../evals/reports/real_deepseek_report.json
```

也可以执行：

```bash
uv run python scripts/run_real_eval.py --provider deepseek --limit 5
```

默认真实模型报告输出到：

```text
evals/reports/real_deepseek_report.json
```

真实模型集成测试默认跳过，只有同时设置 `RUN_REAL_LLM_TESTS=true` 和 API key 时才会运行。

当前仍是 MVP 级 RAG 案例，不是生产级检索系统。完整向量库检索、rerank、LLM-as-a-Judge 和大规模评测属于后续增强。

### Prompt A/B 评测

项目包含两个 prompt 版本：

- `baseline`：普通问答风格；
- `improved`：更严格的 RAG 风格，要求优先依据 context，context 不包含答案时明确拒答。

本机配置 `.env` 后，在 `backend/` 目录执行：

```bash
uv run --env-file .env python scripts/run_prompt_ab_eval.py --provider deepseek --limit 10
```

会生成：

```text
evals/reports/real_deepseek_baseline_report.json
evals/reports/real_deepseek_improved_report.json
evals/reports/real_deepseek_compare_report.json
```

对比报告会展示通过率、平均延迟、Badcase 数量、变好的样本和退化样本。

指标说明：

- `answer_keyword_recall` 只衡量关键词覆盖；
- `source_hit_at_k` 衡量期望来源是否命中；
- `refusal_when_answer_expected` 用于防止“模型复述关键词但实际拒答”被误判通过；
- 当前没有接完整 LLM-as-a-Judge；
- 后续可以扩展 faithfulness、answer relevancy、context precision、context recall 等指标。

## 测试与 Lint

在 `backend/` 目录执行：

```bash
uv run pytest -q
uv run --with ruff ruff check app tests
uv run --with ruff ruff format app tests --check
```

测试环境设置 `TESTING=true`，不会初始化真实 ChromaDB、OpenAI、embedding 资源或真实 LLM 评测 provider。

## 评测报告示例

仓库内保留了可直接查看的样例报告：[`evals/reports/latest_report.json`](evals/reports/latest_report.json)。

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

关键资料：

- QA/RAG 评测集：[`evals/datasets/rag_qa_sample.jsonl`](evals/datasets/rag_qa_sample.jsonl)
- Agent 评测集：[`evals/datasets/agent_eval_sample.jsonl`](evals/datasets/agent_eval_sample.jsonl)
- Badcase 导出：[`evals/badcases/badcases.jsonl`](evals/badcases/badcases.jsonl)
- 指标说明：[`docs/eval_metrics.md`](docs/eval_metrics.md)
- Badcase 闭环：[`docs/badcase_flow.md`](docs/badcase_flow.md)

## 目录结构

```text
.
├── backend/              # FastAPI 服务与 pytest 测试
├── docs/                 # 评测设计与面试说明
├── evals/                # JSONL 评测集、报告、Badcase
├── PORTFOLIO.md          # 面向面试官的项目速览
├── README.md
└── README.zh-CN.md
```

## 来源说明

本项目基于 `full-stack-ai-agent-template` 裁剪和二次开发，已整理为独立的大模型质量评测作品集项目。

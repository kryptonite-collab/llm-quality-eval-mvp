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

默认使用 **deterministic evaluation mode**，不调用外部 LLM，适合稳定 CI 和回归测试。真实 LLM、RAG、embedding 和向量库可以通过 provider 层替换接入。

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

## 测试与 Lint

在 `backend/` 目录执行：

```bash
uv run pytest -q
uv run --with ruff ruff check app tests
uv run --with ruff ruff format app tests --check
```

测试环境设置 `TESTING=true`，不会初始化真实 ChromaDB、OpenAI 或 embedding 资源。

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

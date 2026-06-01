# 面向 LLM/RAG/Agent 应用的大模型质量评测与 Badcase 分析平台

## 项目背景

LLM 应用存在传统接口测试难以覆盖的质量问题：答案缺失、来源未命中、拒答失败、工具调用错误，以及 Badcase 修复后无法持续沉淀为回归资产。本项目以测试开发视角实现一个可本地演示、可稳定回归的质量评测 MVP。

## 解决方案

```text
JSONL 评测集
  -> 问答 / Agent 接口
  -> 自动评分
  -> report
  -> Badcase
  -> Replay
  -> pytest 回归
```

默认使用 deterministic evaluation mode，不调用外部 LLM，保证 CI 和面试演示稳定。真实 LLM、RAG、embedding 与向量库保留 provider 层替换空间。

## 核心功能

- QA/RAG 批量评测：从 JSONL 数据集运行问答并生成结构化报告。
- Agent 过程评测：检查最终答案、工具选择、检索来源、reasoning trace 与超时。
- Badcase 沉淀：支持列表、详情、类型分布、失败排行、JSONL 导出。
- Replay 与回归：对单条 Badcase 复测，并通过 pytest 参数化回归。
- 测试隔离：测试环境显式跳过真实 ChromaDB、OpenAI 和 embedding 初始化。

## 技术栈

`FastAPI`、`Pydantic`、`pytest`、`HTTPX`、`JSONL`、`JSON report`、`ruff`、`uv`

## 核心指标

| 场景 | 指标 |
| --- | --- |
| QA/RAG | `pass_rate`、`answer_keyword_recall`、`source_hit_at_k`、`source_hit_rate`、`avg_latency_ms` |
| Agent | `tool_called`、`tool_name_correct`、`reasoning_trace_valid`、`timeout`、`pass` |
| Badcase | 类型分布、Top failed cases、Replay 结果、JSONL 回归资产 |

## 测试结果

- 完整 pytest 基线：`162 passed, 1 skipped`
- 样例评测集：`50` 条
- 样例通过率：`66%`
- 样例 Badcase：`17` 条
- 来源命中率：`100%`

## 可演示命令

在 `backend/` 目录执行：

```bash
uv sync
uv run pytest -q
uv run python -m app.services.eval_runner
uv run uvicorn app.main:app --reload
```

启动后可通过 Swagger UI 演示：

- `POST /api/v1/eval/ask`
- `POST /api/v1/agent/eval`
- `GET /api/v1/badcases`
- `POST /api/v1/badcases/{id}/replay`

## 当前限制与后续计划

- 当前默认 provider 是确定性评测模式，重点是展示质量闭环，不代表线上模型效果。
- 下一步可接入真实 LLM/RAG provider，增加模型对比、LLM-as-a-Judge、语义相似度和检索分层指标。
- 可进一步增加 Web 控制台、趋势看板、数据集版本管理、CI 阈值门禁和线上 Badcase 自动回流。

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

默认使用 deterministic evaluation mode，不调用外部 LLM，保证 CI 和面试演示稳定。项目已通过 provider 层支持可选真实大模型调用，优先接入 DeepSeek OpenAI-compatible API，并保留 OpenAI-compatible 配置空间。

## 核心功能

- QA/RAG 批量评测：从 JSONL 数据集运行问答并生成结构化报告。
- 真实模型 provider：默认 mock，可通过 `LLM_PROVIDER=deepseek` 或 `LLM_PROVIDER=openai` 切换到 OpenAI-compatible provider。
- 本地真实 RAG 小样本：使用 `evals/knowledge/policy_sample.md` 和 `evals/datasets/real_rag_sample.jsonl` 演示真实模型基于业务规则上下文回答。
- Prompt A/B 评测：使用 baseline 与 improved RAG prompt 生成两份真实模型报告，并输出 compare report 展示指标变化。
- Agent 过程评测：检查最终答案、工具选择、检索来源、reasoning trace 与超时。
- Badcase 沉淀：支持列表、详情、类型分布、失败排行、JSONL 导出。
- Replay 与回归：对单条 Badcase 复测，并通过 pytest 参数化回归。
- 测试隔离：测试环境显式跳过真实 ChromaDB、OpenAI、embedding 初始化和真实 LLM 集成测试。

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
uv run --env-file .env python -m app.services.eval_runner --provider deepseek --dataset-path ../evals/datasets/real_rag_sample.jsonl --limit 10 --report-path ../evals/reports/real_deepseek_report.json
uv run --env-file .env python scripts/run_prompt_ab_eval.py --provider deepseek --limit 10
uv run uvicorn app.main:app --reload
```

真实模型评测需要本机配置环境变量：

```bash
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-flash
LLM_API_KEY=your_deepseek_api_key_here
LLM_BASE_URL=https://api.deepseek.com
```

启动后可通过 Swagger UI 演示：

- `POST /api/v1/eval/ask`
- `POST /api/v1/agent/eval`
- `GET /api/v1/badcases`
- `POST /api/v1/badcases/{id}/replay`

## 当前限制与后续计划

- 当前默认 provider 是确定性评测模式，重点是展示质量闭环；真实 DeepSeek/OpenAI-compatible provider 已作为可选路径接入，不影响默认 CI。
- 当前 RAG 案例使用本地 Markdown policy 样本，不是生产级向量库检索。
- 当前指标以关键词召回、来源命中和拒答误判规则为主，还没有接完整 LLM-as-a-Judge。
- 下一步可扩展真实向量库 RAG provider，增加模型对比、LLM-as-a-Judge、语义相似度和检索分层指标。
- 可进一步增加 Web 控制台、趋势看板、数据集版本管理、CI 阈值门禁和线上 Badcase 自动回流。

## 面试口径

可以直接说：MVP 阶段我先用 deterministic mode 把评测、报告、Badcase 和回归链路做稳定，保证本地和 CI 都可复现；随后通过 provider 层接入 DeepSeek 这类 OpenAI-compatible 大模型，用环境变量切换真实模型评测。这样既能展示真实模型调用能力，又不会让普通 pytest 和 GitHub Actions 依赖外部 API。

如果面试官问“接入了什么大模型”，可以说：项目接入的是 DeepSeek OpenAI-compatible Provider，当前真实评测用 `deepseek-v4-flash` 手动运行，默认 CI 仍然走 mock，不会泄露 API key，也不会让测试依赖外部网络。

如果面试官问“有什么实际价值”，可以说：这个项目不只是调用一次大模型，而是把本地 policy 知识库、JSONL 样本、真实模型回答、自动评分、Badcase 和回归测试串起来。它能展示如何把大模型回答质量变成可复现、可解释、可持续回归的工程资产。

如果面试官追问“怎么证明优化有效”，可以说：我加了 Prompt A/B 评测，使用同一份 `real_rag_sample.jsonl` 分别跑 baseline prompt 和 improved RAG prompt，生成两份报告和一个 compare report。对比报告会列出通过率、平均延迟、Badcase 数量、改善样本和退化样本，这样 prompt 优化不是靠主观感觉，而是有可复现的指标对比。

# 项目面试材料：LLM/RAG/Agent 质量评测与 Badcase 分析 MVP

## 3 分钟项目介绍

面试时可以这样说：

这个项目是我面向 AI 开发、大模型应用开发、大模型质量保障和 Agent 智能化测试开发岗位整理的一个作品集项目。它不是单纯做一个聊天 Demo，而是把大模型应用里常见的质量问题做成了一条可执行、可统计、可回归的评测闭环。

项目的主流程是：先用 JSONL 维护评测集，然后通过 QA/RAG 接口或者 Agent 评测接口执行问题，再用规则化指标自动评分，生成 `evals/reports/latest_report.json`。报告里失败的样本会沉淀成 Badcase，Badcase 可以查询、查看详情、Replay 复测，也可以导出成 `evals/badcases/badcases.jsonl`，最后再通过 pytest 参数化回归，把线上或评测中发现的问题变成可重复执行的测试资产。CI 里会跑 ruff 和 pytest，保证这条质量链路在代码提交时能被验证。

技术上，后端是 FastAPI，数据契约用 Pydantic，评测集和 Badcase 用 JSONL，报告用 JSON，自动化测试用 pytest。项目默认使用 deterministic evaluation mode，也就是确定性的 mock LLM、mock RAG context 和 mock Agent 工具调用。这样做的原因不是说真实模型不重要，而是评测平台本身首先要稳定、可复现、低成本，尤其是 CI 和面试演示不能依赖 API key、网络和模型随机性。

当前仓库里的样例评测集有 50 条 QA/RAG 样本，覆盖 facts_qa、source_hit、multi_doc、refusal、keyword_miss、irrelevant_answer、invalid_input 等类别。最新报告是 50 条里 33 条通过、17 条失败，`pass_rate=0.66`，`source_hit_rate=1.0`，并导出了 17 条 Badcase。这里的 `source_hit_rate=1.0` 不是说真实 RAG 效果完美，而是说明在当前 mock retriever 下，期望来源 `mock_policy.md` 都被命中了，验证的是评测链路和指标合同。

Agent 部分体现在 `/api/v1/agent/eval`，它不是只看最终回答，而是检查工具是否被调用、工具名是否正确、检索来源是否命中、回答关键词是否召回、reasoning trace 是否符合预期，以及是否超时。这样可以覆盖 Agent 测试里很关键的一类问题：最终答案看起来对，但中间工具路径是错的。

我会把这个项目定位成一个质量工程视角的大模型应用测试平台 MVP。它的价值不在于模型能力本身，而在于把评测数据、自动评分、Badcase 管理、Replay、回归测试和 CI 串起来，形成一个能持续迭代的质量闭环。

## 1 分钟精简版项目介绍

面试时可以这样说：

这是一个面向 LLM/RAG/Agent 应用的质量评测和 Badcase 分析 MVP。核心闭环是：JSONL 评测集 -> QA/Agent 接口 -> 自动评分 -> `latest_report.json` -> Badcase -> Replay/Export -> pytest 回归 -> GitHub Actions CI。

它默认不用真实 OpenAI，而是用确定性的 mock provider，目的是让评测、回归和 CI 稳定可复现。当前样例数据是 50 条，报告里 33 条通过、17 条失败，Badcase 会被分类、导出，并能通过 pytest 参数化变成回归用例。

我重点展示的是大模型应用的质量保障能力：怎么设计评测集，怎么定义指标，怎么把失败样本沉淀成回归资产，以及怎么测试 Agent 的工具调用和过程轨迹。

## 项目背景和痛点

面试时可以这样说：

传统接口测试主要验证状态码、字段、数据库状态这些确定性结果，但 LLM 应用的问题更偏质量和行为：答案可能漏关键词，RAG 可能没有命中来源，拒答策略可能失败，Agent 可能用错工具，修过的 Badcase 也可能后面又复现。

所以我做这个项目时没有只做一个问答接口，而是把问题拆成一条质量链路：先有评测数据，再有自动评分，再有报告，再有 Badcase 分析和回归。这样面试官能看到的不只是“我会调模型”，而是“我知道大模型应用上线前后怎么做质量保障”。

## 我的核心贡献

面试时可以这样说：

这个项目不是完全从零搭的空仓库，README 里也明确写了来源：它基于 `full-stack-ai-agent-template` 做了裁剪和二次开发。我不会把模板里已有的通用 FastAPI、用户、数据库、基础 Agent 框架说成完全原创。

我自己的重点贡献主要在大模型质量评测这条主线：整理项目定位和文档；实现/组织 QA/RAG 评测入口；设计 JSONL 评测集；实现自动评分指标；实现批量评测 runner；生成结构化 `latest_report.json`；从报告里沉淀 Badcase；提供 Badcase 查询、详情、Replay 和 Export；把 Badcase JSONL 接到 pytest 参数化回归；补充 Agent 评测接口和工具调用、检索轨迹、reasoning trace 等过程指标；最后用 GitHub Actions 把 lint 和测试纳入 CI。

如果面试官问我哪些是模板，我会说通用 Web 后端框架和部分基础模块来自模板；如果问哪些是我围绕岗位做的，我会重点讲评测闭环、Badcase 闭环、Agent eval、评测数据和文档化。

## 技术选型理由

面试时可以这样说：

我选 FastAPI 是因为它适合快速暴露测试平台接口，Pydantic 能把请求和响应结构固定下来，这对评测平台很重要，因为数据契约要稳定。

评测集和 Badcase 选 JSONL，是因为一行一个 case，方便 diff、追加、人工审查，也很适合 pytest 参数化。报告用 JSON，是为了让服务、文档和后续可视化都能直接消费。

pytest 是测试开发岗位里最直接的技术栈，而且参数化能力很适合把 Badcase 批量转成回归用例。ruff 和 GitHub Actions 则负责基础代码质量和持续验证。

默认使用 deterministic evaluation mode，是因为质量平台要先保证自身稳定。真实模型会有随机性、成本、网络依赖和 API key 管理问题，不适合默认作为 CI 的基础。后续可以通过 provider 层把真实 LLM、真实 embedding 和向量库接进来，但 mock 模式仍然应该保留给回归测试。

## 项目亮点

面试时可以这样说：

第一个亮点是闭环完整。它不是只有评测，也不是只有测试，而是从 JSONL 数据集一路走到报告、Badcase、Replay、导出、pytest 回归和 CI。

第二个亮点是把 LLM 质量问题结构化了。报告里有 `pass_rate`、`answer_keyword_recall`、`source_hit_at_k`、`source_hit_rate`、`failed_metrics`、`badcase_type_distribution` 和 `top_failed_cases`，能帮助定位失败原因。

第三个亮点是 Badcase 能变成资产。失败样本不是只停留在报告里，而是可以 Replay 和 Export，再进入 pytest 参数化回归。

第四个亮点是 Agent 评测不只看最终答案。项目会检查 tool call、tool name、retrieval trace、reasoning trace、timeout，这更接近 Agent 智能化测试开发的关注点。

第五个亮点是默认可复现。因为不依赖真实 OpenAI 和网络，所以本地、CI、面试演示都更稳定。

## 项目不足和后续优化

面试时可以这样说：

这个项目当前最大的不足是 LLM、RAG 和 Agent 行为都是确定性 mock，还不能代表真实模型效果。比如 `source_hit_rate=1.0` 只是 mock source 命中，不是生产级 RAG 检索质量。

第二个不足是指标还偏规则化，主要是关键词召回和来源命中。它能验证评测链路，但不能完整判断语义正确性、事实一致性、引用是否真的支撑答案。

第三个不足是 Agent 评测目前是单接口和少量样例，还没有像 QA/RAG 一样做完整的批量 Agent eval runner 和多轮任务评测。

后续我会按三步扩展：先增加真实 provider 开关，支持 mock 和 real 两种模式；再引入真实 RAG，包括 embedding、向量库、rerank、context precision/recall；最后增加 LLM-as-a-Judge、趋势报告、质量阈值门禁和线上 Badcase 自动回流。

## 和 AI 开发岗位的匹配点

面试时可以这样说：

这个项目能体现我不只是会调一个模型接口，而是理解大模型应用从接口、RAG、Agent 到评测体系的完整链路。

我能把模型输出拆成可测的维度，比如答案关键词、来源命中、工具调用、reasoning trace 和超时；也能设计 provider 可替换的结构，让 mock 模式用于 CI，真实模型模式用于效果验证。

如果岗位偏 AI 应用开发，我会重点讲：FastAPI 接口、Pydantic 契约、RAG context、Agent tool call、评测 runner 和后续如何接真实 OpenAI 或向量数据库。

## 和测试开发岗位的匹配点

面试时可以这样说：

这个项目和测试开发非常匹配，因为它的主线就是把不稳定的大模型输出变成可自动化验证的质量工程。

我设计了评测集、自动评分、失败分类、Badcase Replay、JSONL 回归资产和 pytest 参数化测试，并且接入 CI。这个思路和测试开发里的“发现问题 -> 固化用例 -> 自动回归 -> 持续防回归”是一样的，只是对象从传统 API 变成了 LLM/RAG/Agent。

如果岗位偏测试平台或质量保障，我会重点讲：指标设计、数据集设计、Badcase 沉淀、回归机制、CI 质量门禁，以及未来如何把线上失败样本自动回流到评测集。

## 重点问答

### 1. 这个项目是不是基于模板？

面试时可以直接说：

是的，我不会回避这一点。README 里已经写明，项目基于 `full-stack-ai-agent-template` 做了裁剪和二次开发。模板主要提供了通用后端工程基础，比如 FastAPI 项目结构、部分基础模块和原有 Agent 相关框架。

但我面试时展示的重点不是模板能力，而是我围绕大模型质量保障重新整理出来的评测闭环：JSONL 评测集、QA/RAG 自动评分、`latest_report.json`、Badcase 查询和 Replay、Badcase 导出、pytest 参数化回归、Agent eval 指标和 CI。这个方向是面向岗位做的二次开发和作品集化整理。

### 2. 哪些部分是你自己实现的？

面试时可以直接说：

我会把“自己实现”限定在质量评测主线里讲。主要包括：`eval_runner` 读取 JSONL 并生成报告；`metrics.py` 做关键词召回和来源命中评分；`badcase.py` 从报告里读取、复测和导出 Badcase；`test_badcase_regression.py` 把 Badcase JSONL 参数化回归；`/api/v1/eval/ask`、`/api/v1/badcases`、`/api/v1/agent/eval` 这些测试导向接口；以及 Agent eval 里的 tool call、retrieval trace、reasoning trace 和相关指标。

通用用户系统、数据库模型、基础工程骨架这类我不会说成完全原创。

### 3. 为什么默认使用 deterministic evaluation mode？

面试时可以直接说：

因为这个项目首先是质量评测平台，不是模型效果排行榜。评测平台自己的结果必须稳定，否则今天 CI 过、明天 CI 不过，就很难判断是代码问题、数据问题还是模型随机性问题。

deterministic mode 的价值是：不需要 API key，不依赖网络，没有调用成本，结果可复现，适合 CI 和回归测试。等评测链路稳定后，再接真实模型会更稳。

### 4. 为什么不默认调用真实 OpenAI？

面试时可以直接说：

真实 OpenAI 适合做效果验证，但不适合作为默认 CI 依赖。它会带来 API key 管理、网络波动、成本、限流、模型版本变化和输出随机性。

所以我会把真实 OpenAI 做成可选 provider，而不是默认路径。默认路径保证任何人 clone 仓库后都能本地跑通评测、Badcase 和回归；真实模型用于扩展效果评估。

### 5. RAG 在项目里体现在哪里？

面试时可以直接说：

RAG 现在体现为 mock RAG context 和 source-hit 评测。`/api/v1/eval/ask` 在 `use_rag=true` 时会返回 `mock_policy.md` 这个 context；评测集里有 `expected_source`；评分逻辑会检查 `source_hit_at_k`；报告里会统计 `source_hit_rate`。

另外仓库里也有更完整的 RAG 相关服务目录，比如 ingestion、retrieval、vectorstore、embeddings 等，但当前作品集主线默认走 deterministic mock，不默认启动真实 ChromaDB 或真实 embedding。

### 6. Agent 在项目里体现在哪里？

面试时可以直接说：

Agent 评测入口是 `POST /api/v1/agent/eval`。它会根据问题内容决定是否调用 `retriever` 工具，如果问题里包含 policy、refund、source、knowledge、document、rag 这类关键词，就会走 mock retriever。

返回结果里不只有 final answer，还有 `tool_calls`、`retrieval_trace`、`reasoning_trace`、`latency_ms` 和 `metrics`。评分会检查工具是否调用、工具名是否正确、来源是否命中、关键词是否召回、trace 是否合法、是否超时。

### 7. Badcase Replay 做了什么？

面试时可以直接说：

Replay 做的是“这个失败样本在当前实现下还会不会失败”。它先从 `latest_report.json` 找到某条 badcase，再用同一个 question 重新调用 `LLMQAService.ask()`，然后用 `evaluate_qa_result()` 重新评分。

返回里会告诉我 `pass_after_replay` 是 true 还是 false，以及 `still_failed_metrics` 还有哪些。这样我能判断一个 Badcase 是已经修复，还是仍然需要处理。

### 8. pytest 参数化回归怎么做？

面试时可以直接说：

项目里 Badcase 可以导出成 JSONL，每一行就是一个失败样本。pytest 测试会加载 JSONL，然后通过 `pytest.mark.parametrize` 对每个 case 执行同一套 replay 和 scoring 逻辑。

这样做的好处是评测发现的问题不会只停留在报告里，而是能变成长期回归用例。以后代码或 prompt 改动后，只要跑 pytest，就能检查这些历史失败是否还按预期暴露，或者是否已经被修复。

### 9. 50 条 JSONL 样本怎么设计？

面试时可以直接说：

这 50 条样本不是随机写的，而是按质量场景覆盖。当前数据集包括 15 条 facts_qa、10 条 source_hit、8 条 multi_doc、5 条 refusal、5 条 keyword_miss、4 条 irrelevant_answer、3 条 invalid_input。

前面几类主要验证正常问答和来源命中，后面几类故意设计成失败或风险场景，用来验证评分、Badcase 分类和回归链路。每条样本都有 id、question、expected_keywords、expected_source、category、expected_behavior，有些还带 badcase_type。

### 10. `pass_rate=0.66` 说明什么？

面试时可以直接说：

它说明当前 50 条样本里有 33 条通过、17 条失败，通过率是 66%。这个数字不是在证明模型能力强弱，因为当前模型是 mock 的；它更重要的意义是证明评测 runner、评分逻辑、报告统计和 Badcase 沉淀这条链路是跑通的。

同时，66% 也说明评测集里有意放入了失败样本，不是为了刷一个好看的 100%。质量平台需要能发现问题，而不是只展示通过。

### 11. 17 条 Badcase 说明什么？

面试时可以直接说：

17 条 Badcase 对应报告里的 17 条失败样本。它们被分成 4 类：`refusal_expected` 5 条、`keyword_miss` 5 条、`irrelevant_answer` 4 条、`invalid_input` 3 条。

这说明项目不只是统计失败数量，还能把失败转成可分析、可导出、可 Replay、可回归的资产。面试时我会强调：Badcase 的价值不是“有 17 个错误”，而是“这些错误已经被结构化沉淀，可以持续回归”。

### 12. CI 通过说明什么？

面试时可以直接说：

CI 通过说明项目的基础质量门禁是可自动执行的。GitHub Actions 里会在 Ubuntu 上安装 uv 和 Python，执行 `uv sync --locked`，然后跑 ruff 和 pytest。

它不能说明真实模型效果好，因为 CI 默认不调用真实 OpenAI、ChromaDB 或 embedding；它说明的是代码质量、接口契约、评测 runner、Badcase 服务、Agent metrics 和回归测试这套工程链路能稳定跑通。

### 13. 后续接真实模型应该怎么扩展？

面试时可以直接说：

我会保留 mock provider，同时新增 real provider。第一步把 `LLMQAService.ask()` 抽成 provider adapter，根据配置选择 mock 或真实 OpenAI。第二步把 mock context 替换成真实 RAG retriever，接 embedding、向量库和 reranker。第三步扩展指标，比如 context recall、context precision、faithfulness、answer relevancy、citation correctness 和 LLM-as-a-Judge。

但我不会让真实模型替代所有测试。CI 仍然跑 deterministic mock，真实模型评测可以作为 nightly job、手动评测或者发布前质量门禁。

### 14. 为什么 `source_hit_rate=1.0` 不能说明 RAG 完美？

面试时可以直接说：

因为当前 retriever 是 mock，它稳定返回 `mock_policy.md`。所以 `source_hit_rate=1.0` 只说明样本里的 `expected_source` 在当前 mock context 里都命中了。

真实 RAG 还要看召回是否完整、context 是否相关、答案是否忠实引用、是否有噪声文档、top-k 是否合理。这个项目当前验证的是 source-hit 指标链路，不是生产级 RAG 效果。

### 15. Agent 评测和普通 QA 评测有什么区别？

面试时可以直接说：

普通 QA 评测主要看最终答案和来源命中。Agent 评测还要看过程，比如有没有调用工具、工具名对不对、检索轨迹是什么、reasoning trace 是否符合预期、有没有超时。

这个区别很重要，因为 Agent 可能最后说出一个看似合理的答案，但它其实跳过了应该调用的工具，或者调用了错误工具。只看 final answer 会漏掉这类过程问题。

## 项目核心闭环

面试时可以直接说：

这条闭环可以按文件和接口讲清楚：

```text
evals/datasets/rag_qa_sample.jsonl
  -> POST /api/v1/eval/ask 或 app.services.eval_runner
  -> app.services.llm_qa.LLMQAService
  -> app.services.metrics.evaluate_qa_result
  -> evals/reports/latest_report.json
  -> app.services.badcase.BadcaseService
  -> GET /api/v1/badcases / replay / export
  -> evals/badcases/badcases.jsonl
  -> backend/tests/test_badcase_regression.py
  -> .github/workflows/ci.yml
```

如果是 Agent 链路，可以这样讲：

```text
POST /api/v1/agent/eval
  -> AgentQAService.run_eval
  -> decide_tool
  -> mock_retriever 或 skip_tool
  -> tool_calls / retrieval_trace / reasoning_trace
  -> evaluate_agent_result
  -> AgentEvalResponse
```

## 面试官最可能追问的 10 个细节

1. `latest_report.json` 里除了总数和通过率，还有哪些字段？
   可以答：有 `avg_latency_ms`、`source_hit_rate`、`badcase_count`、`badcase_type_distribution`、`top_failed_cases`、`badcases`、`results` 和 `config`。

2. `failed_metrics` 是怎么来的？
   可以答：`evaluate_qa_result()` 会检查关键词分数和 `source_hit_at_k`，低于阈值就加入 `answer_keyword_recall`，来源没命中就加入 `source_hit_at_k`。

3. `badcase_type` 是人工写的还是自动推断的？
   可以答：样本里有 `badcase_type` 就优先使用；没有的话，runner 会根据失败指标推断，比如只有关键词失败就是 `keyword_miss`，只有来源失败就是 `source_miss`。

4. 为什么 JSONL 比数据库更适合这个 MVP？
   可以答：MVP 阶段重点是可复现和易审查，JSONL 一行一个 case，方便 diff、追加和 pytest 参数化。数据库适合后续做多轮历史、负责人、状态流转和看板。

5. pytest 回归为什么不是直接读仓库里的 badcases.jsonl？
   可以答：当前测试里用 `tmp_path` 构造临时 JSONL，是为了让测试不依赖绝对路径和仓库状态，更稳定；真实回归可以再加一组读取导出文件的集成测试。

6. `min_keyword_score=1.0` 为什么这么严格？
   可以答：当前是确定性规则评测，要求 expected keywords 全命中，便于发现漏答。真实模型接入后可以按场景调阈值，或者加入语义相似度和 judge 分。

7. 当前 Agent 为什么用规则判断是否调用 retriever？
   可以答：这是为了让 Agent 评测合同先稳定下来。规则触发可以稳定覆盖 tool call、skip tool、source hit 和 trace 检查；后续可以替换成真实 Agent runtime。

8. 真实 OpenAI 接入后怎么避免 CI 变慢或不稳定？
   可以答：mock 仍作为 CI 默认路径；真实模型评测通过配置开启，可以放到手动 workflow、nightly job 或发布前质量门禁，并对 judge 结果做缓存或快照。

9. 这个项目有没有真正的 RAG 模块基础？
   可以答：仓库里有 RAG 相关服务目录，包括 documents、ingestion、embeddings、retrieval、vectorstore、reranker 等；但作品集评测主线默认没有启动真实 ChromaDB 和 embedding，而是用 mock context 保证稳定。

10. 如果让你继续做一周，你最优先补什么？
    可以答：我会先补真实 provider 的配置开关和接口抽象，然后做批量 Agent eval runner，最后加 HTML/Markdown 报告和质量阈值门禁，让 CI 能根据 pass_rate 或 badcase_count 判断是否放行。

## 项目中最值得背的 10 个问答

1. 问：这个项目一句话是什么？
   答：它是一个把 LLM/RAG/Agent 质量问题变成可评测、可分析、可 Replay、可回归、可 CI 验证的质量评测 MVP。

2. 问：核心闭环是什么？
   答：JSONL 评测集 -> QA/Agent 接口 -> 自动评分 -> `latest_report.json` -> Badcase -> Replay/Export -> pytest 回归 -> GitHub Actions CI。

3. 问：为什么不用真实模型做默认路径？
   答：默认路径要服务 CI 和回归，所以必须稳定、低成本、无 API key、无网络依赖；真实模型应该作为可选 provider 接入。

4. 问：RAG 做到了什么程度？
   答：当前是 mock RAG context，验证 `expected_source`、`source_hit_at_k` 和 `source_hit_rate` 的评测链路；不把它包装成真实向量检索效果。

5. 问：Agent 做到了什么程度？
   答：当前有确定性 Agent eval，能检查工具调用、工具名、检索轨迹、reasoning trace、关键词召回和超时；不是完整真实 Agent 框架效果评测。

6. 问：`pass_rate=0.66` 怎么解释？
   答：50 条里 33 条通过、17 条失败，说明评测链路能区分通过和失败，也说明数据集有意包含风险和失败样本，不是刷 100%。

7. 问：17 条 Badcase 的价值是什么？
   答：它们是失败样本的结构化沉淀，可以查询、Replay、导出，并进入 pytest 参数化回归，防止问题反复出现。

8. 问：这个项目和测试开发有什么关系？
   答：它把 LLM 输出质量按测试开发思路工程化：设计数据、自动评分、分类失败、固化回归、接入 CI。

9. 问：这个项目和 AI 开发有什么关系？
   答：它覆盖 LLM 应用接口、RAG source hit、Agent tool call 和 provider 可替换设计，体现的是大模型应用落地后的质量保障能力。

10. 问：后续怎么接真实模型？
    答：抽 provider，保留 mock，新增 OpenAI provider；再接真实 retriever、embedding、向量库、reranker；最后扩展语义指标和 LLM-as-a-Judge。

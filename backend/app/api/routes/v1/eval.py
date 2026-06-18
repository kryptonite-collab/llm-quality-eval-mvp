from fastapi import APIRouter

from app.schemas.eval import EvalAskRequest, EvalAskResponse
from app.services.agent_runner import build_agent_runner
from app.services.chroma_retriever import query_policy_contexts
from app.services.llm_qa import LLMQAService

router = APIRouter(prefix="/eval", tags=["eval"])


@router.post("/ask", response_model=EvalAskResponse)
async def ask_eval(request: EvalAskRequest) -> EvalAskResponse:
    if request.mode == "agent":
        runner = build_agent_runner()
        result = runner.run_case(
            {
                "case_id": "api-agent-request",
                "task": request.question,
            }
        )
        return EvalAskResponse(
            answer=result["final_answer"],
            contexts=result["retrieval_trace"],
            latency_ms=result["latency_ms"],
            model=result["model"],
            provider=result["provider"],
            prompt_version=request.prompt_version or "baseline",
            mode="agent",
            tool_calls=result["tool_calls"],
            retrieval_trace=result["retrieval_trace"],
            reasoning_trace=result["reasoning_trace"],
            final_answer=result["final_answer"],
        )

    service = LLMQAService(
        provider=request.provider,
        prompt_version=request.prompt_version,
    )

    if request.mode == "rag":
        contexts = query_policy_contexts(
            question=request.question,
            top_k=request.top_k,
        )
        provider_result = service.provider.generate(
            question=request.question,
            contexts=contexts,
            prompt_template=service.prompt_template,
        )
        return EvalAskResponse(
            answer=provider_result["answer"],
            contexts=contexts,
            latency_ms=provider_result["latency_ms"],
            model=provider_result["model"],
            provider=provider_result["provider"],
            prompt_version=service.prompt_version,
            mode="rag",
        )

    result = service.ask(
        question=request.question,
        use_rag=request.use_rag,
        top_k=request.top_k,
    )
    return EvalAskResponse(
        **result,
        mode="qa",
    )

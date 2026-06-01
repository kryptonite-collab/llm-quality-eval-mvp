from fastapi import APIRouter

from app.schemas.eval import EvalAskRequest, EvalAskResponse
from app.services.llm_qa import LLMQAService

router = APIRouter(prefix="/eval", tags=["eval"])


@router.post("/ask", response_model=EvalAskResponse)
async def ask_eval(request: EvalAskRequest) -> EvalAskResponse:
    service = LLMQAService()
    result = service.ask(
        question=request.question,
        use_rag=request.use_rag,
        top_k=request.top_k,
    )
    return EvalAskResponse(**result)
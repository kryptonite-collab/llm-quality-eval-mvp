from fastapi import APIRouter

from app.schemas.agent_eval import AgentEvalRequest, AgentEvalResponse
from app.services.agent_qa import AgentQAService

router = APIRouter(prefix="/agent", tags=["agent-eval"])


@router.post("/eval", response_model=AgentEvalResponse)
async def evaluate_agent(request: AgentEvalRequest) -> AgentEvalResponse:
    service = AgentQAService()
    result = service.run_eval(
        question=request.question,
        expected_tool=request.expected_tool,
        expected_source=request.expected_source,
        expected_keywords=request.expected_keywords,
        max_steps=request.max_steps,
        timeout_ms=request.timeout_ms,
    )
    return AgentEvalResponse(**result)

from fastapi import APIRouter, HTTPException

from app.schemas.badcase import (
    BadcaseExportResponse,
    BadcaseItem,
    BadcaseListResponse,
    BadcaseReplayResponse,
)
from app.services.badcase import BadcaseService

router = APIRouter(prefix="/badcases", tags=["badcases"])


@router.get("", response_model=BadcaseListResponse)
async def list_badcases() -> BadcaseListResponse:
    service = BadcaseService()
    items = [BadcaseItem(**item) for item in service.list_badcases()]

    return BadcaseListResponse(
        total=len(items),
        items=items,
    )


@router.get("/{badcase_id}", response_model=BadcaseItem)
async def get_badcase(badcase_id: str) -> BadcaseItem:
    service = BadcaseService()
    badcase = service.get_badcase(badcase_id)

    if badcase is None:
        raise HTTPException(status_code=404, detail="Badcase not found")

    return BadcaseItem(**badcase)


@router.post("/{badcase_id}/replay", response_model=BadcaseReplayResponse)
async def replay_badcase(badcase_id: str) -> BadcaseReplayResponse:
    service = BadcaseService()
    result = service.replay_badcase(badcase_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Badcase not found")

    return BadcaseReplayResponse(**result)


@router.post("/export", response_model=BadcaseExportResponse)
async def export_badcases() -> BadcaseExportResponse:
    service = BadcaseService()
    result = service.export_badcases()

    return BadcaseExportResponse(**result)

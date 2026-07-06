from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.core.response import success_response
from app.services.training import TrainingService

router = APIRouter(prefix="/training", tags=["Training"])


class TrainingRequest(BaseModel):
    league_ids: list[int] | None = None
    season: int | None = None
    max_pages: int = Field(default=3, ge=1, le=20)


@router.post("/run")
async def run_training(data: TrainingRequest):
    service = TrainingService()
    result = await service.run_full_pipeline(
        league_ids=data.league_ids,
        season=data.season,
        max_pages=data.max_pages,
    )
    message = "Training completed" if result.get("success") else result.get("message", "Failed")
    return success_response(result, message)


@router.post("/collect")
async def collect_training_data(
    league_ids: list[int] | None = Query(None),
    season: int | None = Query(None),
    max_pages: int = Query(3, ge=1, le=20),
):
    service = TrainingService()
    result = await service.collect_data(
        league_ids=league_ids,
        season=season,
        max_pages=max_pages,
    )
    return success_response(result, f"Collected {result['samples_collected']} samples")


@router.get("/status")
async def get_training_status():
    status = TrainingService().get_training_status()
    return success_response(status)

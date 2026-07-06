from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import success_response
from app.database.session import get_db
from app.schemas.domain import MonitorMatchRequest
from app.services.match import MatchService

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.get("/live")
async def get_live_matches(db: AsyncSession = Depends(get_db)):
    matches = await MatchService(db).get_live_matches()
    return success_response([m.model_dump() for m in matches])


@router.get("/{match_id}")
async def get_match_detail(match_id: int, db: AsyncSession = Depends(get_db)):
    match = await MatchService(db).get_match_detail(match_id)
    return success_response(match.model_dump())


@router.post("/monitor")
async def start_monitoring(data: MonitorMatchRequest, db: AsyncSession = Depends(get_db)):
    match = await MatchService(db).start_monitoring(data.match_id)
    return success_response(match.model_dump(), "Monitoring started")


@router.post("/{match_id}/refresh")
async def refresh_match(match_id: int, db: AsyncSession = Depends(get_db)):
    service = MatchService(db)
    await service.refresh_match_data(match_id)
    match = await service.get_match_detail(match_id)
    return success_response(match.model_dump(), "Match data refreshed")


@router.post("/monitor/stop")
async def stop_monitoring(data: MonitorMatchRequest, db: AsyncSession = Depends(get_db)):
    match = await MatchService(db).stop_monitoring(data.match_id)
    return success_response(match.model_dump(), "Monitoring stopped")


@router.post("/sync")
async def sync_live_matches(db: AsyncSession = Depends(get_db)):
    matches = await MatchService(db).sync_live_matches()
    return success_response(
        {"count": len(matches)},
        f"Synced {len(matches)} live matches",
    )

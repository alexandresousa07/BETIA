from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import success_response
from app.database.session import get_db
from app.services.match import MatchService

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("")
async def get_recommendations(
    match_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    recs = await MatchService(db).get_recommendations(match_id)
    return success_response([r.model_dump() for r in recs])

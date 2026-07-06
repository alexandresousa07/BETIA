from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import success_response
from app.database.session import get_db
from app.services.odds import OddsService
from app.services.training import TrainingService

router = APIRouter(prefix="/odds", tags=["Odds"])


@router.post("/match-all")
async def match_all_odds(db: AsyncSession = Depends(get_db)):
    result = await OddsService(db).match_all_live()
    await db.commit()
    return success_response(result, f"Matched {result['matched']}/{result['total']} fixtures")


@router.post("/sync/{match_id}")
async def sync_match_odds(match_id: int, db: AsyncSession = Depends(get_db)):
    from app.repositories.domain import MatchRepository

    repo = MatchRepository(db)
    match = await repo.get_by_id(match_id)
    if not match:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Match not found")

    service = OddsService(db)
    odds, odds_map = await service.sync_odds_for_match(match)
    await db.commit()

    return success_response({
        "odds_count": len(odds),
        "odds_event_id": match.odds_event_id,
        "odds_sport_key": match.odds_sport_key,
        "match_confidence": match.odds_match_confidence,
        "markets_mapped": odds_map,
    })


@router.get("/status/{match_id}")
async def get_odds_status(match_id: int, db: AsyncSession = Depends(get_db)):
    from app.repositories.domain import MatchRepository

    repo = MatchRepository(db)
    match = await repo.get_by_id(match_id)
    if not match:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Match not found")

    odds_map = await OddsService(db).get_odds_map(match_id)
    return success_response({
        "match_id": match_id,
        "odds_event_id": match.odds_event_id,
        "odds_sport_key": match.odds_sport_key,
        "match_confidence": match.odds_match_confidence,
        "markets_available": odds_map,
    })

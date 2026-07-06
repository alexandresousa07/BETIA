from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.core.response import success_response
from app.database.session import get_db
from app.services.league_sync import LeagueSyncService

router = APIRouter(prefix="/competitions", tags=["Competitions"])


@router.get("")
async def list_competitions(
    country_code: str | None = Query(None),
    status: str | None = Query("active"),
    league_type: str | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    service = LeagueSyncService(db)
    competitions = await service.list_competitions(
        country_code=country_code,
        status=status,
        league_type=league_type,
        search=search,
        skip=skip,
        limit=limit,
    )
    return success_response(competitions)


@router.get("/countries")
async def list_countries(db: AsyncSession = Depends(get_db)):
    from app.repositories.competition import CompetitionRepository

    countries = await CompetitionRepository(db).list_countries()
    return success_response(countries)


@router.post("/sync")
async def sync_competitions(
    season: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = LeagueSyncService(db)
    result = await service.sync_all_leagues(season=season)
    await db.commit()
    return success_response(result, f"Synced {result['fetched']} leagues from API-Football")


@router.get("/{competition_id}")
async def get_competition(competition_id: int, db: AsyncSession = Depends(get_db)):
    service = LeagueSyncService(db)
    competition = await service.get_competition(competition_id)
    if not competition:
        raise NotFoundException("Competition not found")
    return success_response(competition)


@router.post("/{competition_id}/sync-matches")
async def sync_competition_matches(
    competition_id: int,
    date: str | None = Query(None, description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    service = LeagueSyncService(db)
    result = await service.sync_competition_fixtures(competition_id, date=date)
    await db.commit()
    return success_response(result, f"Synced {result['fixtures_synced']} fixtures")

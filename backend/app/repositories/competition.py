from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.clients import APIFootballClient
from app.integrations.league_normalizer import country_code_to_flag_emoji, normalize_league
from app.models.entities import Competition
from app.repositories.base import BaseRepository


class CompetitionRepository(BaseRepository[Competition]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Competition)

    async def get_by_external_id(self, external_id: int) -> Competition | None:
        result = await self.session.execute(
            select(Competition).where(Competition.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, data: dict) -> Competition:
        competition = await self.get_by_external_id(data["external_id"])
        now = datetime.now(timezone.utc)

        if competition:
            competition.name = data["name"]
            competition.country = data.get("country")
            competition.country_code = data.get("country_code")
            competition.country_flag_url = data.get("country_flag_url")
            competition.logo_url = data.get("logo_url")
            competition.season = data.get("season")
            competition.season_year = data.get("season_year")
            competition.league_type = data.get("league_type")
            competition.status = data.get("status", "active")
            if data.get("odds_sport_key"):
                competition.odds_sport_key = data["odds_sport_key"]
            competition.synced_at = now
            return await self.update(competition)

        competition = Competition(
            external_id=data["external_id"],
            name=data["name"],
            country=data.get("country"),
            country_code=data.get("country_code"),
            country_flag_url=data.get("country_flag_url"),
            logo_url=data.get("logo_url"),
            season=data.get("season"),
            season_year=data.get("season_year"),
            league_type=data.get("league_type"),
            status=data.get("status", "active"),
            odds_sport_key=data.get("odds_sport_key"),
            synced_at=now,
        )
        return await self.create(competition)

    async def list_competitions(
        self,
        country_code: str | None = None,
        status: str | None = None,
        league_type: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Competition]:
        query = select(Competition).order_by(Competition.country, Competition.name)

        if country_code:
            query = query.where(Competition.country_code == country_code)
        if status:
            query = query.where(Competition.status == status)
        if league_type:
            query = query.where(Competition.league_type == league_type)
        if search:
            term = f"%{search}%"
            query = query.where(
                or_(Competition.name.ilike(term), Competition.country.ilike(term))
            )

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_competitions(self, status: str | None = None) -> int:
        query = select(func.count(Competition.id))
        if status:
            query = query.where(Competition.status == status)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def list_countries(self) -> list[dict]:
        result = await self.session.execute(
            select(Competition.country_code, Competition.country, func.count(Competition.id))
            .where(Competition.country_code.isnot(None))
            .group_by(Competition.country_code, Competition.country)
            .order_by(Competition.country)
        )
        return [
            {
                "country_code": row[0],
                "country": row[1],
                "count": row[2],
                "flag_emoji": country_code_to_flag_emoji(row[0]),
            }
            for row in result.all()
        ]

    async def get_active_league_external_ids(self, league_type: str = "League") -> list[int]:
        result = await self.session.execute(
            select(Competition.external_id)
            .where(Competition.status == "active", Competition.league_type == league_type)
            .order_by(Competition.name)
        )
        ids = [row[0] for row in result.all()]
        return ids

    async def get_odds_sport_key(self, external_id: int) -> str | None:
        result = await self.session.execute(
            select(Competition.odds_sport_key).where(Competition.external_id == external_id)
        )
        return result.scalar_one_or_none()

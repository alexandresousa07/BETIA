from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.clients import APIFootballClient
from app.integrations.league_normalizer import country_code_to_flag_emoji, normalize_league
from app.integrations.normalizer import normalize_fixture
from app.repositories.competition import CompetitionRepository
from app.services.match import MatchService


class LeagueSyncService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = CompetitionRepository(session)
        self.api = APIFootballClient()
        self.match_service = MatchService(session)

    async def sync_all_leagues(self, season: int | None = None) -> dict:
        season = season or datetime.now(timezone.utc).year
        raw_leagues = await self.api.get_all_leagues(season=season)

        created = 0
        updated = 0

        for item in raw_leagues:
            data = normalize_league(item)
            if not data.get("external_id"):
                continue

            existing = await self.repo.get_by_external_id(data["external_id"])
            await self.repo.upsert(data)

            if existing:
                updated += 1
            else:
                created += 1

        total = await self.repo.count_competitions()
        active = await self.repo.count_competitions(status="active")

        return {
            "season": season,
            "fetched": len(raw_leagues),
            "created": created,
            "updated": updated,
            "total_in_db": total,
            "active_in_db": active,
        }

    async def list_competitions(
        self,
        country_code: str | None = None,
        status: str | None = "active",
        league_type: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict]:
        competitions = await self.repo.list_competitions(
            country_code=country_code,
            status=status,
            league_type=league_type,
            search=search,
            skip=skip,
            limit=limit,
        )
        return [self._to_response(c) for c in competitions]

    async def get_competition(self, competition_id: int) -> dict | None:
        competition = await self.repo.get_by_id(competition_id)
        if not competition:
            return None
        return self._to_response(competition)

    async def sync_competition_fixtures(
        self,
        competition_id: int,
        date: str | None = None,
    ) -> dict:
        from app.core.exceptions import NotFoundException

        competition = await self.repo.get_by_id(competition_id)
        if not competition or not competition.season_year:
            raise NotFoundException("Competition not found or missing season")

        fixtures = await self.api.get_fixtures_by_league(
            league_id=competition.external_id,
            season=competition.season_year,
            date=date,
        )

        synced = []
        for fixture_data in fixtures:
            normalized = normalize_fixture(fixture_data)
            match = await self.match_service._upsert_match(normalized)
            synced.append(match.id)

        return {
            "competition_id": competition_id,
            "competition_name": competition.name,
            "fixtures_synced": len(synced),
            "match_ids": synced,
        }

    def _to_response(self, competition) -> dict:
        return {
            "id": competition.id,
            "external_id": competition.external_id,
            "name": competition.name,
            "country": competition.country,
            "country_code": competition.country_code,
            "country_flag_url": competition.country_flag_url,
            "flag_emoji": country_code_to_flag_emoji(competition.country_code),
            "logo_url": competition.logo_url,
            "season": competition.season,
            "season_year": competition.season_year,
            "league_type": competition.league_type,
            "status": competition.status,
            "odds_sport_key": competition.odds_sport_key,
            "synced_at": competition.synced_at.isoformat() if competition.synced_at else None,
        }

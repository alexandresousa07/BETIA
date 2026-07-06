from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import Match, MatchStatus, Recommendation, Team, User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()


class MatchRepository(BaseRepository[Match]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Match)

    async def get_by_external_id(self, external_id: int) -> Match | None:
        result = await self.session.execute(
            select(Match).where(Match.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def get_live_matches(self) -> list[Match]:
        result = await self.session.execute(
            select(Match)
            .where(Match.status == MatchStatus.LIVE)
            .options(
                selectinload(Match.home_team),
                selectinload(Match.away_team),
                selectinload(Match.competition),
            )
            .order_by(Match.kickoff_at.desc())
        )
        return list(result.scalars().all())

    async def get_monitored_matches(self) -> list[Match]:
        result = await self.session.execute(
            select(Match)
            .where(Match.is_monitored.is_(True))
            .options(
                selectinload(Match.home_team),
                selectinload(Match.away_team),
                selectinload(Match.competition),
            )
        )
        return list(result.scalars().all())

    async def get_match_detail(self, match_id: int) -> Match | None:
        result = await self.session.execute(
            select(Match)
            .where(Match.id == match_id)
            .options(
                selectinload(Match.home_team),
                selectinload(Match.away_team),
                selectinload(Match.competition),
                selectinload(Match.live_stats),
                selectinload(Match.events),
                selectinload(Match.odds),
                selectinload(Match.predictions),
                selectinload(Match.recommendations),
            )
        )
        return result.scalar_one_or_none()


class TeamRepository(BaseRepository[Team]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Team)

    async def get_by_external_id(self, external_id: int) -> Team | None:
        result = await self.session.execute(
            select(Team).where(Team.external_id == external_id)
        )
        return result.scalar_one_or_none()


class RecommendationRepository(BaseRepository[Recommendation]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Recommendation)

    async def get_active_by_match(self, match_id: int) -> list[Recommendation]:
        result = await self.session.execute(
            select(Recommendation)
            .where(Recommendation.match_id == match_id, Recommendation.is_active.is_(True))
            .order_by(Recommendation.confidence_score.desc())
        )
        return list(result.scalars().all())

    async def get_recent(self, limit: int = 50) -> list[Recommendation]:
        result = await self.session.execute(
            select(Recommendation)
            .where(Recommendation.is_active.is_(True))
            .order_by(Recommendation.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

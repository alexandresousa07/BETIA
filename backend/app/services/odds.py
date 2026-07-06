from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.integrations.clients import APIFootballClient, TheOddsAPIClient
from app.integrations.league_mapping import LEAGUE_TO_ODDS_SPORT
from app.integrations.normalizer import build_odds_map_for_markets, normalize_odds_event
from app.integrations.odds_matcher import OddsMatcher, OddsMatchResult
from app.models.entities import Match, Odd
from app.repositories.domain import MatchRepository
from app.services.cache import cache_service


class OddsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.match_repo = MatchRepository(session)
        self.api_football = APIFootballClient()
        self.odds_client = TheOddsAPIClient()
        self.matcher = OddsMatcher()

    async def _fetch_odds_events_for_leagues(self, league_ids: set[int]) -> list[dict]:
        sport_keys = list({
            LEAGUE_TO_ODDS_SPORT[lid]
            for lid in league_ids
            if lid in LEAGUE_TO_ODDS_SPORT
        })
        if not sport_keys:
            sport_keys = list(set(LEAGUE_TO_ODDS_SPORT.values()))[:5]

        cache_key = f"odds_events:{':'.join(sorted(sport_keys))}"
        cached = await cache_service.get(cache_key)
        if cached:
            return cached

        events = await self.odds_client.get_odds_multi_sport(sport_keys)
        await cache_service.set(cache_key, events, ttl=120)
        return events

    async def match_and_link_odds(self, match: Match) -> OddsMatchResult | None:
        await self.session.refresh(match, ["home_team", "away_team", "competition"])

        league_id = match.competition.external_id if match.competition else None
        sport_key = (
            match.competition.odds_sport_key
            if match.competition and match.competition.odds_sport_key
            else self.matcher.get_sport_key_for_league(league_id)
        )

        if match.odds_event_id and match.odds_sport_key:
            return OddsMatchResult(
                odds_event_id=match.odds_event_id,
                odds_sport_key=match.odds_sport_key,
                home_team_odds=match.home_team.name,
                away_team_odds=match.away_team.name,
                confidence=match.odds_match_confidence or 1.0,
            )

        events = await self._fetch_odds_events_for_leagues({league_id} if league_id else set())

        result = self.matcher.match_fixture(
            home_team=match.home_team.name,
            away_team=match.away_team.name,
            league_external_id=league_id,
            kickoff_at=match.kickoff_at,
            odds_events=events,
            sport_key=sport_key,
        )

        if result:
            match.odds_event_id = result.odds_event_id
            match.odds_sport_key = result.odds_sport_key
            match.odds_match_confidence = result.confidence
            match.updated_at = datetime.now(timezone.utc)
            await self.match_repo.update(match)

        return result

    async def sync_odds_for_match(self, match: Match) -> tuple[list[Odd], dict[str, float]]:
        link = await self.match_and_link_odds(match)
        if not link:
            return [], {}

        try:
            event_data = await self.odds_client.get_event_odds(
                link.odds_sport_key, link.odds_event_id
            )
        except Exception:
            events = await self._fetch_odds_events_for_leagues(
                {match.competition.external_id} if match.competition else set()
            )
            event_data = next((e for e in events if e.get("id") == link.odds_event_id), None)
            if not event_data:
                return [], {}

        normalized = normalize_odds_event(event_data)
        odds_map = build_odds_map_for_markets(normalized)

        await self.session.execute(delete(Odd).where(Odd.match_id == match.id))

        saved: list[Odd] = []
        for item in normalized:
            odd = Odd(
                match_id=match.id,
                bookmaker=item["bookmaker"],
                market=item["market"],
                selection=item["selection"],
                odds_value=item["odds_value"],
                implied_probability=item.get("implied_probability"),
            )
            self.session.add(odd)
            saved.append(odd)

        await self.session.flush()
        return saved, odds_map

    async def match_all_live(self) -> dict:
        matches = await self.match_repo.get_live_matches()

        league_ids = {
            m.competition.external_id
            for m in matches
            if m.competition and m.competition.external_id
        }
        events = await self._fetch_odds_events_for_leagues(league_ids)

        matched = 0
        for match in matches:
            await self.session.refresh(match, ["home_team", "away_team", "competition"])
            league_id = match.competition.external_id if match.competition else None
            result = self.matcher.match_fixture(
                home_team=match.home_team.name,
                away_team=match.away_team.name,
                league_external_id=league_id,
                kickoff_at=match.kickoff_at,
                odds_events=events,
            )
            if result:
                match.odds_event_id = result.odds_event_id
                match.odds_sport_key = result.odds_sport_key
                match.odds_match_confidence = result.confidence
                matched += 1

        await self.session.flush()
        return {"total": len(matches), "matched": matched}

    async def get_odds_map(self, match_id: int) -> dict[str, float]:
        result = await self.session.execute(
            select(Odd).where(Odd.match_id == match_id)
        )
        odds = result.scalars().all()
        if not odds:
            return {}

        normalized = [
            {
                "market": o.market,
                "selection": o.selection,
                "odds_value": o.odds_value,
            }
            for o in odds
        ]
        return build_odds_map_for_markets(normalized)

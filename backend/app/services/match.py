from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.integrations.clients import APIFootballClient, TheOddsAPIClient
from app.integrations.normalizer import normalize_fixture, normalize_odds, normalize_statistics
from app.ml.consensus.engine import ConsensusEngine
from app.ml.features.engineer import FeatureEngineer
from app.ml.prediction.model_registry import get_enhanced_predictors
from app.models.entities import (
    Competition,
    LiveStat,
    Match,
    MatchStatus,
    Odd,
    Prediction,
    Recommendation,
    Team,
)
from app.repositories.domain import MatchRepository, RecommendationRepository, TeamRepository
from app.schemas.domain import MatchDetailResponse, MatchResponse, RecommendationResponse
from app.services.cache import cache_service
from app.services.odds import OddsService


class MatchService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.match_repo = MatchRepository(session)
        self.team_repo = TeamRepository(session)
        self.rec_repo = RecommendationRepository(session)
        self.api_football = APIFootballClient()
        self.odds_client = TheOddsAPIClient()
        self.feature_engineer = FeatureEngineer()
        self.consensus_engine = ConsensusEngine(predictors=get_enhanced_predictors())
        self.odds_service = OddsService(session)

    async def sync_live_matches(self) -> list[Match]:
        cached = await cache_service.get("live_matches")
        if cached:
            return await self.match_repo.get_live_matches()

        fixtures = await self.api_football.get_live_fixtures()
        synced = []

        for fixture_data in fixtures:
            normalized = normalize_fixture(fixture_data)
            match = await self._upsert_match(normalized)
            synced.append(match)

        if synced:
            await self.odds_service.match_all_live()

        await cache_service.set("live_matches", [m.id for m in synced], ttl=30)
        return synced

    async def get_live_matches(self) -> list[MatchResponse]:
        matches = await self.match_repo.get_live_matches()
        if not matches:
            matches = await self.sync_live_matches()
        return [MatchResponse.model_validate(m) for m in matches]

    async def get_match_detail(self, match_id: int) -> MatchDetailResponse:
        match = await self.match_repo.get_match_detail(match_id)
        if not match:
            raise NotFoundException("Match not found")
        return MatchDetailResponse.model_validate(match)

    async def start_monitoring(self, match_id: int) -> MatchDetailResponse:
        match = await self.match_repo.get_by_id(match_id)
        if not match:
            raise NotFoundException("Match not found")
        match.is_monitored = True
        await self.match_repo.update(match)
        await self.refresh_match_data(match_id)
        return await self.get_match_detail(match_id)

    async def refresh_match_data(self, match_id: int) -> dict:
        match = await self.match_repo.get_by_id(match_id)
        if not match:
            raise NotFoundException("Match not found")
        try:
            return await self.update_match_live_data(match)
        except Exception as exc:
            return {"error": str(exc), "partial": True}

    async def stop_monitoring(self, match_id: int) -> MatchResponse:
        match = await self.match_repo.get_by_id(match_id)
        if not match:
            raise NotFoundException("Match not found")
        match.is_monitored = False
        await self.match_repo.update(match)
        return MatchResponse.model_validate(match)

    async def update_match_live_data(self, match: Match) -> dict:
        fixture = await self.api_football.get_fixture_by_id(match.external_id)
        if not fixture:
            return {}

        normalized = normalize_fixture(fixture)
        match.status = normalized["status"]
        match.minute = normalized["minute"]
        match.home_score = normalized["home_score"]
        match.away_score = normalized["away_score"]
        match.updated_at = datetime.now(timezone.utc)
        await self.match_repo.update(match)

        stats_data = await self.api_football.get_fixture_statistics(match.external_id)
        stats = normalize_statistics(stats_data, match.minute or 0)

        if stats.get("shots_home", 0) + stats.get("shots_away", 0) == 0 and len(stats_data) < 2:
            stats = self._fallback_stats(match, stats)

        live_stat = LiveStat(match_id=match.id, **stats)
        self.session.add(live_stat)
        await self.session.flush()

        await self._sync_events(match)

        _, odds_map = await self.odds_service.sync_odds_for_match(match)

        match_dict = {
            "home_score": match.home_score,
            "away_score": match.away_score,
            "minute": match.minute,
        }

        features = self.feature_engineer.extract(match_dict, stats)
        consensus_results = self.consensus_engine.analyze_all_markets(features, odds_map)

        for result in consensus_results:
            prediction = Prediction(
                match_id=match.id,
                market=result.market,
                probability=result.probability,
                model_name="consensus",
                features_used={"minute": match.minute},
                minute=match.minute or 0,
            )
            self.session.add(prediction)

            recommendation = Recommendation(
                match_id=match.id,
                market=result.market,
                selection=result.selection,
                confidence_score=result.confidence_score,
                confidence_level=result.confidence_level,
                probability=result.probability,
                expected_value=result.expected_value,
                odds_at_creation=odds_map.get(result.market),
                reasons=result.reasons,
                positive_points=result.positive_points,
                negative_points=result.negative_points,
                model_contributions=result.model_contributions,
                explanation=result.explanation,
                minute=match.minute or 0,
            )
            self.session.add(recommendation)

        await self.session.flush()

        await cache_service.publish(f"match:{match.id}", {
            "type": "update",
            "match_id": match.id,
            "stats": stats,
            "recommendations_count": len(consensus_results),
        })

        return {"stats": stats, "recommendations": len(consensus_results)}

    def _fallback_stats(self, match: Match, stats: dict) -> dict:
        """Minimal stats when API statistics are not yet available."""
        minute = match.minute or stats.get("minute", 1) or 1
        return {
            **stats,
            "minute": minute,
            "possession_home": 50.0,
            "possession_away": 50.0,
            "shots_home": match.home_score * 2,
            "shots_away": match.away_score * 2,
            "shots_on_target_home": match.home_score,
            "shots_on_target_away": match.away_score,
            "xg_home": float(match.home_score) * 0.4,
            "xg_away": float(match.away_score) * 0.4,
            "corners_home": 0,
            "corners_away": 0,
            "momentum_home": 30.0 + match.home_score * 10,
            "momentum_away": 30.0 + match.away_score * 10,
            "offensive_pressure_home": 20.0,
            "offensive_pressure_away": 20.0,
            "dangerous_attacks_home": 0,
            "dangerous_attacks_away": 0,
            "attacks_home": 0,
            "attacks_away": 0,
            "fouls_home": 0,
            "fouls_away": 0,
            "yellow_cards_home": 0,
            "yellow_cards_away": 0,
            "red_cards_home": 0,
            "red_cards_away": 0,
            "passes_home": 0,
            "passes_away": 0,
            "crosses_home": 0,
            "crosses_away": 0,
            "offsides_home": 0,
            "offsides_away": 0,
            "defensive_intensity_home": 0.0,
            "defensive_intensity_away": 0.0,
        }

    async def _sync_events(self, match: Match) -> None:
        from sqlalchemy import func, select

        from app.integrations.normalizer import normalize_event
        from app.models.entities import Event

        count_result = await self.session.execute(
            select(func.count(Event.id)).where(Event.match_id == match.id)
        )
        if count_result.scalar_one() > 0:
            return

        try:
            events_data = await self.api_football.get_fixture_events(match.external_id)
        except Exception:
            return

        for event_data in events_data:
            normalized = normalize_event(event_data)
            event = Event(
                match_id=match.id,
                minute=normalized["minute"],
                event_type=normalized["event_type"],
                detail=normalized.get("detail"),
                extra_data=normalized.get("extra_data"),
            )
            self.session.add(event)
        await self.session.flush()

    async def _upsert_match(self, data: dict) -> Match:
        match = await self.match_repo.get_by_external_id(data["external_id"])

        home_team = await self._upsert_team(data["home_team"])
        away_team = await self._upsert_team(data["away_team"])
        competition = await self._upsert_competition(data.get("competition"))

        kickoff = None
        if data.get("kickoff_at"):
            kickoff = datetime.fromisoformat(data["kickoff_at"].replace("Z", "+00:00"))

        if match:
            match.status = data["status"]
            match.minute = data["minute"]
            match.home_score = data["home_score"]
            match.away_score = data["away_score"]
            match.updated_at = datetime.now(timezone.utc)
            return await self.match_repo.update(match)

        match = Match(
            external_id=data["external_id"],
            competition_id=competition.id if competition else None,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            status=data["status"],
            kickoff_at=kickoff,
            minute=data["minute"],
            home_score=data["home_score"],
            away_score=data["away_score"],
            venue=data.get("venue"),
        )
        return await self.match_repo.create(match)

    async def _upsert_team(self, data: dict) -> Team:
        team = await self.team_repo.get_by_external_id(data["external_id"])
        if team:
            return team
        team = Team(
            external_id=data["external_id"],
            name=data["name"],
            logo_url=data.get("logo_url"),
        )
        return await self.team_repo.create(team)

    async def _upsert_competition(self, data: dict | None) -> Competition | None:
        if not data or not data.get("external_id"):
            return None
        from app.repositories.competition import CompetitionRepository

        repo = CompetitionRepository(self.session)
        existing = await repo.get_by_external_id(data["external_id"])
        payload = {
            "external_id": data["external_id"],
            "name": data["name"],
            "country": data.get("country"),
            "country_code": data.get("country_code"),
            "country_flag_url": data.get("country_flag_url"),
            "logo_url": data.get("logo_url"),
            "season": data.get("season"),
            "season_year": int(data["season"]) if data.get("season") and str(data["season"]).isdigit() else None,
            "league_type": data.get("league_type"),
            "status": data.get("status", "active"),
            "odds_sport_key": data.get("odds_sport_key"),
        }
        if not payload.get("odds_sport_key"):
            from app.integrations.league_mapping import LEAGUE_TO_ODDS_SPORT
            payload["odds_sport_key"] = LEAGUE_TO_ODDS_SPORT.get(data["external_id"])
        return await repo.upsert(payload)

    async def get_recommendations(self, match_id: int | None = None) -> list[RecommendationResponse]:
        if match_id:
            recs = await self.rec_repo.get_active_by_match(match_id)
        else:
            recs = await self.rec_repo.get_recent()
        return [RecommendationResponse.model_validate(r) for r in recs]

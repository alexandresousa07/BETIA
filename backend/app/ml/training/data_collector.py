"""Collect historical match data from API-Football for training."""

import asyncio
from typing import Any

from app.integrations.clients import APIFootballClient
from app.integrations.league_mapping import DEFAULT_TRAINING_LEAGUES
from app.integrations.normalizer import normalize_fixture, normalize_statistics
from app.ml.features.engineer import FeatureEngineer
from app.ml.training.labels import compute_market_labels


class HistoricalDataCollector:
    def __init__(self, api_client: APIFootballClient | None = None):
        self.client = api_client or APIFootballClient()
        self.feature_engineer = FeatureEngineer()

    async def collect_league_season(
        self,
        league_id: int,
        season: int,
        max_pages: int = 5,
    ) -> list[dict[str, Any]]:
        fixtures = await self.client.get_all_finished_fixtures(
            league_id, season, max_pages=max_pages
        )
        samples: list[dict[str, Any]] = []

        for fixture_data in fixtures:
            sample = await self._process_fixture(fixture_data)
            if sample:
                samples.append(sample)

        return samples

    async def collect_multiple_leagues(
        self,
        league_ids: list[int] | None = None,
        season: int | None = None,
        max_pages: int = 3,
    ) -> list[dict[str, Any]]:
        from datetime import datetime

        league_ids = league_ids or DEFAULT_TRAINING_LEAGUES
        season = season or datetime.now().year

        all_samples: list[dict[str, Any]] = []
        for league_id in league_ids:
            try:
                samples = await self.collect_league_season(league_id, season, max_pages)
                all_samples.extend(samples)
                await asyncio.sleep(0.5)
            except Exception as exc:
                print(f"Warning: failed to collect league {league_id}: {exc}")

        return all_samples

    async def _process_fixture(self, fixture_data: dict) -> dict[str, Any] | None:
        normalized = normalize_fixture(fixture_data)
        fixture_id = normalized["external_id"]
        if not fixture_id:
            return None

        home_score = normalized["home_score"]
        away_score = normalized["away_score"]

        try:
            stats_data = await self.client.get_fixture_statistics(fixture_id)
        except Exception:
            return None

        if len(stats_data) < 2:
            return None

        stats = normalize_statistics(stats_data, minute=90)
        match_dict = {
            "home_score": home_score,
            "away_score": away_score,
            "minute": 90,
        }

        features = self.feature_engineer.extract(match_dict, stats)
        labels = compute_market_labels(home_score, away_score, stats)

        return {
            "fixture_id": fixture_id,
            "features": features.to_array().tolist(),
            "labels": labels,
            "home_score": home_score,
            "away_score": away_score,
        }

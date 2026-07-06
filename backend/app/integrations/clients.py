from typing import Any

import httpx

from app.config.settings import get_settings

settings = get_settings()


class APIFootballClient:
    """Client for API-Football (api-sports.io)."""

    def __init__(self):
        self.base_url = settings.api_football_base_url
        self.headers = {
            "x-apisports-key": settings.api_football_key,
        }

    async def _request(self, endpoint: str, params: dict[str, Any] | None = None) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/{endpoint}",
                headers=self.headers,
                params=params or {},
            )
            response.raise_for_status()
            return response.json()

    async def get_live_fixtures(self) -> list[dict]:
        data = await self._request("fixtures", {"live": "all"})
        return data.get("response", [])

    async def get_fixture_by_id(self, fixture_id: int) -> dict | None:
        data = await self._request("fixtures", {"id": fixture_id})
        results = data.get("response", [])
        return results[0] if results else None

    async def get_fixture_statistics(self, fixture_id: int) -> list[dict]:
        data = await self._request("fixtures/statistics", {"fixture": fixture_id})
        return data.get("response", [])

    async def get_fixture_events(self, fixture_id: int) -> list[dict]:
        data = await self._request("fixtures/events", {"fixture": fixture_id})
        return data.get("response", [])

    async def get_fixtures_by_date(self, date: str, league_id: int | None = None) -> list[dict]:
        params: dict[str, Any] = {"date": date}
        if league_id:
            params["league"] = league_id
        data = await self._request("fixtures", params)
        return data.get("response", [])

    async def get_team_statistics(self, team_id: int, league_id: int, season: int) -> dict | None:
        data = await self._request(
            "teams/statistics",
            {"team": team_id, "league": league_id, "season": season},
        )
        results = data.get("response", [])
        return results if results else None

    async def get_head_to_head(self, team1_id: int, team2_id: int) -> list[dict]:
        data = await self._request("fixtures/headtohead", {"h2h": f"{team1_id}-{team2_id}"})
        return data.get("response", [])

    async def get_fixtures_by_league_season(
        self,
        league_id: int,
        season: int,
        status: str = "FT",
        page: int = 1,
    ) -> tuple[list[dict], int]:
        data = await self._request(
            "fixtures",
            {"league": league_id, "season": season, "status": status, "page": page},
        )
        paging = data.get("paging", {})
        total_pages = paging.get("total", 1)
        return data.get("response", []), total_pages

    async def get_all_finished_fixtures(
        self, league_id: int, season: int, max_pages: int = 10
    ) -> list[dict]:
        all_fixtures: list[dict] = []
        page = 1
        while page <= max_pages:
            fixtures, total_pages = await self.get_fixtures_by_league_season(
                league_id, season, status="FT", page=page
            )
            all_fixtures.extend(fixtures)
            if page >= total_pages:
                break
            page += 1
        return all_fixtures

    async def get_leagues(
        self,
        season: int | None = None,
        country: str | None = None,
        page: int = 1,
    ) -> tuple[list[dict], int]:
        params: dict[str, Any] = {"page": page}
        if season:
            params["season"] = season
        if country:
            params["country"] = country
        data = await self._request("leagues", params)
        paging = data.get("paging", {})
        total_pages = paging.get("total", 1)
        return data.get("response", []), total_pages

    async def get_all_leagues(
        self,
        season: int | None = None,
        max_pages: int = 50,
    ) -> list[dict]:
        all_leagues: list[dict] = []
        page = 1
        while page <= max_pages:
            leagues, total_pages = await self.get_leagues(season=season, page=page)
            all_leagues.extend(leagues)
            if page >= total_pages:
                break
            page += 1
        return all_leagues

    async def get_fixtures_by_league(
        self,
        league_id: int,
        season: int,
        date: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        params: dict[str, Any] = {"league": league_id, "season": season}
        if date:
            params["date"] = date
        if status:
            params["status"] = status
        data = await self._request("fixtures", params)
        return data.get("response", [])


class TheOddsAPIClient:
    """Client for The Odds API."""

    def __init__(self):
        self.base_url = settings.the_odds_api_base_url
        self.api_key = settings.the_odds_api_key

    async def _request(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        query = {"apiKey": self.api_key, **(params or {})}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}/{endpoint}", params=query)
            response.raise_for_status()
            return response.json()

    async def get_sports(self) -> list[dict]:
        return await self._request("sports")

    async def get_odds(
        self,
        sport: str = "soccer_epl",
        regions: str = "eu",
        markets: str = "h2h,totals,spreads",
    ) -> list[dict]:
        return await self._request(
            f"sports/{sport}/odds",
            {"regions": regions, "markets": markets, "oddsFormat": "decimal"},
        )

    async def get_odds_multi_sport(
        self,
        sport_keys: list[str],
        regions: str = "eu",
        markets: str = "h2h,totals,spreads",
    ) -> list[dict]:
        all_events: list[dict] = []
        for sport in sport_keys:
            try:
                events = await self.get_odds(sport=sport, regions=regions, markets=markets)
                all_events.extend(events)
            except Exception:
                continue
        return all_events

    async def get_event_odds(self, sport: str, event_id: str) -> dict:
        return await self._request(
            f"sports/{sport}/events/{event_id}/odds",
            {"regions": "eu", "markets": "h2h,totals,spreads", "oddsFormat": "decimal"},
        )

"""Normalize league/competition data from API-Football."""

from datetime import datetime, timezone
from typing import Any

from app.integrations.league_mapping import LEAGUE_TO_ODDS_SPORT


def get_current_season(seasons: list[dict]) -> dict | None:
    if not seasons:
        return None
    for season in seasons:
        if season.get("current"):
            return season
    return seasons[0]


def normalize_league(league_data: dict) -> dict[str, Any]:
    league = league_data.get("league", {})
    country = league_data.get("country", {})
    current = get_current_season(league_data.get("seasons", []))

    external_id = league.get("id")
    season_year = current.get("year") if current else None

    status = "active"
    if current is None:
        status = "inactive"
    elif current.get("end"):
        try:
            end_date = datetime.fromisoformat(current["end"])
            if end_date.date() < datetime.now(timezone.utc).date():
                status = "finished"
        except (ValueError, TypeError):
            pass

    return {
        "external_id": external_id,
        "name": league.get("name", "Unknown"),
        "country": country.get("name"),
        "country_code": country.get("code"),
        "country_flag_url": country.get("flag"),
        "logo_url": league.get("logo"),
        "league_type": league.get("type"),
        "season": str(season_year) if season_year else None,
        "season_year": season_year,
        "status": status,
        "odds_sport_key": LEAGUE_TO_ODDS_SPORT.get(external_id),
    }


def country_code_to_flag_emoji(country_code: str | None) -> str:
    if not country_code or len(country_code) != 2:
        return "🌎"
    return "".join(chr(127397 + ord(char)) for char in country_code.upper())

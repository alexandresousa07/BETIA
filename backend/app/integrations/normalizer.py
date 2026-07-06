from typing import Any

from app.models.entities import MatchStatus


STATUS_MAP = {
    "TBD": MatchStatus.SCHEDULED,
    "NS": MatchStatus.SCHEDULED,
    "1H": MatchStatus.LIVE,
    "HT": MatchStatus.LIVE,
    "2H": MatchStatus.LIVE,
    "ET": MatchStatus.LIVE,
    "P": MatchStatus.LIVE,
    "FT": MatchStatus.FINISHED,
    "AET": MatchStatus.FINISHED,
    "PEN": MatchStatus.FINISHED,
    "PST": MatchStatus.POSTPONED,
    "CANC": MatchStatus.CANCELLED,
    "ABD": MatchStatus.CANCELLED,
}

STAT_TYPE_MAP = {
    "Ball Possession": ("possession_home", "possession_away", True),
    "Total Shots": ("shots_home", "shots_away", False),
    "Shots on Goal": ("shots_on_target_home", "shots_on_target_away", False),
    "Corner Kicks": ("corners_home", "corners_away", False),
    "Fouls": ("fouls_home", "fouls_away", False),
    "Yellow Cards": ("yellow_cards_home", "yellow_cards_away", False),
    "Red Cards": ("red_cards_home", "red_cards_away", False),
    "Passes": ("passes_home", "passes_away", False),
    "Offsides": ("offsides_home", "offsides_away", False),
}


def parse_percentage(value: str | int | float | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value).replace("%", "").strip() or 0)


def normalize_fixture(fixture_data: dict) -> dict[str, Any]:
    fixture = fixture_data.get("fixture", {})
    league = fixture_data.get("league", {})
    teams = fixture_data.get("teams", {})
    goals = fixture_data.get("goals", {})
    status = fixture_data.get("fixture", {}).get("status", {})

    return {
        "external_id": fixture.get("id"),
        "competition": {
            "external_id": league.get("id"),
            "name": league.get("name"),
            "country": league.get("country"),
            "logo_url": league.get("logo"),
            "season": str(league.get("season", "")),
        },
        "home_team": {
            "external_id": teams.get("home", {}).get("id"),
            "name": teams.get("home", {}).get("name"),
            "logo_url": teams.get("home", {}).get("logo"),
        },
        "away_team": {
            "external_id": teams.get("away", {}).get("id"),
            "name": teams.get("away", {}).get("name"),
            "logo_url": teams.get("away", {}).get("logo"),
        },
        "status": STATUS_MAP.get(status.get("short", "NS"), MatchStatus.SCHEDULED),
        "kickoff_at": fixture.get("date"),
        "minute": status.get("elapsed"),
        "home_score": goals.get("home") or 0,
        "away_score": goals.get("away") or 0,
        "venue": fixture.get("venue", {}).get("name"),
    }


def normalize_statistics(stats_data: list[dict], minute: int = 0) -> dict[str, Any]:
    result: dict[str, Any] = {"minute": minute}

    if len(stats_data) < 2:
        return result

    home_stats = {s["type"]: s["value"] for s in stats_data[0].get("statistics", [])}
    away_stats = {s["type"]: s["value"] for s in stats_data[1].get("statistics", [])}

    for stat_type, (home_key, away_key, is_pct) in STAT_TYPE_MAP.items():
        home_val = home_stats.get(stat_type)
        away_val = away_stats.get(stat_type)
        if is_pct:
            result[home_key] = parse_percentage(home_val)
            result[away_key] = parse_percentage(away_val)
        else:
            result[home_key] = int(home_val or 0)
            result[away_key] = int(away_val or 0)

    shots_home = result.get("shots_home", 0)
    shots_away = result.get("shots_away", 0)
    sot_home = result.get("shots_on_target_home", 0)
    sot_away = result.get("shots_on_target_away", 0)
    poss_home = result.get("possession_home", 50.0)

    result["xg_home"] = round(sot_home * 0.35 + shots_home * 0.08, 2)
    result["xg_away"] = round(sot_away * 0.35 + shots_away * 0.08, 2)
    result["dangerous_attacks_home"] = int(shots_home * 1.5 + sot_home * 2)
    result["dangerous_attacks_away"] = int(shots_away * 1.5 + sot_away * 2)
    result["attacks_home"] = int(result.get("passes_home", 0) * 0.05 + shots_home * 3)
    result["attacks_away"] = int(result.get("passes_away", 0) * 0.05 + shots_away * 3)
    result["momentum_home"] = round(poss_home * 0.4 + sot_home * 8 + shots_home * 3, 2)
    result["momentum_away"] = round((100 - poss_home) * 0.4 + sot_away * 8 + shots_away * 3, 2)
    result["offensive_pressure_home"] = round(sot_home * 10 + shots_home * 4, 2)
    result["offensive_pressure_away"] = round(sot_away * 10 + shots_away * 4, 2)
    result["defensive_intensity_home"] = round(result.get("fouls_away", 0) * 2 + result.get("offsides_away", 0), 2)
    result["defensive_intensity_away"] = round(result.get("fouls_home", 0) * 2 + result.get("offsides_home", 0), 2)

    return result


def normalize_event(event_data: dict) -> dict[str, Any]:
    return {
        "minute": event_data.get("time", {}).get("elapsed", 0),
        "event_type": event_data.get("type", "unknown").lower(),
        "detail": event_data.get("detail"),
        "team_external_id": event_data.get("team", {}).get("id"),
        "player_name": event_data.get("player", {}).get("name"),
        "extra_data": {
            "assist": event_data.get("assist", {}).get("name"),
            "comments": event_data.get("comments"),
        },
    }


def normalize_odds(odds_data: list[dict], match_external_id: int | None = None) -> list[dict]:
    normalized = []
    for event in odds_data:
        for bookmaker in event.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                for outcome in market.get("outcomes", []):
                    odds_val = outcome.get("price", 0)
                    normalized.append({
                        "match_external_id": match_external_id,
                        "bookmaker": bookmaker.get("title", "unknown"),
                        "market": market.get("key", "unknown"),
                        "selection": outcome.get("name", "unknown"),
                        "point": outcome.get("point"),
                        "odds_value": odds_val,
                        "implied_probability": round(1 / odds_val, 4) if odds_val > 0 else None,
                    })
    return normalized


def build_odds_map_for_markets(normalized_odds: list[dict]) -> dict[str, float]:
    """Map internal market keys to best available decimal odds."""
    from app.integrations.league_mapping import MARKET_TO_ODDS_SELECTION

    odds_map: dict[str, float] = {}

    for market_key, (odds_market, selection) in MARKET_TO_ODDS_SELECTION.items():
        matching = [
            o for o in normalized_odds
            if o["market"] == odds_market and selection.lower() in o["selection"].lower()
        ]
        if matching:
            odds_map[market_key] = min(o["odds_value"] for o in matching if o["odds_value"] > 0)

    return odds_map


def normalize_odds_event(event: dict) -> list[dict]:
    """Normalize a single The Odds API event (with embedded bookmakers)."""
    return normalize_odds([event])

import pytest

from app.integrations.league_normalizer import country_code_to_flag_emoji, normalize_league


def test_normalize_league_active():
    data = {
        "league": {"id": 39, "name": "Premier League", "type": "League", "logo": "https://logo.png"},
        "country": {"name": "England", "code": "GB", "flag": "https://flag.png"},
        "seasons": [{"year": 2024, "start": "2024-08-16", "end": "2025-05-25", "current": True}],
    }
    result = normalize_league(data)

    assert result["external_id"] == 39
    assert result["name"] == "Premier League"
    assert result["country"] == "England"
    assert result["country_code"] == "GB"
    assert result["season_year"] == 2024
    assert result["status"] == "active"
    assert result["league_type"] == "League"
    assert result["odds_sport_key"] == "soccer_epl"


def test_country_code_to_flag_emoji():
    assert country_code_to_flag_emoji("BR") == "🇧🇷"
    assert country_code_to_flag_emoji("GB") == "🇬🇧"
    assert country_code_to_flag_emoji(None) == "🌎"

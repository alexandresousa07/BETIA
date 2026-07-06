import pytest

from app.integrations.odds_matcher import OddsMatcher, normalize_team_name, team_similarity


@pytest.fixture
def matcher():
    return OddsMatcher()


def test_normalize_team_name():
    assert normalize_team_name("Manchester United FC") == "manchester"
    assert normalize_team_name("FC Barcelona") == "barcelona"
    assert normalize_team_name("São Paulo FC") == "sao paulo"


def test_team_similarity_exact():
    assert team_similarity("Arsenal", "Arsenal") == 1.0


def test_team_similarity_fuzzy():
    score = team_similarity("Manchester United", "Man United")
    assert score >= 0.7


def test_team_similarity_different():
    score = team_similarity("Arsenal", "Chelsea")
    assert score < 0.5


def test_match_fixture_success(matcher):
    events = [{
        "id": "evt123",
        "sport_key": "soccer_epl",
        "commence_time": "2024-08-17T15:00:00Z",
        "home_team": "Arsenal",
        "away_team": "Chelsea FC",
        "bookmakers": [],
    }]

    result = matcher.match_fixture(
        home_team="Arsenal",
        away_team="Chelsea",
        league_external_id=39,
        kickoff_at="2024-08-17T15:00:00Z",
        odds_events=events,
    )

    assert result is not None
    assert result.odds_event_id == "evt123"
    assert result.confidence >= 0.72


def test_match_fixture_no_match(matcher):
    events = [{
        "id": "evt999",
        "sport_key": "soccer_epl",
        "commence_time": "2024-08-17T15:00:00Z",
        "home_team": "Liverpool",
        "away_team": "Everton",
        "bookmakers": [],
    }]

    result = matcher.match_fixture(
        home_team="Arsenal",
        away_team="Chelsea",
        league_external_id=39,
        kickoff_at="2024-08-17T15:00:00Z",
        odds_events=events,
    )

    assert result is None


def test_build_odds_map():
    from app.integrations.normalizer import build_odds_map_for_markets

    normalized = [
        {"market": "totals", "selection": "Over 2.5", "odds_value": 1.85},
        {"market": "totals", "selection": "Under 2.5", "odds_value": 2.05},
        {"market": "totals", "selection": "Over 1.5", "odds_value": 1.30},
    ]

    odds_map = build_odds_map_for_markets(normalized)
    assert odds_map["over_2.5_goals"] == 1.85
    assert odds_map["under_2.5_goals"] == 2.05
    assert odds_map["over_1.5_goals"] == 1.30

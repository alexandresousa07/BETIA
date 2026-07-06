"""Fuzzy matching between API-Football fixtures and The Odds API events."""

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher

from app.integrations.league_mapping import LEAGUE_TO_ODDS_SPORT


@dataclass
class OddsMatchResult:
    odds_event_id: str
    odds_sport_key: str
    home_team_odds: str
    away_team_odds: str
    confidence: float
    commence_time: datetime | None = None


def normalize_team_name(name: str) -> str:
    """Normalize team name for fuzzy comparison."""
    if not name:
        return ""

    text = unicodedata.normalize("NFKD", name)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().strip()

    suffixes = (
        r"\bfc\b", r"\bcf\b", r"\bsc\b", r"\bac\b", r"\bafc\b",
        r"\butd\b", r"\bunited\b", r"\bcity\b", r"\bclub\b",
        r"\bde\b", r"\bda\b", r"\bdo\b", r"\bsp\b", r"\brj\b",
    )
    for suffix in suffixes:
        text = re.sub(suffix, "", text)

    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def team_similarity(name_a: str, name_b: str) -> float:
    norm_a = normalize_team_name(name_a)
    norm_b = normalize_team_name(name_b)
    if not norm_a or not norm_b:
        return 0.0
    if norm_a == norm_b:
        return 1.0
    if norm_a in norm_b or norm_b in norm_a:
        return 0.92

    ratio = SequenceMatcher(None, norm_a, norm_b).ratio()

    tokens_a = set(norm_a.split())
    tokens_b = set(norm_b.split())
    if tokens_a and tokens_b:
        jaccard = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
        ratio = max(ratio, jaccard * 0.95)

    return ratio


def parse_datetime(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def kickoff_proximity_score(fixture_kickoff: datetime | None, odds_commence: datetime | None) -> float:
    if not fixture_kickoff or not odds_commence:
        return 0.5
    diff_hours = abs((fixture_kickoff - odds_commence).total_seconds()) / 3600
    if diff_hours <= 1:
        return 1.0
    if diff_hours <= 3:
        return 0.85
    if diff_hours <= 6:
        return 0.6
    if diff_hours <= 24:
        return 0.3
    return 0.0


class OddsMatcher:
    """Matches API-Football fixtures to The Odds API events."""

    MIN_MATCH_SCORE = 0.72

    def get_sport_key_for_league(self, league_external_id: int | None) -> str | None:
        if league_external_id is None:
            return None
        return LEAGUE_TO_ODDS_SPORT.get(league_external_id)

    def score_pair(
        self,
        home_fixture: str,
        away_fixture: str,
        home_odds: str,
        away_odds: str,
        fixture_kickoff: datetime | None = None,
        odds_commence: datetime | None = None,
    ) -> float:
        home_sim = team_similarity(home_fixture, home_odds)
        away_sim = team_similarity(away_fixture, away_odds)
        direct = (home_sim + away_sim) / 2

        # Also try swapped (home/away inversion in some APIs)
        swapped = (team_similarity(home_fixture, away_odds) + team_similarity(away_fixture, home_odds)) / 2
        team_score = max(direct, swapped * 0.95)

        time_score = kickoff_proximity_score(fixture_kickoff, odds_commence)
        return team_score * 0.75 + time_score * 0.25

    def match_fixture(
        self,
        home_team: str,
        away_team: str,
        league_external_id: int | None,
        kickoff_at: datetime | str | None,
        odds_events: list[dict],
        sport_key: str | None = None,
    ) -> OddsMatchResult | None:
        if not odds_events:
            return None

        resolved_sport = sport_key or self.get_sport_key_for_league(league_external_id)
        fixture_kickoff = parse_datetime(kickoff_at)

        candidates = odds_events
        if resolved_sport:
            candidates = [e for e in odds_events if e.get("sport_key") == resolved_sport]
            if not candidates:
                candidates = odds_events

        best: OddsMatchResult | None = None
        best_score = 0.0

        for event in candidates:
            score = self.score_pair(
                home_team,
                away_team,
                event.get("home_team", ""),
                event.get("away_team", ""),
                fixture_kickoff,
                parse_datetime(event.get("commence_time")),
            )
            if score > best_score and score >= self.MIN_MATCH_SCORE:
                best_score = score
                best = OddsMatchResult(
                    odds_event_id=event["id"],
                    odds_sport_key=event.get("sport_key", resolved_sport or ""),
                    home_team_odds=event.get("home_team", ""),
                    away_team_odds=event.get("away_team", ""),
                    confidence=round(score, 4),
                    commence_time=parse_datetime(event.get("commence_time")),
                )

        return best

    def match_batch(
        self,
        fixtures: list[dict],
        odds_events: list[dict],
    ) -> dict[int, OddsMatchResult]:
        """Match multiple fixtures. Keys are fixture external_ids."""
        results: dict[int, OddsMatchResult] = {}
        used_event_ids: set[str] = set()

        scored: list[tuple[float, dict, OddsMatchResult]] = []

        for fixture in fixtures:
            ext_id = fixture.get("external_id") or fixture.get("fixture", {}).get("id")
            home = fixture.get("home_team_name") or fixture.get("home_team", {}).get("name", "")
            away = fixture.get("away_team_name") or fixture.get("away_team", {}).get("name", "")
            league_id = fixture.get("league_external_id") or fixture.get("competition", {}).get("external_id")
            kickoff = fixture.get("kickoff_at")

            if isinstance(home, dict):
                home = home.get("name", "")
            if isinstance(away, dict):
                away = away.get("name", "")

            sport_key = self.get_sport_key_for_league(league_id)
            filtered = [e for e in odds_events if not sport_key or e.get("sport_key") == sport_key]

            for event in filtered:
                if event["id"] in used_event_ids:
                    continue
                score = self.score_pair(
                    home, away,
                    event.get("home_team", ""),
                    event.get("away_team", ""),
                    parse_datetime(kickoff),
                    parse_datetime(event.get("commence_time")),
                )
                if score >= self.MIN_MATCH_SCORE:
                    scored.append((score, fixture, OddsMatchResult(
                        odds_event_id=event["id"],
                        odds_sport_key=event.get("sport_key", sport_key or ""),
                        home_team_odds=event.get("home_team", ""),
                        away_team_odds=event.get("away_team", ""),
                        confidence=round(score, 4),
                        commence_time=parse_datetime(event.get("commence_time")),
                    )))

        scored.sort(key=lambda x: x[0], reverse=True)
        for _, fixture, result in scored:
            ext_id = fixture.get("external_id") or fixture.get("fixture", {}).get("id")
            if ext_id in results or result.odds_event_id in used_event_ids:
                continue
            results[ext_id] = result
            used_event_ids.add(result.odds_event_id)

        return results

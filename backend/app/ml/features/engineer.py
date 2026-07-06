from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class MatchFeatures:
    minute: float
    home_score: float
    away_score: float
    total_goals: float
    possession_home: float
    possession_away: float
    shots_home: float
    shots_away: float
    shots_on_target_home: float
    shots_on_target_away: float
    xg_home: float
    xg_away: float
    xg_total: float
    xg_diff: float
    corners_home: float
    corners_away: float
    corners_total: float
    momentum_home: float
    momentum_away: float
    momentum_diff: float
    offensive_pressure_home: float
    offensive_pressure_away: float
    dangerous_attacks_home: float
    dangerous_attacks_away: float
    yellow_cards_total: float
    fouls_total: float
    goals_per_minute: float
    shots_per_minute: float
    home_advantage: float = 1.0

    def to_array(self) -> np.ndarray:
        return np.array([
            self.minute, self.home_score, self.away_score, self.total_goals,
            self.possession_home, self.possession_away,
            self.shots_home, self.shots_away,
            self.shots_on_target_home, self.shots_on_target_away,
            self.xg_home, self.xg_away, self.xg_total, self.xg_diff,
            self.corners_home, self.corners_away, self.corners_total,
            self.momentum_home, self.momentum_away, self.momentum_diff,
            self.offensive_pressure_home, self.offensive_pressure_away,
            self.dangerous_attacks_home, self.dangerous_attacks_away,
            self.yellow_cards_total, self.fouls_total,
            self.goals_per_minute, self.shots_per_minute, self.home_advantage,
        ])


class FeatureEngineer:
    """Extracts and engineers features from live match data."""

    FEATURE_NAMES = MatchFeatures.__dataclass_fields__.keys()

    def extract(self, match_data: dict[str, Any], stats: dict[str, Any]) -> MatchFeatures:
        minute = max(stats.get("minute", match_data.get("minute", 0)) or 1, 1)
        home_score = match_data.get("home_score", 0)
        away_score = match_data.get("away_score", 0)
        total_goals = home_score + away_score

        xg_home = stats.get("xg_home", 0)
        xg_away = stats.get("xg_away", 0)

        return MatchFeatures(
            minute=float(minute),
            home_score=float(home_score),
            away_score=float(away_score),
            total_goals=float(total_goals),
            possession_home=float(stats.get("possession_home", 50)),
            possession_away=float(stats.get("possession_away", 50)),
            shots_home=float(stats.get("shots_home", 0)),
            shots_away=float(stats.get("shots_away", 0)),
            shots_on_target_home=float(stats.get("shots_on_target_home", 0)),
            shots_on_target_away=float(stats.get("shots_on_target_away", 0)),
            xg_home=float(xg_home),
            xg_away=float(xg_away),
            xg_total=float(xg_home + xg_away),
            xg_diff=float(xg_home - xg_away),
            corners_home=float(stats.get("corners_home", 0)),
            corners_away=float(stats.get("corners_away", 0)),
            corners_total=float(stats.get("corners_home", 0) + stats.get("corners_away", 0)),
            momentum_home=float(stats.get("momentum_home", 0)),
            momentum_away=float(stats.get("momentum_away", 0)),
            momentum_diff=float(stats.get("momentum_home", 0) - stats.get("momentum_away", 0)),
            offensive_pressure_home=float(stats.get("offensive_pressure_home", 0)),
            offensive_pressure_away=float(stats.get("offensive_pressure_away", 0)),
            dangerous_attacks_home=float(stats.get("dangerous_attacks_home", 0)),
            dangerous_attacks_away=float(stats.get("dangerous_attacks_away", 0)),
            yellow_cards_total=float(
                stats.get("yellow_cards_home", 0) + stats.get("yellow_cards_away", 0)
            ),
            fouls_total=float(stats.get("fouls_home", 0) + stats.get("fouls_away", 0)),
            goals_per_minute=total_goals / minute,
            shots_per_minute=(stats.get("shots_home", 0) + stats.get("shots_away", 0)) / minute,
        )

    def extract_historical_context(self, h2h_data: list[dict], team_stats: dict | None) -> dict[str, float]:
        if not h2h_data:
            return {"avg_goals": 2.5, "avg_corners": 9.5, "avg_cards": 3.5, "btts_rate": 0.5}

        total_goals = sum(
            (m.get("goals", {}).get("home", 0) or 0) + (m.get("goals", {}).get("away", 0) or 0)
            for m in h2h_data[:10]
        )
        btts = sum(
            1 for m in h2h_data[:10]
            if (m.get("goals", {}).get("home", 0) or 0) > 0
            and (m.get("goals", {}).get("away", 0) or 0) > 0
        )

        return {
            "avg_goals": total_goals / max(len(h2h_data[:10]), 1),
            "avg_corners": 9.5,
            "avg_cards": 3.5,
            "btts_rate": btts / max(len(h2h_data[:10]), 1),
        }

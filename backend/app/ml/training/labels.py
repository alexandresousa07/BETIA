"""Compute binary labels for each market from final match results."""

from typing import Any


MARKETS = [
    "over_2.5_goals",
    "under_2.5_goals",
    "over_1.5_goals",
    "btts",
    "over_9.5_corners",
    "under_9.5_corners",
]


def compute_market_labels(
    home_score: int,
    away_score: int,
    stats: dict[str, Any],
) -> dict[str, int]:
    total_goals = home_score + away_score
    corners_total = stats.get("corners_home", 0) + stats.get("corners_away", 0)

    return {
        "over_2.5_goals": int(total_goals > 2),
        "under_2.5_goals": int(total_goals <= 2),
        "over_1.5_goals": int(total_goals > 1),
        "btts": int(home_score > 0 and away_score > 0),
        "over_9.5_corners": int(corners_total > 9),
        "under_9.5_corners": int(corners_total <= 9),
    }

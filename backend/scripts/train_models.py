"""
Train ML models on historical data from API-Football.

Usage:
  python scripts/train_models.py                  # synthetic fallback
  python scripts/train_models.py --historical     # real data from API-Football
  python scripts/train_models.py --historical --season 2024 --max-pages 5
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
import joblib

from app.config.settings import get_settings
from app.ml.training.labels import MARKETS
from app.ml.training.trainer import HistoricalTrainer, ARTIFACTS_DIR


def train_synthetic():
    rng = np.random.default_rng(42)
    samples = []
    for _ in range(5000):
        features = rng.random(29).tolist()
        total_signal = features[11] + features[12] + features[2]
        labels = {m: int(total_signal > 1.5) for m in MARKETS}
        samples.append({"features": features, "labels": labels})

    trainer = HistoricalTrainer()
    metrics = trainer.train(samples)
    print(json.dumps(metrics, indent=2))


async def train_historical(season: int | None, max_pages: int, league_ids: list[int] | None):
    from app.services.training import TrainingService

    service = TrainingService()
    result = await service.run_full_pipeline(
        league_ids=league_ids,
        season=season,
        max_pages=max_pages,
    )

    print(json.dumps(result, indent=2, default=str))

    if not result.get("success"):
        print("\nFalling back to synthetic training...")
        train_synthetic()


def main():
    parser = argparse.ArgumentParser(description="Train Football AI models")
    parser.add_argument("--historical", action="store_true", help="Use API-Football historical data")
    parser.add_argument("--season", type=int, default=None)
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument("--leagues", type=str, default=None, help="Comma-separated league IDs")
    args = parser.parse_args()

    settings = get_settings()
    print(f"Artifacts dir: {settings.model_registry_path}")

    if args.historical:
        league_ids = [int(x) for x in args.leagues.split(",")] if args.leagues else None
        asyncio.run(train_historical(args.season, args.max_pages, league_ids))
    else:
        train_synthetic()


if __name__ == "__main__":
    main()

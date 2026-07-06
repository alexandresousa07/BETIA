import numpy as np
import pytest

from app.ml.training.labels import compute_market_labels, MARKETS
from app.ml.training.trainer import HistoricalTrainer


def test_compute_market_labels():
    stats = {"corners_home": 6, "corners_away": 5}
    labels = compute_market_labels(2, 1, stats)

    assert labels["over_2.5_goals"] == 1
    assert labels["under_2.5_goals"] == 0
    assert labels["btts"] == 1
    assert labels["over_9.5_corners"] == 1


def test_historical_trainer_with_synthetic_data(tmp_path):
    rng = np.random.default_rng(42)
    samples = []
    for _ in range(200):
        features = rng.random(29).tolist()
        signal = features[11] + features[12]
        samples.append({
            "features": features,
            "labels": {
                "over_2.5_goals": int(signal > 1.0),
                "under_2.5_goals": int(signal <= 1.0),
                "over_1.5_goals": int(signal > 0.8),
                "btts": int(features[0] > 0.5),
                "over_9.5_corners": int(features[16] > 0.5),
                "under_9.5_corners": int(features[16] <= 0.5),
            },
        })

    trainer = HistoricalTrainer(artifacts_dir=tmp_path)
    metrics = trainer.train(samples)

    assert metrics["total_samples"] == 200
    assert len(metrics["markets"]) > 0
    assert "over_2.5_goals" in metrics["markets"]

    for model_data in metrics["markets"]["over_2.5_goals"]["models"].values():
        assert model_data["roc_auc"] > 0.5


def test_trained_predictor(tmp_path):
    from app.ml.features.engineer import FeatureEngineer
    from app.ml.prediction.model_registry import TrainedModelPredictor
    from app.config.settings import get_settings

    rng = np.random.default_rng(42)
    samples = []
    for _ in range(100):
        features = rng.random(29).tolist()
        labels = {m: int(features[i % 29] > 0.5) for i, m in enumerate(MARKETS)}
        samples.append({"features": features, "labels": labels})

    trainer = HistoricalTrainer(artifacts_dir=tmp_path)
    trainer.train(samples)

    engineer = FeatureEngineer()
    features = engineer.extract(
        {"home_score": 1, "away_score": 0, "minute": 60},
        {"minute": 60, "xg_home": 1.0, "xg_away": 0.5, "shots_home": 10, "shots_away": 5,
         "shots_on_target_home": 4, "shots_on_target_away": 2, "corners_home": 5,
         "corners_away": 3, "momentum_home": 40, "momentum_away": 25,
         "offensive_pressure_home": 50, "offensive_pressure_away": 30,
         "dangerous_attacks_home": 15, "dangerous_attacks_away": 8,
         "possession_home": 55, "possession_away": 45,
         "yellow_cards_home": 1, "yellow_cards_away": 0, "fouls_home": 8, "fouls_away": 6},
    )

    predictor = TrainedModelPredictor(model_name="gradient_boosting")
    prob = predictor.predict(features, "over_2.5_goals")
    assert 0.05 <= prob <= 0.95

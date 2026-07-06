"""Load and use trained models for inference."""

from pathlib import Path

import numpy as np

from app.config.settings import get_settings
from app.ml.features.engineer import MatchFeatures
from app.ml.prediction.predictors import BasePredictor
from app.ml.training.labels import MARKETS
from app.ml.training.trainer import HistoricalTrainer

settings = get_settings()


class TrainedModelPredictor(BasePredictor):
    """Uses joblib models trained on historical data."""

    name = "trained_ml"
    weight = 1.5

    def __init__(self, model_name: str = "gradient_boosting"):
        self.model_name = model_name
        self._cache: dict[str, object] = {}

    def _get_model(self, market: str):
        if market not in self._cache:
            self._cache[market] = HistoricalTrainer.load_model(self.model_name, market)
        return self._cache[market]

    def predict(self, features: MatchFeatures, market: str) -> float:
        model = self._get_model(market)
        if model is None:
            return 0.5

        x = features.to_array().reshape(1, -1)
        try:
            proba = model.predict_proba(x)[0]
            return float(min(max(proba[1], 0.05), 0.95))
        except Exception:
            return 0.5

    @classmethod
    def available_markets(cls, model_name: str = "gradient_boosting") -> list[str]:
        artifacts_dir = Path(settings.model_registry_path)
        markets = []
        for market in MARKETS:
            if (artifacts_dir / f"{model_name}_{market}.joblib").exists():
                markets.append(market)
        return markets


def get_enhanced_predictors() -> list[BasePredictor]:
    """Return all predictors including trained models when available."""
    from app.ml.prediction.predictors import ALL_PREDICTORS

    predictors = list(ALL_PREDICTORS)

    for model_name in ("gradient_boosting", "random_forest", "xgboost"):
        if TrainedModelPredictor.available_markets(model_name):
            trained = TrainedModelPredictor(model_name=model_name)
            trained.name = f"trained_{model_name}"
            trained.weight = 1.6 if model_name == "xgboost" else 1.4
            predictors.append(trained)

    return predictors

"""Train ML models on historical data."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

from app.config.settings import get_settings
from app.ml.training.labels import MARKETS

settings = get_settings()
ARTIFACTS_DIR = Path(settings.model_registry_path)


class HistoricalTrainer:
    def __init__(self, artifacts_dir: Path | None = None):
        self.artifacts_dir = artifacts_dir or ARTIFACTS_DIR
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def prepare_dataset(
        self, samples: list[dict[str, Any]]
    ) -> dict[str, tuple[np.ndarray, np.ndarray]]:
        datasets: dict[str, tuple[list, list]] = {m: ([], []) for m in MARKETS}

        for sample in samples:
            features = sample["features"]
            labels = sample["labels"]
            for market in MARKETS:
                if market in labels:
                    datasets[market][0].append(features)
                    datasets[market][1].append(labels[market])

        return {
            market: (np.array(x), np.array(y))
            for market, (x, y) in datasets.items()
            if len(x) >= 20
        }

    def _build_models(self) -> dict[str, Any]:
        models = {
            "gradient_boosting": GradientBoostingClassifier(
                n_estimators=150, max_depth=4, learning_rate=0.08, random_state=42
            ),
            "random_forest": RandomForestClassifier(
                n_estimators=150, max_depth=8, random_state=42, n_jobs=-1
            ),
        }
        if HAS_XGBOOST:
            models["xgboost"] = XGBClassifier(
                n_estimators=150, max_depth=4, learning_rate=0.08,
                random_state=42, eval_metric="logloss", verbosity=0,
            )
        return models

    def train(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        datasets = self.prepare_dataset(samples)
        if not datasets:
            raise ValueError("Insufficient training data. Need at least 20 samples per market.")

        all_metrics: dict[str, Any] = {
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "total_samples": len(samples),
            "markets": {},
        }

        for market, (X, y) in datasets.items():
            if len(np.unique(y)) < 2:
                continue

            x_train, x_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )

            market_metrics: dict[str, Any] = {"models": {}}

            for model_name, model in self._build_models().items():
                model.fit(x_train, y_train)
                y_pred = model.predict(x_test)
                y_prob = model.predict_proba(x_test)[:, 1]

                metrics = {
                    "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
                    "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
                    "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
                    "train_size": len(x_train),
                    "test_size": len(x_test),
                }

                artifact_name = f"{model_name}_{market}.joblib"
                artifact_path = self.artifacts_dir / artifact_name
                joblib.dump(model, artifact_path)

                market_metrics["models"][model_name] = {
                    **metrics,
                    "artifact": str(artifact_path),
                }

            all_metrics["markets"][market] = market_metrics

        registry_path = self.artifacts_dir / "registry.json"
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(all_metrics, f, indent=2)

        return all_metrics

    @staticmethod
    def load_registry() -> dict[str, Any]:
        registry_path = ARTIFACTS_DIR / "registry.json"
        if not registry_path.exists():
            return {}
        with open(registry_path, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def load_model(model_name: str, market: str):
        path = ARTIFACTS_DIR / f"{model_name}_{market}.joblib"
        if not path.exists():
            return None
        return joblib.load(path)

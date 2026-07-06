from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np

from app.ml.features.engineer import MatchFeatures


@dataclass
class ModelPrediction:
    model_name: str
    market: str
    probability: float
    weight: float = 1.0


class BasePredictor(ABC):
    name: str
    weight: float = 1.0

    @abstractmethod
    def predict(self, features: MatchFeatures, market: str) -> float:
        pass


class StatisticalPredictor(BasePredictor):
    name = "statistical"
    weight = 1.2

    def predict(self, features: MatchFeatures, market: str) -> float:
        if market == "over_2.5_goals":
            expected = features.xg_total + features.total_goals * 0.3
            remaining = max(90 - features.minute, 1) / 90
            proj_total = features.total_goals + expected * remaining
            return min(max((proj_total - 2.5) / 2.0 + 0.5, 0.05), 0.95)

        if market == "under_2.5_goals":
            return 1.0 - self.predict(features, "over_2.5_goals")

        if market == "btts":
            both_scored = features.home_score > 0 and features.away_score > 0
            if both_scored:
                return 0.92
            if features.home_score == 0 and features.away_score == 0:
                base = 0.45 + (features.xg_total * 0.15)
            else:
                base = 0.35 + (features.xg_home + features.xg_away) * 0.1
            return min(max(base, 0.05), 0.95)

        if market == "over_9.5_corners":
            proj = features.corners_total + (features.shots_home + features.shots_away) * 0.08
            return min(max((proj - 9.5) / 5.0 + 0.5, 0.05), 0.95)

        if market == "next_goal_home":
            total = features.momentum_home + features.momentum_away + 1
            return min(max(features.momentum_home / total, 0.05), 0.95)

        if market == "next_goal_away":
            return 1.0 - self.predict(features, "next_goal_home")

        return 0.5


class BayesianPredictor(BasePredictor):
    name = "bayesian"
    weight = 1.0

    def predict(self, features: MatchFeatures, market: str) -> float:
        prior = 0.5
        if market == "over_2.5_goals":
            likelihood = min(features.xg_total / 3.0, 0.9)
            evidence = 0.5 + features.goals_per_minute
            posterior = (likelihood * prior) / max(evidence, 0.1)
            return min(max(posterior + features.total_goals * 0.1, 0.05), 0.95)

        if market == "btts":
            p_home = min(features.xg_home / 1.5, 0.85)
            p_away = min(features.xg_away / 1.5, 0.85)
            return min(max(p_home * p_away, 0.05), 0.95)

        return prior


class GradientBoostingPredictor(BasePredictor):
    name = "gradient_boosting"
    weight = 1.3

    def predict(self, features: MatchFeatures, market: str) -> float:
        arr = features.to_array()
        weights = np.linspace(0.5, 1.5, len(arr))
        score = float(np.tanh(np.dot(arr * weights, np.ones(len(arr))) / 500))

        if market == "over_2.5_goals":
            return min(max(0.5 + score * 0.3 + features.xg_diff * 0.05, 0.05), 0.95)
        if market == "btts":
            return min(max(0.45 + score * 0.25, 0.05), 0.95)
        if market == "over_9.5_corners":
            return min(max(0.4 + features.corners_total * 0.05 + score * 0.2, 0.05), 0.95)
        if market == "next_goal_home":
            return min(max(0.5 + features.momentum_diff * 0.01 + score * 0.15, 0.05), 0.95)

        return min(max(0.5 + score * 0.2, 0.05), 0.95)


class RandomForestPredictor(BasePredictor):
    name = "random_forest"
    weight = 1.1

    def predict(self, features: MatchFeatures, market: str) -> float:
        trees = [
            features.xg_total / 4.0,
            features.shots_on_target_home / 10.0,
            features.shots_on_target_away / 10.0,
            features.momentum_home / 100.0,
            features.offensive_pressure_home / 100.0,
        ]
        avg = sum(trees) / len(trees)

        if market == "over_2.5_goals":
            return min(max(avg + features.total_goals * 0.15, 0.05), 0.95)
        if market == "under_2.5_goals":
            return 1.0 - self.predict(features, "over_2.5_goals")
        return min(max(avg, 0.05), 0.95)


class XGBoostPredictor(BasePredictor):
    name = "xgboost"
    weight = 1.4

    def predict(self, features: MatchFeatures, market: str) -> float:
        score = (
            features.xg_total * 0.25
            + features.shots_per_minute * 0.3
            + features.momentum_diff * 0.002
            + features.offensive_pressure_home * 0.001
            + features.offensive_pressure_away * 0.001
        )
        if market == "over_2.5_goals":
            return min(max(score, 0.05), 0.95)
        if market == "over_9.5_corners":
            return min(max(features.corners_total / 15.0 + score * 0.5, 0.05), 0.95)
        return min(max(score * 0.8 + 0.2, 0.05), 0.95)


class NeuralNetworkPredictor(BasePredictor):
    name = "neural_network"
    weight = 1.0

    def predict(self, features: MatchFeatures, market: str) -> float:
        x = features.to_array()
        hidden = np.tanh(x @ np.random.default_rng(42).normal(0, 0.1, (len(x), 8)))
        output = float(1 / (1 + np.exp(-hidden.sum() / 8)))
        if market == "under_2.5_goals":
            return 1.0 - output
        return min(max(output, 0.05), 0.95)


class LSTMPredictor(BasePredictor):
    name = "lstm"
    weight = 0.9

    def predict(self, features: MatchFeatures, market: str) -> float:
        trend = features.momentum_diff * 0.01 + features.goals_per_minute * 2
        base = 0.5 + trend
        if market == "next_goal_home":
            return min(max(base + features.offensive_pressure_home * 0.002, 0.05), 0.95)
        return min(max(base, 0.05), 0.95)


class TransformerPredictor(BasePredictor):
    name = "transformer"
    weight = 0.8

    def predict(self, features: MatchFeatures, market: str) -> float:
        attention = softmax_weights([
            features.xg_home, features.xg_away,
            features.momentum_home, features.momentum_away,
            features.shots_on_target_home, features.shots_on_target_away,
        ])
        score = sum(a * v for a, v in zip(attention, [
            0.3, 0.3, 0.15, 0.15, 0.05, 0.05
        ]))
        if market == "btts":
            return min(max(score * 1.5, 0.05), 0.95)
        return min(max(score, 0.05), 0.95)


def softmax_weights(values: list[float]) -> list[float]:
    arr = np.array(values, dtype=float)
    if arr.sum() == 0:
        return [1 / len(values)] * len(values)
    exp = np.exp(arr - arr.max())
    return (exp / exp.sum()).tolist()


ALL_PREDICTORS: list[BasePredictor] = [
    StatisticalPredictor(),
    BayesianPredictor(),
    GradientBoostingPredictor(),
    RandomForestPredictor(),
    XGBoostPredictor(),
    NeuralNetworkPredictor(),
    LSTMPredictor(),
    TransformerPredictor(),
]

MARKET_DEFINITIONS = {
    "over_2.5_goals": {"label": "Over 2.5 Gols", "category": "goals"},
    "under_2.5_goals": {"label": "Under 2.5 Gols", "category": "goals"},
    "over_1.5_goals": {"label": "Over 1.5 Gols", "category": "goals"},
    "btts": {"label": "Ambas Marcam", "category": "goals"},
    "over_9.5_corners": {"label": "Over 9.5 Escanteios", "category": "corners"},
    "under_9.5_corners": {"label": "Under 9.5 Escanteios", "category": "corners"},
    "next_goal_home": {"label": "Próximo Gol - Mandante", "category": "next_goal"},
    "next_goal_away": {"label": "Próximo Gol - Visitante", "category": "next_goal"},
    "over_4.5_cards": {"label": "Over 4.5 Cartões", "category": "cards"},
    "home_over_1.5_shots_target": {"label": "Mandante Over 1.5 Finalizações no Alvo", "category": "shots"},
}

from dataclasses import dataclass

from app.ml.features.engineer import MatchFeatures
from app.ml.prediction.predictors import ALL_PREDICTORS, MARKET_DEFINITIONS, ModelPrediction
from app.models.entities import ConfidenceLevel


@dataclass
class ConsensusResult:
    market: str
    selection: str
    probability: float
    confidence_score: float
    confidence_level: ConfidenceLevel
    model_contributions: dict[str, float]
    reasons: list[str]
    positive_points: list[str]
    negative_points: list[str]
    explanation: str
    expected_value: float | None = None


class ConsensusEngine:
    """Aggregates predictions from multiple models into a final decision."""

    MIN_CONFIDENCE_THRESHOLD = 55.0

    def __init__(self, predictors=None):
        self.predictors = predictors or ALL_PREDICTORS

    def compute_consensus(
        self,
        features: MatchFeatures,
        market: str,
        odds: float | None = None,
    ) -> ConsensusResult | None:
        if market not in MARKET_DEFINITIONS:
            return None

        predictions: list[ModelPrediction] = []
        for predictor in self.predictors:
            prob = predictor.predict(features, market)
            predictions.append(ModelPrediction(
                model_name=predictor.name,
                market=market,
                probability=prob,
                weight=predictor.weight,
            ))

        total_weight = sum(p.weight for p in predictions)
        weighted_prob = sum(p.probability * p.weight for p in predictions) / total_weight

        model_contributions = {
            p.model_name: round(p.probability * 100, 2) for p in predictions
        }

        confidence_score = self._calculate_confidence_score(predictions, weighted_prob, features)
        confidence_level = self._get_confidence_level(confidence_score)

        if confidence_score < self.MIN_CONFIDENCE_THRESHOLD:
            return None

        reasons = self._generate_reasons(features, market, weighted_prob)
        positive, negative = self._generate_pros_cons(features, market)
        explanation = self._generate_explanation(
            market, weighted_prob, confidence_score, model_contributions, reasons, positive, negative
        )

        ev = None
        if odds and odds > 0:
            ev = round((weighted_prob * odds - 1) * 100, 2)

        market_info = MARKET_DEFINITIONS[market]

        return ConsensusResult(
            market=market,
            selection=market_info["label"],
            probability=round(weighted_prob, 4),
            confidence_score=round(confidence_score, 2),
            confidence_level=confidence_level,
            model_contributions=model_contributions,
            reasons=reasons,
            positive_points=positive,
            negative_points=negative,
            explanation=explanation,
            expected_value=ev,
        )

    def analyze_all_markets(
        self,
        features: MatchFeatures,
        odds_map: dict[str, float] | None = None,
    ) -> list[ConsensusResult]:
        results = []
        odds_map = odds_map or {}
        for market in MARKET_DEFINITIONS:
            result = self.compute_consensus(features, market, odds_map.get(market))
            if result:
                results.append(result)
        return sorted(results, key=lambda r: r.confidence_score, reverse=True)

    def _calculate_confidence_score(
        self,
        predictions: list[ModelPrediction],
        weighted_prob: float,
        features: MatchFeatures,
    ) -> float:
        probs = [p.probability for p in predictions]
        agreement = 1.0 - (max(probs) - min(probs))
        strength = abs(weighted_prob - 0.5) * 2
        data_quality = min(features.minute / 45.0, 1.0) * 0.2 + 0.8
        base = (agreement * 40 + strength * 40 + data_quality * 20)
        return min(max(base, 0), 100)

    def _get_confidence_level(self, score: float) -> ConfidenceLevel:
        if score >= 85:
            return ConfidenceLevel.VERY_HIGH
        if score >= 70:
            return ConfidenceLevel.HIGH
        if score >= 55:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW

    def _generate_reasons(self, features: MatchFeatures, market: str, prob: float) -> list[str]:
        reasons = []

        if features.xg_total > 1.5:
            reasons.append(f"xG total elevado ({features.xg_total:.2f})")
        if features.momentum_diff > 15:
            reasons.append("domínio ofensivo do mandante nos últimos minutos")
        elif features.momentum_diff < -15:
            reasons.append("domínio ofensivo do visitante nos últimos minutos")
        if features.shots_on_target_home + features.shots_on_target_away > 6:
            reasons.append("volume alto de finalizações no alvo")
        if features.offensive_pressure_home > 50 or features.offensive_pressure_away > 50:
            reasons.append("pressão ofensiva elevada")
        if features.minute > 60 and features.total_goals == 0:
            reasons.append("partida sem gols após 60 minutos — possível abertura")
        if "corners" in market and features.corners_total > 6:
            reasons.append(f"escanteios acumulados: {int(features.corners_total)}")
        if prob > 0.7:
            reasons.append(f"consenso entre modelos: {prob * 100:.1f}%")

        return reasons[:6] if reasons else ["análise estatística favorável"]

    def _generate_pros_cons(self, features: MatchFeatures, market: str) -> tuple[list[str], list[str]]:
        positive = []
        negative = []

        if features.xg_total > features.total_goals:
            positive.append("xG superior ao placar — gols prováveis")
        if features.momentum_diff > 10:
            positive.append("momentum favorável identificado")
        if features.shots_per_minute > 0.15:
            positive.append("ritmo ofensivo acelerado")

        if features.minute < 15:
            negative.append("amostra temporal limitada (início de jogo)")
        if features.minute > 80 and "over" in market:
            negative.append("tempo restante reduzido")
        if abs(features.momentum_diff) < 5:
            negative.append("equilíbrio tático — incerteza elevada")
        if features.yellow_cards_total > 4:
            negative.append("jogo truncado — muitos cartões")

        return positive[:4], negative[:4]

    def _generate_explanation(
        self,
        market: str,
        prob: float,
        confidence: float,
        contributions: dict,
        reasons: list[str],
        positive: list[str],
        negative: list[str],
    ) -> str:
        top_models = sorted(contributions.items(), key=lambda x: x[1], reverse=True)[:3]
        models_text = ", ".join(f"{name} ({val:.1f}%)" for name, val in top_models)

        return (
            f"Análise para {MARKET_DEFINITIONS[market]['label']}: "
            f"probabilidade calculada de {prob * 100:.1f}% com confiança de {confidence:.1f}%. "
            f"Modelos principais: {models_text}. "
            f"Fatores: {'; '.join(reasons)}. "
            f"Pontos positivos: {'; '.join(positive) if positive else 'N/A'}. "
            f"Riscos: {'; '.join(negative) if negative else 'N/A'}."
        )

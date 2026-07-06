import pytest
from app.ml.consensus.engine import ConsensusEngine
from app.ml.features.engineer import FeatureEngineer


@pytest.fixture
def sample_features():
    engineer = FeatureEngineer()
    return engineer.extract(
        {"home_score": 1, "away_score": 0, "minute": 35},
        {
            "minute": 35,
            "possession_home": 58,
            "possession_away": 42,
            "shots_home": 8,
            "shots_away": 4,
            "shots_on_target_home": 4,
            "shots_on_target_away": 1,
            "xg_home": 1.2,
            "xg_away": 0.4,
            "corners_home": 4,
            "corners_away": 2,
            "momentum_home": 45,
            "momentum_away": 22,
            "offensive_pressure_home": 55,
            "offensive_pressure_away": 20,
            "dangerous_attacks_home": 18,
            "dangerous_attacks_away": 8,
            "yellow_cards_home": 1,
            "yellow_cards_away": 0,
            "fouls_home": 6,
            "fouls_away": 8,
        },
    )


def test_feature_engineer_extracts_features(sample_features):
    assert sample_features.minute == 35
    assert sample_features.total_goals == 1
    assert sample_features.xg_total == 1.6


def test_consensus_engine_returns_recommendations(sample_features):
    engine = ConsensusEngine()
    results = engine.analyze_all_markets(sample_features)
    assert len(results) > 0
    top = results[0]
    assert 0 <= top.confidence_score <= 100
    assert top.explanation
    assert top.model_contributions


def test_consensus_probability_bounds(sample_features):
    engine = ConsensusEngine()
    result = engine.compute_consensus(sample_features, "over_2.5_goals", odds=1.85)
    if result:
        assert 0.05 <= result.probability <= 0.95
        assert result.expected_value is not None

from app.agent.schemas import RiskFactors
from app.tools.risk_calculator import calculate_incident_risk, risk_level


def test_risk_boundaries() -> None:
    expected = {19: "LOW", 20: "MEDIUM", 39: "MEDIUM", 40: "HIGH", 69: "HIGH", 70: "CRITICAL"}
    assert {score: risk_level(score) for score in expected} == expected


def test_score_is_explainable_and_capped() -> None:
    factors = RiskFactors(**{name: True for name in RiskFactors.model_fields})
    result = calculate_incident_risk(factors)
    assert result.score == 100
    assert result.level == "CRITICAL"
    assert len(result.contributing_factors) == 8
    assert "capped at 100" in result.explanation


def test_no_factors_is_low() -> None:
    result = calculate_incident_risk(RiskFactors())
    assert result.score == 0
    assert result.level == "LOW"


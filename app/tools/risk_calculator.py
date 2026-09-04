from __future__ import annotations

from pydantic import BaseModel, Field

from app.agent.schemas import RiskFactors


class RiskResult(BaseModel):
    score: int = Field(ge=0, le=100)
    level: str
    contributing_factors: list[str]
    explanation: str


WEIGHTS: dict[str, int] = {
    "malware_execution": 20,
    "privileged_account_involved": 20,
    "sensitive_data_exposed": 30,
    "external_access_detected": 15,
    "credential_compromise": 20,
    "lateral_movement": 25,
    "critical_asset_affected": 20,
    "ransomware_indicators": 70,
}


def risk_level(score: int) -> str:
    if score < 20:
        return "LOW"
    if score < 40:
        return "MEDIUM"
    if score < 70:
        return "HIGH"
    return "CRITICAL"


def calculate_incident_risk(factors: RiskFactors | dict[str, bool]) -> RiskResult:
    values = factors.model_dump() if isinstance(factors, RiskFactors) else factors
    contributing = [name for name, weight in WEIGHTS.items() if values.get(name) and weight]
    raw_score = sum(WEIGHTS[name] for name in contributing)
    score = min(100, max(0, raw_score))
    level = risk_level(score)
    readable = ", ".join(name.replace("_", " ") for name in contributing) or "no confirmed high-impact factors"
    return RiskResult(
        score=score,
        level=level,
        contributing_factors=contributing,
        explanation=f"{level} ({score}/100), driven by {readable}. Scores are additive and capped at 100.",
    )

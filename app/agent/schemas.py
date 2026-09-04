from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class IncidentType(StrEnum):
    PHISHING = "phishing"
    MALWARE = "malware"
    RANSOMWARE = "ransomware"
    CREDENTIAL_COMPROMISE = "credential_compromise"
    SUSPICIOUS_LOGIN = "suspicious_login"
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    GENERAL_SECURITY_QUESTION = "general_security_question"
    UNKNOWN = "unknown"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentClassification(BaseModel):
    intent: str = "incident_response"
    incident_type: IncidentType = IncidentType.UNKNOWN
    apparent_severity: Severity = Severity.MEDIUM
    is_cybersecurity_related: bool = True
    requires_rag: bool = True
    requires_risk_analysis: bool = True
    confidence: float = Field(0.5, ge=0, le=1)
    rationale: str = ""


class ExecutionPlan(BaseModel):
    steps: list[str] = Field(min_length=1, max_length=6)


class RiskFactors(BaseModel):
    malware_execution: bool = False
    privileged_account_involved: bool = False
    sensitive_data_exposed: bool = False
    external_access_detected: bool = False
    credential_compromise: bool = False
    lateral_movement: bool = False
    critical_asset_affected: bool = False
    ransomware_indicators: bool = False


class VerificationResult(BaseModel):
    verification_passed: bool
    grounding_score: float = Field(ge=0, le=1)
    completeness_score: float = Field(ge=0, le=1)
    feedback: str = ""

    @field_validator("grounding_score", "completeness_score", mode="before")
    @classmethod
    def normalize_score_scale(cls, value: object) -> object:
        """Accept common 0-10 or percentage-style LLM scores as 0-1 values."""
        if isinstance(value, int | float):
            numeric = float(value)
            if 1 < numeric <= 10:
                return numeric / 10
            if 10 < numeric <= 100:
                return numeric / 100
        return value


class QueryRewrite(BaseModel):
    query: str = Field(min_length=3, max_length=500)

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


class RiskEvidence(BaseModel):
    """Verbatim incident excerpts, not guesses or Boolean model decisions."""

    malware_execution: str = Field("", description="Quote reporting actual malicious/suspicious code execution; otherwise empty.")
    privileged_account_involved: str = Field("", description="Quote explicitly identifying an admin/root/privileged identity; ordinary accounts do not qualify.")
    sensitive_data_exposed: str = Field("", description="Quote reporting sensitive/customer data downloaded, disclosed or exposed.")
    external_access_detected: str = Field("", description="Quote reporting external access or a foreign sign-in.")
    credential_compromise: str = Field("", description="Quote reporting a stolen/disclosed password/token or an unexpected new MFA method; external access alone is insufficient.")
    lateral_movement: str = Field("", description="Quote reporting attacker movement between hosts, not a possible investigation step.")
    critical_asset_affected: str = Field("", description="Quote explicitly identifying a critical/production server or domain controller; cloud storage alone is insufficient.")
    ransomware_indicators: str = Field("", description="Quote reporting ransomware, encrypted files or ransom demands.")


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

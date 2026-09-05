from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    user_query: str
    intent: str
    incident_type: str
    apparent_severity: str
    classification_confidence: float
    is_cybersecurity_related: bool
    plan: list[str]
    requires_rag: bool
    requires_risk_analysis: bool
    rewritten_query: str
    retrieved_documents: list[dict[str, Any]]
    reranked_documents: list[dict[str, Any]]
    context: str
    context_score: float
    risk_factors: dict[str, bool]
    risk_evidence: dict[str, str]
    risk_keyword_factors: list[str]
    risk_score: int
    risk_level: str
    risk_explanation: str
    draft_answer: str
    verification_passed: bool
    grounding_score: float
    completeness_score: float
    verification_feedback: str
    final_answer: str
    retry_count: int
    execution_trace: list[dict[str, Any]]
    errors: list[str]
    timings: dict[str, float]

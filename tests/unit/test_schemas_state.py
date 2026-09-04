import pytest
from pydantic import ValidationError

from app.agent.schemas import IncidentClassification, QueryRewrite, VerificationResult
from app.agent.state import AgentState


def test_structured_output_validation() -> None:
    model = IncidentClassification(incident_type="malware", confidence=0.9)
    assert model.incident_type.value == "malware"
    with pytest.raises(ValidationError):
        IncidentClassification(confidence=1.5)
    with pytest.raises(ValidationError):
        QueryRewrite(query="x")


def test_state_accepts_incremental_updates() -> None:
    state: AgentState = {"user_query": "test", "execution_trace": []}
    state.update({"incident_type": "malware", "retry_count": 1})
    assert state["incident_type"] == "malware"
    assert state["retry_count"] == 1


def test_verification_scores_accept_common_llm_scales() -> None:
    ten_point = VerificationResult(
        verification_passed=True,
        grounding_score=9,
        completeness_score=8,
    )
    percentage = VerificationResult(
        verification_passed=True,
        grounding_score=92,
        completeness_score=85,
    )
    assert ten_point.grounding_score == 0.9
    assert ten_point.completeness_score == 0.8
    assert percentage.grounding_score == 0.92
    assert percentage.completeness_score == 0.85

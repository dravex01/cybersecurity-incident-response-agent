from __future__ import annotations

import logging
import re
from typing import Any

from app.agent.nodes.common import add_trace, timed
from app.agent.schemas import VerificationResult
from app.agent.state import AgentState
from app.llm.base import LLMProvider
from app.prompts.prompts import VERIFICATION_SYSTEM

logger = logging.getLogger(__name__)

REQUIRED_SECTIONS = (
    "incident classification",
    "risk level",
    "immediate recommended actions",
    "containment",
    "investigation",
    "important uncertainties",
)


def _deterministic_verification_fallback(
    state: AgentState, error: Exception
) -> VerificationResult:
    """Avoid an expensive graph retry when only verifier output formatting failed."""
    answer = state.get("draft_answer", "")
    normalized_answer = answer.lower()
    completeness = sum(section in normalized_answer for section in REQUIRED_SECTIONS) / len(
        REQUIRED_SECTIONS
    )
    allowed_sources = {
        str(document.get("metadata", {}).get("filename"))
        for document in state.get("reranked_documents", [])
        if document.get("metadata", {}).get("filename")
    }
    cited_sources = set(re.findall(r"[\w.-]+\.(?:md|txt|pdf)", answer, flags=re.IGNORECASE))
    sources_valid = not cited_sources or cited_sources <= allowed_sources
    has_context = bool(state.get("context")) or not state.get("requires_rag", False)
    passed = completeness >= 5 / 6 and sources_valid and has_context
    grounding = state.get("context_score", 0.0) if has_context else 0.0
    return VerificationResult(
        verification_passed=passed,
        grounding_score=max(0.0, min(1.0, grounding)),
        completeness_score=completeness,
        feedback=(
            "Deterministic verifier fallback used because the LLM verifier returned malformed "
            f"structured output: {error}"
        ),
    )


def make_verifier(llm: LLMProvider):
    def verify_answer(state: AgentState) -> dict[str, Any]:
        if not state.get("is_cybersecurity_related", True):
            result = VerificationResult(
                verification_passed=True,
                grounding_score=1.0,
                completeness_score=1.0,
                feedback="Out-of-scope response is appropriate.",
            )
            timings = state.get("timings", {})
        else:
            allowed_sources = [
                doc.get("metadata", {}).get("filename") for doc in state.get("reranked_documents", [])
            ]
            prompt = f"""USER QUERY: {state['user_query']}
INCIDENT TYPE: {state.get('incident_type')}
RETRIEVED CONTEXT: {state.get('context', '')}
ALLOWED SOURCES: {allowed_sources}
DRAFT ANSWER:
{state.get('draft_answer', '')}"""
            try:
                result, timings = timed(
                    state,
                    "verification",
                    lambda: llm.generate_structured(VERIFICATION_SYSTEM, prompt, VerificationResult),
                )
            except Exception as exc:
                logger.warning("Verification failed: %s", exc)
                result = _deterministic_verification_fallback(state, exc)
                timings = state.get("timings", {})
        return {
            "verification_passed": result.verification_passed,
            "grounding_score": result.grounding_score,
            "completeness_score": result.completeness_score,
            "verification_feedback": result.feedback,
            "execution_trace": add_trace(
                state,
                "verify_answer",
                f"passed={result.verification_passed}; grounding={result.grounding_score:.2f}; completeness={result.completeness_score:.2f}",
            ),
            "timings": timings,
        }

    return verify_answer

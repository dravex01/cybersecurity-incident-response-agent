from __future__ import annotations

from typing import Any

from app.agent.nodes.common import add_trace
from app.agent.state import AgentState


def finalize_response(state: AgentState) -> dict[str, Any]:
    answer = state.get("draft_answer", "No response could be generated.").strip()
    warnings: list[str] = []
    if state.get("requires_rag") and not state.get("context"):
        warnings.append("The local knowledge base returned no usable context; procedural guidance is limited.")
    if not state.get("verification_passed", False):
        warnings.append(
            f"Automated verification did not pass after {state.get('retry_count', 0)} retries: "
            f"{state.get('verification_feedback', 'insufficient grounding')}"
        )
    if state.get("context_score", 1) < 0.3 and state.get("requires_rag"):
        warnings.append("Retrieved-context confidence is low; validate actions with a trained responder.")
    if warnings:
        answer += "\n\n> **Confidence warning:** " + " ".join(warnings)
    if state.get("is_cybersecurity_related", True):
        answer += "\n\n---\n*Defensive prototype guidance; it does not replace your incident-response team, legal counsel, or applicable reporting obligations.*"
    return {
        "final_answer": answer,
        "execution_trace": add_trace(state, "finalize_response", f"warnings={len(warnings)}"),
    }


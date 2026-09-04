from __future__ import annotations

from typing import Literal

from app.agent.state import AgentState


def route_after_plan(state: AgentState) -> Literal["rag", "risk", "generate"]:
    if state.get("requires_rag", False):
        return "rag"
    if state.get("requires_risk_analysis", False):
        return "risk"
    return "generate"


def route_after_rag(state: AgentState) -> Literal["risk", "generate"]:
    return "risk" if state.get("requires_risk_analysis", False) else "generate"


def route_after_verification(
    state: AgentState, max_retries: int
) -> Literal["finalize", "retry"]:
    if state.get("verification_passed", False):
        return "finalize"
    if state.get("retry_count", 0) < max_retries and state.get("requires_rag", False):
        return "retry"
    return "finalize"


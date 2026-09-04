from __future__ import annotations

import logging
from typing import Any

from app.agent.nodes.common import add_trace, timed
from app.agent.schemas import ExecutionPlan
from app.agent.state import AgentState
from app.llm.base import LLMProvider
from app.prompts.prompts import PLANNING_SYSTEM

logger = logging.getLogger(__name__)


def make_planner(llm: LLMProvider):
    def plan_response(state: AgentState) -> dict[str, Any]:
        def plan() -> ExecutionPlan:
            if not state.get("is_cybersecurity_related", True):
                return ExecutionPlan(steps=["respond with scope clarification and safe redirection"])
            prompt = (
                f"Query: {state['user_query']}\nIncident: {state.get('incident_type')}\n"
                f"Retrieval required: {state.get('requires_rag')}\nRisk required: {state.get('requires_risk_analysis')}"
            )
            try:
                return llm.generate_structured(PLANNING_SYSTEM, prompt, ExecutionPlan)
            except Exception as exc:
                logger.warning("Planning failed: %s", exc)
                steps = []
                if state.get("requires_rag"):
                    steps.append("retrieve relevant incident-response procedure")
                if state.get("requires_risk_analysis"):
                    steps.append("calculate deterministic risk")
                steps.append("generate and verify defensive guidance")
                return ExecutionPlan(steps=steps)

        result, timings = timed(state, "planning", plan)
        return {
            "plan": result.steps,
            "execution_trace": add_trace(state, "plan_response", f"steps={len(result.steps)}"),
            "timings": timings,
        }

    return plan_response


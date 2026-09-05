from __future__ import annotations

import re
from typing import Any

from app.agent.nodes.common import add_trace, timed
from app.agent.state import AgentState
from app.llm.base import LLMProvider
from app.prompts.prompts import GENERATION_SYSTEM


def _sources(state: AgentState) -> list[str]:
    values: list[str] = []
    for document in state.get("reranked_documents", []):
        metadata = document.get("metadata", {})
        filename = metadata.get("filename")
        if not filename:
            continue
        source = str(filename)
        if metadata.get("page"):
            source += f", page {metadata['page']}"
        if source not in values:
            values.append(source)
    return values


def make_generator(llm: LLMProvider):
    def generate_answer(state: AgentState) -> dict[str, Any]:
        if not state.get("is_cybersecurity_related", True):
            answer = (
                "This assistant is scoped to defensive cybersecurity incident response. "
                "The request does not appear security-related; please provide an incident, alert, "
                "account, endpoint, email, or data-protection question."
            )
            return {
                "draft_answer": answer,
                "execution_trace": add_trace(state, "generate_answer", "safe out-of-scope response"),
            }

        sources = _sources(state)
        prompt = f"""USER QUERY:
{state['user_query']}

CLASSIFICATION: {state.get('incident_type')} ({state.get('classification_confidence', 0):.2f})
PLAN: {state.get('plan', [])}
RISK: {state.get('risk_level', 'NOT CALCULATED')} {state.get('risk_score', '')}
RISK EXPLANATION: {state.get('risk_explanation', '')}

RETRIEVED CONTEXT:
{state.get('context', 'No retrieved context was available.')}

ALLOWED SOURCES: {sources}

PREVIOUS VERIFIER FEEDBACK: {state.get('verification_feedback', 'None')}

Write only these sections: Immediate recommended actions, Containment steps,
Investigation recommendations, Recovery / follow-up, Important uncertainties.
The program adds the authoritative classification, risk decision, and source list after generation,
so do not repeat them and do not include filenames, links, citations, or a Sources section.

Keep the generated content under 350 words. Cover every requested section before adding detail,
use short actionable bullets, and ensure every factual claim is supported by RETRIEVED CONTEXT or
clearly labeled as a conditional recommendation."""

        answer, timings = timed(state, "generation", lambda: llm.generate(GENERATION_SYSTEM, prompt))
        score = state.get("risk_score")
        # Replace entire generated decision/source sections, not just their headings.
        lines = []
        skip = False
        for line in answer.splitlines():
            heading = re.match(r"^\s*(?:#{1,6}\s+|\*\*)(.+)", line)
            normalized = line.strip().strip("#*_ :").lower()
            if heading:
                skip = normalized.startswith(("incident classification", "risk level", "sources used", "sources:"))
            if not skip:
                lines.append(line)
        answer = "\n".join(lines).strip()
        risk_text = (
            f"**{state.get('risk_level')} ({score}/100)** — calculated by the deterministic risk tool."
            if score is not None else "Not calculated: no incident risk assessment was requested."
        )
        if state.get("requires_risk_analysis") and score is None:
            risk_text = "Unavailable: risk-factor extraction failed; manual triage is required."
        answer = (
            "## Incident classification\n"
            f"**{state.get('incident_type', 'unknown')}** "
            f"(confidence {state.get('classification_confidence', 0):.2f}).\n\n"
            f"## Risk level\n{risk_text}\n\n{answer}"
        )
        if sources:
            answer = f"{answer.rstrip()}\n\n## Sources used\n" + "\n".join(f"- {source}" for source in sources)
        return {
            "draft_answer": answer,
            "execution_trace": add_trace(state, "generate_answer", f"characters={len(answer)}"),
            "timings": timings,
        }

    return generate_answer

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

Write only these sections: Immediate recommended actions, Containment steps,
Investigation recommendations, Recovery / follow-up, Important uncertainties.
The program adds the authoritative classification, risk decision, and source list after generation,
so do not repeat them and do not include filenames, links, citations, or a Sources section.

Keep the generated content under 350 words. Cover every requested section before adding detail,
use short actionable bullets, and ensure every factual claim is supported by RETRIEVED CONTEXT or
clearly labeled as a conditional recommendation."""

        answer, timings = timed(state, "generation", lambda: llm.generate(GENERATION_SYSTEM, prompt))
        score = state.get("risk_score")
        if score is not None:
            authoritative = f"{score}/100"
            filtered_lines = []
            for line in answer.splitlines():
                normalized = line.strip().strip("#*_ ").lower()
                generated_decision_line = normalized.startswith(
                    "incident classification"
                ) or normalized.startswith("risk level")
                conflicting_score = (
                    "risk score" in normalized
                    and authoritative not in line
                    and bool(re.search(r"\d", line))
                )
                if not generated_decision_line and not conflicting_score:
                    filtered_lines.append(line)
            answer = "\n".join(filtered_lines)
            answer = (
                "## Incident classification\n"
                f"**{state.get('incident_type', 'unknown')}** "
                f"(confidence {state.get('classification_confidence', 0):.2f}).\n\n"
                "## Risk level\n"
                f"**{state.get('risk_level')} ({authoritative})** — calculated by the "
                f"deterministic risk tool.\n\n{answer.lstrip()}"
            )
        if sources and "## Sources used" not in answer:
            answer = f"{answer.rstrip()}\n\n## Sources used\n" + "\n".join(f"- {source}" for source in sources)
        return {
            "draft_answer": answer,
            "execution_trace": add_trace(state, "generate_answer", f"characters={len(answer)}"),
            "timings": timings,
        }

    return generate_answer

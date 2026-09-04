from __future__ import annotations

import logging
from typing import Any

from app.agent.nodes.common import add_trace, timed
from app.agent.schemas import IncidentClassification, IncidentType, Severity
from app.agent.state import AgentState
from app.llm.base import LLMProvider
from app.prompts.prompts import CLASSIFICATION_SYSTEM

logger = logging.getLogger(__name__)


def make_classifier(llm: LLMProvider):
    def classify_query(state: AgentState) -> dict[str, Any]:
        def classify() -> IncidentClassification:
            try:
                return llm.generate_structured(
                    CLASSIFICATION_SYSTEM, f"USER QUERY:\n{state['user_query']}", IncidentClassification
                )
            except Exception as exc:
                logger.warning("Structured classification failed: %s", exc)
                return IncidentClassification(
                    incident_type=IncidentType.UNKNOWN,
                    apparent_severity=Severity.MEDIUM,
                    confidence=0.2,
                    rationale=f"Classification fallback used: {exc}",
                )

        result, timings = timed(state, "classification", classify)
        query = state["user_query"].lower()
        if (
            result.incident_type is IncidentType.UNKNOWN
            or not result.is_cybersecurity_related
        ):
            explicit_indicators = [
                (
                    IncidentType.RANSOMWARE,
                    ("ransom", "encrypted files", "ransom note", "zsarolóvírus", "titkosított fájl"),
                ),
                (
                    IncidentType.MALWARE,
                    ("powershell", "malware", "payload", "virus", "kártékony program"),
                ),
                (
                    IncidentType.PHISHING,
                    ("phishing", "suspicious email", "attachment", "adathalász", "gyanús e-mail"),
                ),
                (
                    IncidentType.DATA_BREACH,
                    (
                        "data breach",
                        "data leak",
                        "exfiltrat",
                        "adatszivárgás",
                        "adatlopás",
                        "ügyféladat",
                        "adat-export",
                        "adat export",
                        "érzékeny adat",
                    ),
                ),
                (
                    IncidentType.SUSPICIOUS_LOGIN,
                    (
                        "suspicious login",
                        "impossible travel",
                        "külföldi ip",
                        "gyanús bejelentkezés",
                        "sikeres belépés",
                        "új mfa-eszköz",
                        "új mfa eszköz",
                    ),
                ),
            ]
            for incident_type, indicators in explicit_indicators:
                if any(indicator in query for indicator in indicators):
                    result = result.model_copy(
                        update={
                            "incident_type": incident_type,
                            "is_cybersecurity_related": True,
                            "requires_rag": True,
                            "requires_risk_analysis": True,
                            "confidence": max(result.confidence, 0.75),
                            "rationale": (
                                f"Deterministic recovery recognized explicit {incident_type.value} indicators."
                            ),
                        }
                    )
                    break
        return {
            "intent": result.intent,
            "incident_type": result.incident_type.value,
            "apparent_severity": result.apparent_severity.value,
            "classification_confidence": result.confidence,
            "is_cybersecurity_related": result.is_cybersecurity_related,
            "requires_rag": result.requires_rag,
            "requires_risk_analysis": result.requires_risk_analysis,
            "execution_trace": add_trace(
                state, "classify_query", f"incident_type={result.incident_type.value}; confidence={result.confidence:.2f}"
            ),
            "timings": timings,
        }

    return classify_query

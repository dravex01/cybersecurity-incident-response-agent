from __future__ import annotations

import logging
from typing import Any

from app.agent.nodes.common import add_trace, timed
from app.agent.schemas import RiskFactors
from app.agent.state import AgentState
from app.llm.base import LLMProvider
from app.tools.risk_calculator import calculate_incident_risk

logger = logging.getLogger(__name__)

RISK_EXTRACTION_SYSTEM = """Extract only risk factors explicitly indicated by the incident description. Do not infer sensitive-data exposure, lateral movement, privilege, or ransomware without evidence. Return the supplied JSON schema."""


def make_risk_analyzer(llm: LLMProvider):
    def risk_analysis(state: AgentState) -> dict[str, Any]:
        def analyze():
            try:
                factors = llm.generate_structured(
                    RISK_EXTRACTION_SYSTEM, f"Incident description: {state['user_query']}", RiskFactors
                )
            except Exception as exc:
                logger.warning("Risk-factor extraction failed: %s", exc)
                raise RuntimeError("Risk assessment unavailable: model extraction failed. Retry when Ollama is ready; do not interpret this as Low risk.") from exc
            query = state["user_query"].lower()
            explicit = {
                "malware_execution": any(
                    value in query for value in ("powershell", "malware executed", "payload ran")
                ),
                "privileged_account_involved": any(
                    value in query for value in ("admin", "privileged", "domain controller", "root")
                ),
                "sensitive_data_exposed": any(
                    value in query
                    for value in (
                        "customer data",
                        "sensitive data",
                        "data leak",
                        "exfiltrat",
                        "ügyféladat",
                        "érzékeny adat",
                        "adatszivárg",
                        "adat-export",
                        "adat export",
                    )
                ),
                "external_access_detected": any(
                    value in query
                    for value in (
                        "external account",
                        "external access",
                        "foreign sign-in",
                        "külföldi ip",
                        "külföldi bejelentkezés",
                        "külső hozzáférés",
                        "külső fiók",
                    )
                ),
                "credential_compromise": any(
                    value in query
                    for value in (
                        "entered their password",
                        "stolen credential",
                        "token was posted",
                        "új mfa-eszköz",
                        "új mfa eszköz",
                        "új hitelesítési módszer",
                        "ellopott hitelesítő adat",
                        "megadta a jelszavát",
                    )
                ),
                "lateral_movement": any(
                    value in query for value in ("lateral movement", "spread to", "multiple hosts")
                ),
                "critical_asset_affected": any(
                    value in query for value in ("production server", "critical server", "domain controller")
                ),
                "ransomware_indicators": any(
                    value in query for value in ("ransom", "encrypted files", "ransom note")
                ),
            }
            factors = RiskFactors(
                **{
                    name: enabled or explicit[name]
                    for name, enabled in factors.model_dump().items()
                }
            )
            return factors, calculate_incident_risk(factors)

        (factors, result), timings = timed(state, "risk_analysis", analyze)
        return {
            "risk_factors": factors.model_dump(),
            "risk_score": result.score,
            "risk_level": result.level,
            "risk_explanation": result.explanation,
            "execution_trace": add_trace(state, "risk_analysis", f"level={result.level}; score={result.score}"),
            "timings": timings,
        }

    return risk_analysis

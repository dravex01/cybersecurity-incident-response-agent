from __future__ import annotations

import re

from app.agent.schemas import (
    ExecutionPlan,
    IncidentClassification,
    IncidentType,
    QueryRewrite,
    RiskEvidence,
    RiskFactors,
    Severity,
    VerificationResult,
)
from app.llm.base import LLMProvider, ModelT


def _classify(text: str) -> IncidentType:
    value = text.lower()
    rules = [
        (IncidentType.RANSOMWARE, ("ransom", "encrypted files", "decrypt", "zsarolóvírus")),
        (
            IncidentType.PHISHING,
            ("phish", "email", "attachment", "link", "mailbox", "malicious message", "adathalász"),
        ),
        (IncidentType.MALWARE, ("malware", "powershell", "virus", "payload", "kártevő")),
        (
            IncidentType.DATA_BREACH,
            (
                "breach",
                "exfiltrat",
                "data leak",
                "customer data",
                "data export",
                "adatszivárgás",
                "ügyféladat",
                "adat-export",
            ),
        ),
        (
            IncidentType.CREDENTIAL_COMPROMISE,
            ("password", "credential", "token", "account takeover", "jelszó", "hitelesítő adat"),
        ),
        (
            IncidentType.SUSPICIOUS_LOGIN,
            (
                "login",
                "sign-in",
                "impossible travel",
                "mfa prompt",
                "külföldi ip",
                "bejelentkezés",
                "belépés",
                "mfa-eszköz",
            ),
        ),
        (
            IncidentType.UNAUTHORIZED_ACCESS,
            ("unauthorized", "unknown user", "accessed", "jogosulatlan hozzáférés"),
        ),
    ]
    for incident, keywords in rules:
        if any(keyword in value for keyword in keywords):
            return incident
    security = ("security", "incident", "endpoint", "firewall", "soc", "account")
    return IncidentType.GENERAL_SECURITY_QUESTION if any(x in value for x in security) else IncidentType.UNKNOWN


class FakeLLMProvider(LLMProvider):
    """Deterministic provider for tests, evaluation, and offline demonstrations."""

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        query_match = re.search(r"USER QUERY:\s*(.*?)(?:\n\n|$)", user_prompt, re.S)
        query = query_match.group(1).strip() if query_match else user_prompt
        incident = _classify(query).value.replace("_", " ")
        risk_match = re.search(r"RISK:\s*([A-Z]+)\s*(\d*)", user_prompt)
        risk = (
            f"{risk_match.group(1)} ({risk_match.group(2)}/100)"
            if risk_match and risk_match.group(2)
            else "not calculated"
        )
        context_match = re.search(
            r"RETRIEVED CONTEXT:\s*(.*?)(?:\n\nALLOWED SOURCES:|$)", user_prompt, re.S
        )
        context = context_match.group(1).strip()[:2200] if context_match else ""
        return (
            f"## Incident classification\nLikely **{incident}** based on the reported indicators.\n\n"
            f"## Risk level\n**{risk}**. Escalate if impact expands.\n\n"
            "## Immediate recommended actions\n- Isolate affected endpoints or accounts without powering systems off.\n"
            "- Preserve evidence, record timestamps, and notify the incident-response lead.\n\n"
            "## Containment steps\n- Block known malicious indicators and revoke exposed sessions or credentials.\n"
            "- Scope related endpoints, accounts, mailboxes, and network activity.\n\n"
            "## Investigation recommendations\n- Investigate process execution, authentication logs, email headers, and endpoint telemetry.\n"
            "- Establish a timeline and determine whether lateral movement or data access occurred.\n\n"
            "## Recovery / follow-up\n- Remove persistence, rotate credentials, restore from known-good backups, and monitor for recurrence.\n\n"
            f"## Evidence-based procedure notes\n{context}\n\n"
            "## Important uncertainties\nThe exact impact and root cause require validation from host, identity, and network evidence."
        )

    def generate_structured(
        self, system_prompt: str, user_prompt: str, schema: type[ModelT]
    ) -> ModelT:
        incident = _classify(user_prompt)
        lower = user_prompt.lower()
        if schema is IncidentClassification:
            related = incident is not IncidentType.UNKNOWN
            severe = Severity.CRITICAL if incident is IncidentType.RANSOMWARE else Severity.MEDIUM
            return schema.model_validate(
                {
                    "intent": "incident_response" if related else "unrelated",
                    "incident_type": incident,
                    "apparent_severity": severe,
                    "is_cybersecurity_related": related,
                    "requires_rag": related,
                    "requires_risk_analysis": related and incident is not IncidentType.GENERAL_SECURITY_QUESTION,
                    "confidence": 0.86 if related else 0.7,
                    "rationale": "Deterministic keyword classification for offline execution.",
                }
            )
        if schema is ExecutionPlan:
            return schema.model_validate(
                {"steps": ["retrieve relevant response procedures", "calculate incident risk", "prepare grounded containment and investigation guidance"]}
            )
        if schema is QueryRewrite:
            return schema.model_validate({"query": f"{incident.value} incident response containment investigation evidence preservation"})
        if schema is RiskEvidence:
            indicators = {
                "malware_execution": ("powershell", "malware", "payload ran"),
                "privileged_account_involved": ("privileged", "admin", "root"),
                "sensitive_data_exposed": ("customer data", "data leak", "exfiltrat"),
                "external_access_detected": ("external", "foreign sign-in"),
                "credential_compromise": ("entered their password", "token was posted", "stolen credential"),
                "lateral_movement": ("lateral movement", "spread to", "multiple hosts"),
                "critical_asset_affected": ("production server", "critical server", "domain controller"),
                "ransomware_indicators": ("ransom", "encrypted files"),
            }
            return schema.model_validate({name: next((term for term in terms if term in lower), "")
                                          for name, terms in indicators.items()})
        if schema is RiskFactors:
            return schema.model_validate(
                {
                    "malware_execution": any(x in lower for x in ("powershell", "malware", "executed", "payload")),
                    "privileged_account_involved": any(x in lower for x in ("admin", "privileged", "root")),
                    "sensitive_data_exposed": any(x in lower for x in ("sensitive", "customer data", "exfiltrat", "leak")),
                    "external_access_detected": any(x in lower for x in ("external", "foreign", "internet", "remote")),
                    "credential_compromise": any(x in lower for x in ("password", "credential", "token", "account")),
                    "lateral_movement": any(x in lower for x in ("lateral", "multiple hosts", "spread")),
                    "critical_asset_affected": any(x in lower for x in ("critical", "domain controller", "production", "server")),
                    "ransomware_indicators": any(x in lower for x in ("ransom", "encrypted files", "decrypt")),
                }
            )
        if schema is VerificationResult:
            required = ("Incident classification", "Risk level", "Immediate recommended actions", "Containment", "Investigation", "Important uncertainties")
            completeness = sum(x.lower() in lower for x in required) / len(required)
            return schema.model_validate(
                {
                    "verification_passed": completeness >= 0.8,
                    "grounding_score": 0.85 if "retrieved context" in lower else 0.65,
                    "completeness_score": completeness,
                    "feedback": "All required operational sections should be present and cited.",
                }
            )
        raise TypeError(f"FakeLLMProvider does not support schema {schema.__name__}")

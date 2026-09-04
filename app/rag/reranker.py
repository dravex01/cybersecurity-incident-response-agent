from __future__ import annotations

import re
from typing import Any


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


INCIDENT_SOURCE_HINTS: dict[str, tuple[str, ...]] = {
    "phishing": ("phishing", "credential_compromise", "malware", "evidence"),
    "malware": ("malware", "powershell", "endpoint", "evidence"),
    "ransomware": ("ransomware", "backup", "incident_escalation", "evidence"),
    "credential_compromise": ("credential", "mfa", "suspicious_login", "evidence"),
    "suspicious_login": ("suspicious_login", "mfa", "credential", "evidence"),
    "data_breach": ("data_breach", "evidence", "incident_escalation", "unauthorized"),
    "unauthorized_access": ("unauthorized", "credential", "evidence", "incident_escalation"),
    "general_security_question": ("incident_response", "evidence", "endpoint"),
}


def rerank(
    query: str,
    documents: list[dict[str, Any]],
    enabled: bool = True,
    incident_type: str = "",
) -> list[dict[str, Any]]:
    if not enabled:
        return documents
    query_tokens = _tokens(query)
    results = []
    for document in documents:
        metadata = document.get("metadata", {})
        filename = str(metadata.get("filename", ""))
        searchable = " ".join(
            (
                str(document.get("content", "")),
                filename,
                str(metadata.get("title", "")),
            )
        )
        content_tokens = _tokens(searchable)
        lexical = len(query_tokens & content_tokens) / max(1, len(query_tokens))
        initial = float(document.get("similarity", 0.0))
        filename_tokens = _tokens(filename.removesuffix(".md").removesuffix(".txt"))
        incident_match_bonus = 0.15 if len(filename_tokens & query_tokens) >= 2 else 0.0
        source_hint_bonus = (
            0.18
            if any(hint in filename for hint in INCIDENT_SOURCE_HINTS.get(incident_type, ()))
            else 0.0
        )
        score = min(
            1.0,
            0.5 * initial + 0.5 * lexical + incident_match_bonus + source_hint_bonus,
        )
        results.append({**document, "rerank_score": round(score, 4)})
    return sorted(results, key=lambda item: item["rerank_score"], reverse=True)

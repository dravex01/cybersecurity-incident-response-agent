from __future__ import annotations

import re
from typing import Any


def source_names(result: dict[str, Any]) -> set[str]:
    return {
        str(document.get("metadata", {}).get("filename"))
        for document in result.get("reranked_documents", [])
        if document.get("metadata", {}).get("filename")
    }


def evaluate_case(case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    answer = result.get("final_answer", "").lower()
    actual_sources = source_names(result)
    expected_sources = set(case["expected_sources"])
    concepts = case["required_concepts"]
    concept_coverage = sum(
        any(term.lower() in answer for term in ([concept] if isinstance(concept, str) else concept))
        for concept in concepts
    ) / max(1, len(concepts))
    classification = result.get("incident_type") == case["expected_incident_type"]
    retrieval_required = bool(expected_sources)
    retrieval = bool(actual_sources & expected_sources) if retrieval_required else not actual_sources
    risk_required = case["expected_risk_level"] is not None
    risk = (str(result.get("risk_level", "")).lower() in case["expected_risk_level"]
            if risk_required else result.get("risk_score") is None)
    if "expected_risk_score" in case:
        risk = risk and result.get("risk_score") == case["expected_risk_score"]
    cited = set(re.findall(r"[\w.-]+\.(?:md|txt|pdf)\b", answer, re.IGNORECASE))
    valid_sources = {source.lower() for source in actual_sources}
    source_correctness = len(cited & valid_sources) / len(cited) if cited else float(not retrieval_required)
    groundedness = float(result.get("grounding_score", 0))
    success = (classification and retrieval and risk and concept_coverage >= 2 / 3
               and source_correctness == 1.0 and result.get("verification_passed", False))
    return {
        "id": case["id"],
        "risk_required": risk_required,
        "retrieval_required": retrieval_required,
        "classification_correct": classification,
        "retrieval_hit": retrieval,
        "risk_agreement": risk,
        "concept_coverage": concept_coverage,
        "source_correctness": source_correctness,
        "groundedness": groundedness,
        "verification_passed": result.get("verification_passed", False),
        "end_to_end_success": success,
        "actual_incident_type": result.get("incident_type"),
        "actual_risk_level": result.get("risk_level"),
        "actual_risk_score": result.get("risk_score"),
        "risk_factors": result.get("risk_factors", {}),
        "risk_evidence": result.get("risk_evidence", {}),
        "risk_keyword_factors": result.get("risk_keyword_factors", []),
        "actual_sources": sorted(actual_sources),
    }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(results)

    def mean(key: str, subset: list[dict[str, Any]] | None = None) -> float:
        items = results if subset is None else subset
        return sum(float(item[key]) for item in items) / max(1, len(items))

    return {
        "questions": count,
        "classification_accuracy": mean("classification_correct"),
        "retrieval_hit_rate": mean("retrieval_hit", [r for r in results if r["retrieval_required"]]),
        "risk_level_agreement": mean("risk_agreement", [r for r in results if r["risk_required"]]),
        "required_concept_coverage": mean("concept_coverage"),
        "source_correctness": mean("source_correctness"),
        "groundedness_heuristic": mean("groundedness"),
        "end_to_end_success_rate": mean("end_to_end_success"),
    }

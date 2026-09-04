from __future__ import annotations

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
    concept_coverage = sum(concept.lower() in answer for concept in concepts) / len(concepts)
    classification = result.get("incident_type") == case["expected_incident_type"]
    retrieval = bool(actual_sources & expected_sources)
    risk = str(result.get("risk_level", "")).lower() in case["expected_risk_level"]
    cited = {source for source in actual_sources if source.lower() in answer}
    source_correctness = len(cited) / max(1, len(actual_sources))
    groundedness = float(result.get("grounding_score", 0))
    success = classification and retrieval and risk and concept_coverage >= 2 / 3 and source_correctness >= 0.8
    return {
        "id": case["id"],
        "classification_correct": classification,
        "retrieval_hit": retrieval,
        "risk_agreement": risk,
        "concept_coverage": concept_coverage,
        "source_correctness": source_correctness,
        "groundedness": groundedness,
        "end_to_end_success": success,
        "actual_incident_type": result.get("incident_type"),
        "actual_risk_level": result.get("risk_level"),
        "actual_sources": sorted(actual_sources),
    }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(results)

    def mean(key: str) -> float:
        return sum(float(item[key]) for item in results) / max(1, count)

    return {
        "questions": count,
        "classification_accuracy": mean("classification_correct"),
        "retrieval_hit_rate": mean("retrieval_hit"),
        "risk_level_agreement": mean("risk_agreement"),
        "required_concept_coverage": mean("concept_coverage"),
        "source_correctness": mean("source_correctness"),
        "groundedness_heuristic": mean("groundedness"),
        "end_to_end_success_rate": mean("end_to_end_success"),
    }

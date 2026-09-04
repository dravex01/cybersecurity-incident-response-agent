from __future__ import annotations

from typing import Any


def context_quality(documents: list[dict[str, Any]]) -> float:
    if not documents:
        return 0.0
    scores = [float(item.get("rerank_score", item.get("similarity", 0.0))) for item in documents[:3]]
    coverage_bonus = min(0.12, 0.03 * len(documents))
    return round(min(1.0, (sum(scores) / len(scores)) + coverage_bonus), 4)


def context_is_sufficient(score: float, threshold: float) -> bool:
    return score >= threshold


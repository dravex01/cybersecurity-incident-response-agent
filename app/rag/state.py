from __future__ import annotations

from typing import Any, TypedDict


class RAGState(TypedDict, total=False):
    user_query: str
    incident_type: str
    rewritten_query: str
    retrieved_documents: list[dict[str, Any]]
    reranked_documents: list[dict[str, Any]]
    context: str
    context_score: float
    rag_retry_count: int
    max_rag_retries: int
    context_threshold: float
    execution_trace: list[dict[str, Any]]
    errors: list[str]


from __future__ import annotations

from typing import Any

from app.llm.ollama import OllamaProvider
from app.rag.retriever import Retriever


def health_check(llm: OllamaProvider, retriever: Retriever) -> dict[str, Any]:
    llm_health = llm.health()
    count = retriever.count()
    guidance: list[str] = []
    if not llm_health.get("reachable"):
        guidance.append(f"Ollama is unreachable at {llm.base_url}. Start it with: ollama serve")
    elif not llm_health.get("model_available"):
        guidance.append(f"Ollama is reachable but model {llm.model} is unavailable. Run: ollama pull {llm.model}")
    if count == 0:
        guidance.append("The vector database is empty. Run: python -m app.rag.ingestion")
    return {"ollama": llm_health, "vector_document_count": count, "healthy": not guidance, "guidance": guidance}


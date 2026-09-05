from __future__ import annotations

import os
from typing import Any

from app.llm.ollama import OllamaProvider
from app.rag.retriever import Retriever


def health_check(llm: OllamaProvider, retriever: Retriever) -> dict[str, Any]:
    llm_health = llm.health()
    count = retriever.count()
    guidance: list[str] = []
    containerized = os.environ.get("CONTAINERIZED") == "true"
    ollama_command = "docker compose up -d ollama" if containerized else "ollama serve"
    pull_command = "docker compose exec ollama ollama pull" if containerized else "ollama pull"
    ingest_command = "docker compose exec app python -m app.rag.ingestion" if containerized else "python -m app.rag.ingestion"
    if not llm_health.get("reachable"):
        guidance.append(f"Ollama is unreachable. Start it with: {ollama_command}")
    elif not llm_health.get("model_available"):
        guidance.append(f"Model {llm.model} is unavailable. Run: {pull_command} {llm.model}")
    if count == 0:
        guidance.append(f"The vector database is empty. Run: {ingest_command}")
    return {"ollama": llm_health, "vector_document_count": count, "healthy": not guidance, "guidance": guidance}

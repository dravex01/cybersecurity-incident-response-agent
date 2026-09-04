from __future__ import annotations

from typing import Any

from app.rag.retriever import Retriever


class KnowledgeSearchTool:
    name = "knowledge_base_search"
    description = "Search locally ingested defensive incident-response procedures."

    def __init__(self, retriever: Retriever, top_k: int = 5) -> None:
        self.retriever = retriever
        self.top_k = top_k

    def invoke(self, query: str) -> list[dict[str, Any]]:
        return self.retriever.search(query, self.top_k)


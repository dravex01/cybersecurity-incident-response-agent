from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

import chromadb

from app.rag.embeddings import EmbeddingFunction


class Retriever(Protocol):
    def search(self, query: str, top_k: int) -> list[dict[str, Any]]: ...

    def count(self) -> int: ...


class ChromaRetriever:
    def __init__(
        self,
        path: Path,
        collection_name: str,
        embedding_function: EmbeddingFunction,
    ) -> None:
        self.client = chromadb.PersistentClient(path=str(path))
        self.collection = self.client.get_or_create_collection(
            collection_name,
            embedding_function=embedding_function,  # type: ignore[arg-type]
            metadata={"hnsw:space": "cosine"},
        )

    def search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        if self.count() == 0:
            return []
        result = self.collection.query(query_texts=[query], n_results=min(top_k, self.count()))
        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metadata = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            {
                "id": item_id,
                "content": content,
                "metadata": meta or {},
                "similarity": max(0.0, min(1.0, 1.0 - float(distance))),
            }
            for item_id, content, meta, distance in zip(ids, docs, metadata, distances, strict=True)
        ]

    def count(self) -> int:
        return self.collection.count()

    def upsert(self, ids: list[str], documents: list[str], metadatas: list[dict[str, Any]]) -> None:
        self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    def clear(self) -> int:
        """Remove existing chunks before a full knowledge-base replacement."""
        ids = self.collection.get(include=[]).get("ids", [])
        if ids:
            self.collection.delete(ids=ids)
        return len(ids)


class InMemoryRetriever:
    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self.documents = documents

    def count(self) -> int:
        return len(self.documents)

    def search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        terms = set(query.lower().split())
        ranked = []
        for index, document in enumerate(self.documents):
            content_terms = set(str(document["content"]).lower().split())
            score = len(terms & content_terms) / max(1, len(terms))
            ranked.append({"id": document.get("id", str(index)), **document, "similarity": score})
        return sorted(ranked, key=lambda item: item["similarity"], reverse=True)[:top_k]

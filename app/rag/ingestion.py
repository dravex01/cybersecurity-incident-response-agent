from __future__ import annotations

import argparse
import hashlib
import logging
from pathlib import Path
from typing import Any

from app.config import Settings, get_settings
from app.logging_config import configure_logging
from app.rag.chunking import chunk_text
from app.rag.embeddings import EmbeddingFunction, SentenceTransformerEmbedding
from app.rag.loaders import load_directory
from app.rag.retriever import ChromaRetriever

logger = logging.getLogger(__name__)


def ingest(
    settings: Settings,
    embedding_function: EmbeddingFunction | None = None,
    source_path: Path | None = None,
) -> dict[str, int]:
    source = source_path or settings.knowledge_base_path
    documents = load_directory(source)
    embedding = embedding_function or SentenceTransformerEmbedding(settings.embedding_model)
    retriever = ChromaRetriever(settings.chroma_path, settings.collection_name, embedding)
    previous_ids = set(retriever.collection.get(include=[]).get("ids", []))
    ids: list[str] = []
    texts: list[str] = []
    metadatas: list[dict[str, Any]] = []
    for loaded in documents:
        for index, chunk in enumerate(
            chunk_text(loaded.text, settings.chunk_size, settings.chunk_overlap)
        ):
            stable = hashlib.sha256(
                f"{loaded.metadata['path']}:{loaded.metadata.get('page', 0)}:{index}:{chunk}".encode()
            ).hexdigest()[:24]
            ids.append(stable)
            texts.append(chunk)
            metadatas.append({**loaded.metadata, "chunk_id": stable, "chunk_index": index})
    if not texts:
        raise RuntimeError(f"No text chunks were produced from {source}")
    batch_size = 64
    for offset in range(0, len(texts), batch_size):
        retriever.upsert(
            ids[offset : offset + batch_size],
            texts[offset : offset + batch_size],
            metadatas[offset : offset + batch_size],
        )
    # Keep the previous index usable if parsing or embedding fails. Delete obsolete
    # chunks only after every new batch was successfully stored (not transactional).
    obsolete_ids = sorted(previous_ids - set(ids))
    for offset in range(0, len(obsolete_ids), batch_size):
        retriever.collection.delete(ids=obsolete_ids[offset : offset + batch_size])
    removed_chunks = len(obsolete_ids)
    logger.info("Ingested %s chunks from %s source documents", len(texts), len(documents))
    return {
        "source_documents": len(documents),
        "chunks": len(texts),
        "removed_chunks": removed_chunks,
        "collection_count": retriever.count(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest local incident-response documents into Chroma")
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    settings = get_settings()
    configure_logging(settings.log_level)
    result = ingest(settings, source_path=args.source)
    print(f"Ingestion complete: {result}")


if __name__ == "__main__":
    main()

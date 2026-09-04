from pathlib import Path

from app.config import Settings
from app.rag.embeddings import HashEmbedding
from app.rag.ingestion import ingest
from app.rag.retriever import ChromaRetriever


def test_document_ingestion_with_metadata(tmp_path: Path) -> None:
    source = tmp_path / "kb"
    source.mkdir()
    (source / "procedure.md").write_text("# Procedure\n\nIsolate the endpoint and preserve evidence. " * 20, encoding="utf-8")
    settings = Settings(
        _env_file=None,
        chroma_path=tmp_path / "chroma",
        knowledge_base_path=source,
        collection_name="test_ingestion",
        chunk_size=250,
        chunk_overlap=30,
    )
    embedding = HashEmbedding()
    stats = ingest(settings, embedding)
    retriever = ChromaRetriever(settings.chroma_path, settings.collection_name, embedding)
    result = retriever.search("isolate endpoint evidence", 2)
    assert stats["source_documents"] == 1
    assert stats["chunks"] > 1
    assert result[0]["metadata"]["filename"] == "procedure.md"
    assert result[0]["metadata"]["chunk_id"]

    (source / "procedure.md").write_text("Updated procedure: revoke sessions.", encoding="utf-8")
    refreshed = ingest(settings, embedding)
    assert refreshed["removed_chunks"] == stats["chunks"]
    assert refreshed["collection_count"] == 1

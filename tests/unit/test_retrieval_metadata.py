from app.rag.retriever import InMemoryRetriever


def test_retrieval_preserves_source_metadata() -> None:
    retriever = InMemoryRetriever(
        [{"content": "isolate malware endpoint", "metadata": {"filename": "malware.md", "page": 2}}]
    )
    result = retriever.search("malware isolate", 1)[0]
    assert result["metadata"] == {"filename": "malware.md", "page": 2}
    assert result["similarity"] > 0


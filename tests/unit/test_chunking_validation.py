from app.rag.chunking import chunk_text
from app.rag.validation import context_is_sufficient, context_quality


def test_chunking_has_overlap_and_no_empty_chunks() -> None:
    chunks = chunk_text("A sentence. " * 200, chunk_size=250, overlap=40)
    assert len(chunks) > 1
    assert all(chunks)
    assert max(map(len, chunks)) <= 250


def test_context_validation() -> None:
    docs = [{"similarity": 0.8}, {"similarity": 0.6}]
    score = context_quality(docs)
    assert score > 0.65
    assert context_is_sufficient(score, 0.65)
    assert context_quality([]) == 0


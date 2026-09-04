from app.llm.fake import FakeLLMProvider
from app.rag.graph import build_rag_graph
from app.rag.retriever import InMemoryRetriever


def test_rag_subgraph_rewrites_retrieves_and_validates() -> None:
    retriever = InMemoryRetriever(
        [
            {"content": "malware incident response containment isolate endpoint evidence investigation", "metadata": {"filename": "malware_response.md"}},
            {"content": "credential reset and revoke sessions", "metadata": {"filename": "credential.md"}},
        ]
    )
    graph = build_rag_graph(FakeLLMProvider(), retriever, top_k=2)
    result = graph.invoke(
        {"user_query": "PowerShell malware ran", "incident_type": "malware", "rag_retry_count": 0, "max_rag_retries": 1, "context_threshold": 0.2, "execution_trace": [], "errors": []}
    )
    assert result["rewritten_query"]
    assert result["reranked_documents"]
    assert "malware_response.md" in result["context"]
    assert result["context_score"] >= 0.2


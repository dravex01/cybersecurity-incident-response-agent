from __future__ import annotations

import streamlit as st

from app.agent.graph import build_agent_graph, initial_state
from app.config import get_settings
from app.health import health_check
from app.llm.ollama import OllamaProvider
from app.logging_config import configure_logging
from app.rag.embeddings import SentenceTransformerEmbedding
from app.rag.retriever import ChromaRetriever

st.set_page_config(page_title="Cybersecurity Incident Response Agent", page_icon="🛡️", layout="wide")
settings = get_settings()
configure_logging(settings.log_level)


@st.cache_resource
def resources():
    llm = OllamaProvider(
        settings.ollama_base_url,
        settings.ollama_model,
        num_ctx=settings.ollama_num_ctx,
    )
    retriever = ChromaRetriever(
        settings.chroma_path,
        settings.collection_name,
        SentenceTransformerEmbedding(settings.embedding_model),
    )
    return llm, retriever, build_agent_graph(llm, retriever, settings)


llm, retriever, graph = resources()
st.title("🛡️ Cybersecurity Incident Response Agent")
st.caption("Local-first Agentic RAG for defensive triage, containment, investigation, and recovery guidance.")

with st.sidebar:
    st.header("System health")
    health = health_check(llm, retriever)
    st.metric("Knowledge chunks", health["vector_document_count"])
    if health["healthy"]:
        st.success(f"Ollama and {settings.ollama_model} are ready")
    else:
        for message in health["guidance"]:
            st.warning(message)
    st.caption("Never paste secrets, credentials, or unnecessary personal data.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if result := message.get("result"):
            with st.expander("Agent execution"):
                for item in result.get("execution_trace", []):
                    icon = "✓" if item.get("status") == "completed" else "!"
                    st.write(f"{icon} **{item.get('node')}** — {item.get('details')}")
                st.json(result.get("timings", {}))
            with st.expander("Retrieved context"):
                for document in result.get("reranked_documents", []):
                    metadata = document.get("metadata", {})
                    st.markdown(f"**{metadata.get('filename', 'unknown')}** · score {document.get('rerank_score', 0):.2f}")
                    st.text(document.get("content", "")[:1200])
            with st.expander("Risk result"):
                st.metric(result.get("risk_level", "N/A"), result.get("risk_score", 0))
                st.write(result.get("risk_explanation", "Risk analysis was not required."))
            with st.expander("System/debug information"):
                st.json(
                    {
                        "incident_type": result.get("incident_type"),
                        "context_score": result.get("context_score"),
                        "grounding_score": result.get("grounding_score"),
                        "completeness_score": result.get("completeness_score"),
                        "errors": result.get("errors", []),
                    }
                )

if query := st.chat_input("Describe the incident or ask a defensive response question"):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    with st.chat_message("assistant"):
        if not health["healthy"]:
            st.error("The system is not ready. Follow the health guidance in the sidebar.")
        else:
            with st.spinner("Analyzing incident…"):
                try:
                    result = graph.invoke(initial_state(query))
                    answer = result["final_answer"]
                    st.markdown(answer)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer, "result": result}
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"The analysis could not be completed: {exc}")

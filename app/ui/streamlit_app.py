from __future__ import annotations

import time

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
        timeout=settings.ollama_timeout_seconds,
        num_ctx=settings.ollama_num_ctx,
        num_predict=settings.ollama_num_predict,
        think=settings.ollama_think,
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
    st.caption("Each message is analyzed independently; chat history is for display only.")
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.info("Describe what happened, which account or system is affected, and what evidence is available. Hungarian and English inputs are supported. CPU inference can take several minutes.")
    st.caption('Example: "An external account downloaded a customer data export."')

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

if query := st.chat_input("Describe the incident or ask a defensive response question", disabled=not health["healthy"], max_chars=8000):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    with st.chat_message("assistant"):
        if not health["healthy"]:
            st.error("The system is not ready. Follow the health guidance in the sidebar.")
        else:
            with st.status("Analyzing incident…", expanded=True) as progress:
                try:
                    started = time.perf_counter()
                    result = initial_state(query)
                    labels = {
                        "classify_query": "Incident classified",
                        "plan_response": "Response plan prepared",
                        "execute_knowledge_retrieval": "Knowledge base searched and context checked",
                        "risk_analysis": "Risk factors assessed",
                        "generate_answer": "Response drafted",
                        "verify_answer": "Response verification completed",
                        "increment_agent_retry": "Improving the response using verifier feedback",
                        "finalize_response": "Analysis complete",
                    }
                    for update in graph.stream(result, stream_mode="updates"):
                        for node, values in update.items():
                            result.update(values)
                            elapsed = time.perf_counter() - started
                            st.write(f"{labels.get(node, node)} · {elapsed:.1f} s")
                    result["total_seconds"] = time.perf_counter() - started
                    progress.update(label=f"Complete in {result['total_seconds']:.1f} s", state="complete", expanded=False)
                    answer = result["final_answer"]
                    st.markdown(answer)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer, "result": result}
                    )
                    st.rerun()
                except Exception as exc:
                    progress.update(label="Analysis could not finish", state="error")
                    st.error(f"The analysis could not be completed: {exc}")

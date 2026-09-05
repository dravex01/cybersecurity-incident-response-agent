from __future__ import annotations

import logging
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from app.agent.schemas import QueryRewrite
from app.llm.base import LLMProvider
from app.prompts.prompts import REWRITE_SYSTEM
from app.rag.reranker import rerank
from app.rag.retriever import Retriever
from app.rag.state import RAGState
from app.rag.validation import context_is_sufficient, context_quality
from app.tools.knowledge_search import KnowledgeSearchTool

logger = logging.getLogger(__name__)


def _trace(state: RAGState, node: str, details: str) -> list[dict[str, Any]]:
    return [*state.get("execution_trace", []), {"node": node, "status": "completed", "details": details}]


def build_rag_graph(
    llm: LLMProvider,
    retriever: Retriever,
    *,
    top_k: int = 5,
    enable_reranker: bool = True,
):
    def rewrite_query(state: RAGState) -> dict[str, Any]:
        original = state.get("rewritten_query") or state["user_query"]
        prompt = f"Incident type: {state.get('incident_type', 'unknown')}\nQuery: {original}\nRetry: {state.get('rag_retry_count', 0)}"
        try:
            rewritten = llm.generate_structured(REWRITE_SYSTEM, prompt, QueryRewrite).query
        except Exception as exc:
            logger.warning("Query rewrite failed: %s", exc)
            rewritten = f"{original} incident response containment investigation"
        if state["user_query"].lower() not in rewritten.lower():
            rewritten = f"{rewritten} | Original indicators: {state['user_query']}"
        return {
            "rewritten_query": rewritten,
            "execution_trace": _trace(state, "rag.rewrite_query", rewritten),
        }

    def retrieve_documents(state: RAGState) -> dict[str, Any]:
        candidate_k = min(20, max(top_k, top_k * 2))
        documents = KnowledgeSearchTool(retriever, candidate_k).invoke(state["rewritten_query"])
        errors = state.get("errors", [])
        if not documents:
            errors = [*errors, "Knowledge retrieval returned no documents. Run ingestion first."]
        return {
            "retrieved_documents": documents,
            "errors": errors,
            "execution_trace": _trace(state, "rag.retrieve_documents", f"chunks={len(documents)}"),
        }

    def rerank_documents(state: RAGState) -> dict[str, Any]:
        ranked = rerank(
            state["rewritten_query"],
            state.get("retrieved_documents", []),
            enable_reranker,
            state.get("incident_type", ""),
        )
        documents: list[dict[str, Any]] = []
        seen_sources: set[str] = set()
        for document in ranked:
            source = str(document.get("metadata", {}).get("filename", document.get("id", "")))
            if source in seen_sources:
                continue
            seen_sources.add(source)
            documents.append(document)
            if len(documents) == top_k:
                break
        return {
            "reranked_documents": documents,
            "execution_trace": _trace(state, "rag.rerank_documents", f"enabled={enable_reranker}"),
        }

    def validate_context(state: RAGState) -> dict[str, Any]:
        documents = state.get("reranked_documents", [])
        score = context_quality(documents)
        context = "\n\n".join(
            f"[SOURCE: {doc.get('metadata', {}).get('filename', 'unknown')}]\n{doc.get('content', '')}"
            for doc in documents
        )
        sufficient = context_is_sufficient(score, state.get("context_threshold", 0.45))
        return {
            "context": context,
            "context_score": score,
            "execution_trace": _trace(state, "rag.validate_context", f"score={score:.2f}; sufficient={sufficient}"),
        }

    def route_context(state: RAGState) -> Literal["retry", "done"]:
        sufficient = context_is_sufficient(
            state.get("context_score", 0), state.get("context_threshold", 0.45)
        )
        retries = state.get("rag_retry_count", 0)
        if not sufficient and retries < state.get("max_rag_retries", 1):
            return "retry"
        return "done"

    def increment_retry(state: RAGState) -> dict[str, Any]:
        retry = state.get("rag_retry_count", 0) + 1
        return {
            "rag_retry_count": retry,
            "rewritten_query": f"{state.get('rewritten_query', state['user_query'])} procedures playbook escalation",
            "execution_trace": _trace(state, "rag.retry", f"attempt={retry}"),
        }

    workflow = StateGraph(RAGState)
    workflow.add_node("rewrite_query", rewrite_query)
    workflow.add_node("retrieve_documents", retrieve_documents)
    workflow.add_node("rerank_documents", rerank_documents)
    workflow.add_node("validate_context", validate_context)
    workflow.add_node("increment_retry", increment_retry)
    workflow.add_edge(START, "rewrite_query")
    workflow.add_edge("rewrite_query", "retrieve_documents")
    workflow.add_edge("retrieve_documents", "rerank_documents")
    workflow.add_edge("rerank_documents", "validate_context")
    workflow.add_conditional_edges("validate_context", route_context, {"retry": "increment_retry", "done": END})
    workflow.add_edge("increment_retry", "rewrite_query")
    return workflow.compile()

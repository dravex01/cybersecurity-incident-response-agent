from __future__ import annotations

import logging
import time
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agent.nodes.classifier import make_classifier
from app.agent.nodes.common import add_trace
from app.agent.nodes.finalizer import finalize_response
from app.agent.nodes.generator import make_generator
from app.agent.nodes.planner import make_planner
from app.agent.nodes.risk_analysis import make_risk_analyzer
from app.agent.nodes.verifier import make_verifier
from app.agent.routing import route_after_plan, route_after_rag, route_after_verification
from app.agent.state import AgentState
from app.config import Settings
from app.llm.base import LLMProvider
from app.rag.graph import build_rag_graph
from app.rag.retriever import Retriever

logger = logging.getLogger(__name__)


def build_agent_graph(llm: LLMProvider, retriever: Retriever, settings: Settings):
    rag_graph = build_rag_graph(
        llm, retriever, top_k=settings.top_k, enable_reranker=settings.enable_reranker
    )

    def execute_knowledge_retrieval(state: AgentState) -> dict[str, Any]:
        started = time.perf_counter()
        result = rag_graph.invoke(
            {
                "user_query": state["user_query"],
                "incident_type": state.get("incident_type", "unknown"),
                "rewritten_query": state.get("rewritten_query", ""),
                "rag_retry_count": 0,
                "max_rag_retries": settings.max_rag_retries,
                "context_threshold": settings.context_threshold,
                "execution_trace": state.get("execution_trace", []),
                "errors": state.get("errors", []),
            }
        )
        timings = {
            **state.get("timings", {}),
            "retrieval": round(state.get("timings", {}).get("retrieval", 0.0) + time.perf_counter() - started, 6),
        }
        return {
            "rewritten_query": result.get("rewritten_query", ""),
            "retrieved_documents": result.get("retrieved_documents", []),
            "reranked_documents": result.get("reranked_documents", []),
            "context": result.get("context", ""),
            "context_score": result.get("context_score", 0.0),
            "execution_trace": result.get("execution_trace", state.get("execution_trace", [])),
            "errors": result.get("errors", state.get("errors", [])),
            "timings": timings,
        }

    def increment_agent_retry(state: AgentState) -> dict[str, Any]:
        retry = state.get("retry_count", 0) + 1
        return {
            "retry_count": retry,
            "rewritten_query": (
                f"{state.get('rewritten_query', state['user_query'])} "
                f"address verifier feedback {state.get('verification_feedback', '')}"
            ),
            "execution_trace": add_trace(state, "agent.retry", f"attempt={retry}"),
        }

    graph = StateGraph(AgentState)
    graph.add_node("classify_query", make_classifier(llm))
    graph.add_node("plan_response", make_planner(llm))
    graph.add_node("execute_knowledge_retrieval", execute_knowledge_retrieval)
    graph.add_node("risk_analysis", make_risk_analyzer(llm))
    graph.add_node("generate_answer", make_generator(llm))
    graph.add_node("verify_answer", make_verifier(llm))
    graph.add_node("increment_agent_retry", increment_agent_retry)
    graph.add_node("finalize_response", finalize_response)
    graph.add_edge(START, "classify_query")
    graph.add_edge("classify_query", "plan_response")
    graph.add_conditional_edges(
        "plan_response",
        route_after_plan,
        {"rag": "execute_knowledge_retrieval", "risk": "risk_analysis", "generate": "generate_answer"},
    )
    graph.add_conditional_edges(
        "execute_knowledge_retrieval",
        route_after_rag,
        {"risk": "risk_analysis", "generate": "generate_answer"},
    )
    graph.add_edge("risk_analysis", "generate_answer")
    graph.add_edge("generate_answer", "verify_answer")
    graph.add_conditional_edges(
        "verify_answer",
        lambda state: route_after_verification(state, settings.max_agent_retries),
        {"retry": "increment_agent_retry", "finalize": "finalize_response"},
    )
    graph.add_edge("increment_agent_retry", "execute_knowledge_retrieval")
    graph.add_edge("finalize_response", END)
    return graph.compile().with_config({"recursion_limit": 64})


def initial_state(query: str) -> AgentState:
    return {
        "user_query": query,
        "retry_count": 0,
        "execution_trace": [],
        "errors": [],
        "timings": {},
    }

from __future__ import annotations

import argparse
import json

from app.agent.graph import build_agent_graph, initial_state
from app.config import get_settings
from app.llm import FakeLLMProvider, OllamaProvider
from app.logging_config import configure_logging
from app.rag.embeddings import SentenceTransformerEmbedding
from app.rag.retriever import ChromaRetriever


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one incident-response query")
    parser.add_argument("query")
    parser.add_argument("--fake-llm", action="store_true", help="Use deterministic offline provider")
    args = parser.parse_args()
    settings = get_settings()
    configure_logging(settings.log_level)
    llm = (
        FakeLLMProvider()
        if args.fake_llm
        else OllamaProvider(
            settings.ollama_base_url,
            settings.ollama_model,
            timeout=settings.ollama_timeout_seconds,
            num_ctx=settings.ollama_num_ctx,
            num_predict=settings.ollama_num_predict,
            think=settings.ollama_think,
        )
    )
    retriever = ChromaRetriever(
        settings.chroma_path,
        settings.collection_name,
        SentenceTransformerEmbedding(settings.embedding_model),
    )
    result = build_agent_graph(llm, retriever, settings).invoke(initial_state(args.query))
    print(result["final_answer"])
    print("\nExecution metadata:")
    print(json.dumps({"trace": result.get("execution_trace"), "timings": result.get("timings")}, indent=2))


if __name__ == "__main__":
    main()

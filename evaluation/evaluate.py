from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from app.agent.graph import build_agent_graph, initial_state
from app.config import get_settings
from app.llm import FakeLLMProvider, OllamaProvider
from app.rag.embeddings import SentenceTransformerEmbedding
from app.rag.retriever import ChromaRetriever
from evaluation.metrics import evaluate_case, summarize


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the 15-case functional evaluation")
    parser.add_argument("--real-llm", action="store_true", help="Use configured Ollama rather than FakeLLM")
    args = parser.parse_args()
    settings = get_settings()
    cases = json.loads(Path("evaluation/questions.json").read_text(encoding="utf-8"))
    if len(cases) != 15:
        raise RuntimeError(f"Evaluation dataset must contain exactly 15 cases, found {len(cases)}")
    llm = (
        OllamaProvider(
            settings.ollama_base_url,
            settings.ollama_model,
            num_ctx=settings.ollama_num_ctx,
        )
        if args.real_llm
        else FakeLLMProvider()
    )
    retriever = ChromaRetriever(
        settings.chroma_path, settings.collection_name, SentenceTransformerEmbedding(settings.embedding_model)
    )
    if retriever.count() == 0:
        raise RuntimeError("Chroma is empty. Run: python -m app.rag.ingestion")
    graph = build_agent_graph(llm, retriever, settings)
    records = [evaluate_case(case, graph.invoke(initial_state(case["question"]))) for case in cases]
    summary = summarize(records)
    output = {"mode": "ollama" if args.real_llm else "deterministic_fake_llm", "summary": summary, "cases": records}
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    (results_dir / "evaluation_results.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    with (results_dir / "evaluation_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    print(f"Questions: {summary['questions']}")
    for key, value in summary.items():
        if key != "questions":
            print(f"{key.replace('_', ' ').title()}: {value:.1%}")
    print("Results: results/evaluation_results.json and results/evaluation_results.csv")


if __name__ == "__main__":
    main()

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
from evaluation.provenance import provenance


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the 10-20 case functional evaluation")
    parser.add_argument("--real-llm", action="store_true", help="Use configured Ollama rather than FakeLLM")
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--case-id", action="append", help="Run selected cases for a real-model smoke test")
    args = parser.parse_args()
    settings = get_settings()
    cases = json.loads(Path("evaluation/questions.json").read_text(encoding="utf-8"))
    if not 10 <= len(cases) <= 20:
        raise RuntimeError(f"Evaluation dataset must contain 10-20 cases, found {len(cases)}")
    if args.case_id:
        missing = set(args.case_id) - {case["id"] for case in cases}
        if missing:
            parser.error(f"Unknown case IDs: {sorted(missing)}")
        cases = [case for case in cases if case["id"] in args.case_id]
    llm = (
        OllamaProvider(
            settings.ollama_base_url,
            settings.ollama_model,
            num_ctx=settings.ollama_num_ctx,
            num_predict=settings.ollama_num_predict,
            timeout=settings.ollama_timeout_seconds,
            think=settings.ollama_think,
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
    records = []
    for case in cases:
        import time

        started = time.perf_counter()
        try:
            result = graph.invoke(initial_state(case["question"]))
            record = evaluate_case(case, result)
            record.update(error="", answer=result["final_answer"], trace=result.get("execution_trace", []),
                          timings=result.get("timings", {}), feedback=result.get("verification_feedback", ""))
        except Exception as exc:
            record = evaluate_case(case, {})
            record.update(error=str(exc), answer="", trace=[], timings={}, feedback="")
        record["latency_seconds"] = time.perf_counter() - started
        records.append(record)
        print(f"{case['id']}: {'PASS' if record['end_to_end_success'] else 'FAIL'}", flush=True)
    summary = summarize(records)
    output = {"mode": "ollama" if args.real_llm else "deterministic_fake_llm", "provenance": provenance(settings), "summary": summary, "cases": records}
    results_dir = args.output_dir
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "evaluation_results.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    with (results_dir / "evaluation_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    print(f"Questions: {summary['questions']}")
    for key, value in summary.items():
        if key != "questions":
            print(f"{key.replace('_', ' ').title()}: {value:.1%}")
    print(f"Results: {results_dir}/evaluation_results.json and evaluation_results.csv")


if __name__ == "__main__":
    main()

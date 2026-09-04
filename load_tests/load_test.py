from __future__ import annotations

import argparse
import csv
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from app.agent.graph import build_agent_graph, initial_state
from app.config import get_settings
from app.llm import FakeLLMProvider, OllamaProvider
from app.rag.embeddings import SentenceTransformerEmbedding
from app.rag.retriever import ChromaRetriever


def percentile(values: list[float], percent: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int((len(ordered) - 1) * percent)))
    return ordered[index]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run 50-200 local agent queries")
    parser.add_argument("--requests", type=int, default=100, choices=range(50, 201), metavar="50..200")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--real-llm", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    llm = (
        OllamaProvider(
            settings.ollama_base_url,
            settings.ollama_model,
            num_ctx=settings.ollama_num_ctx,
        )
        if args.real_llm
        else FakeLLMProvider()
    )
    retriever = ChromaRetriever(settings.chroma_path, settings.collection_name, SentenceTransformerEmbedding(settings.embedding_model))
    if retriever.count() == 0:
        raise RuntimeError("Chroma is empty. Run ingestion before load testing.")
    graph = build_agent_graph(llm, retriever, settings)
    questions = [item["question"] for item in json.loads(Path("evaluation/questions.json").read_text(encoding="utf-8"))]

    warmup_started = time.perf_counter()
    graph.invoke(initial_state(questions[0]))
    warmup_seconds = time.perf_counter() - warmup_started

    def run(index: int) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            result = graph.invoke(initial_state(questions[index % len(questions)]))
            return {"index": index, "success": True, "latency": time.perf_counter() - started, "error": "", **{f"stage_{k}": v for k, v in result.get("timings", {}).items()}}
        except Exception as exc:
            return {"index": index, "success": False, "latency": time.perf_counter() - started, "error": str(exc)}

    overall = time.perf_counter()
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        records = list(as_completed([pool.submit(run, i) for i in range(args.requests)]))
        records = [future.result() for future in records]
    duration = time.perf_counter() - overall
    latencies = [record["latency"] for record in records]
    succeeded = sum(record["success"] for record in records)
    stage_keys = sorted({key for record in records for key in record if key.startswith("stage_")})
    stages = {key.removeprefix("stage_"): statistics.mean([r[key] for r in records if key in r]) for key in stage_keys}
    summary = {
        "mode": "ollama" if args.real_llm else "deterministic_fake_llm",
        "request_count": args.requests,
        "successful_requests": succeeded,
        "failed_requests": args.requests - succeeded,
        "min_latency_seconds": min(latencies),
        "max_latency_seconds": max(latencies),
        "mean_latency_seconds": statistics.mean(latencies),
        "median_latency_seconds": statistics.median(latencies),
        "p95_latency_seconds": percentile(latencies, 0.95),
        "p99_latency_seconds": percentile(latencies, 0.99),
        "throughput_queries_per_second": args.requests / duration,
        "error_rate": (args.requests - succeeded) / args.requests,
        "mean_stage_timings_seconds": stages,
        "unmeasured_warmup_seconds": warmup_seconds,
        "measured_wall_time_seconds": duration,
    }
    output = Path("results")
    output.mkdir(exist_ok=True)
    (output / "load_test_results.json").write_text(json.dumps({"summary": summary, "requests": records}, indent=2), encoding="utf-8")
    with (output / "load_test_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted({key for record in records for key in record}))
        writer.writeheader()
        writer.writerows(records)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

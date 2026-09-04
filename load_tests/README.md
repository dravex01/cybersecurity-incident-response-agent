# Load test

Run `python -m load_tests.load_test --requests 100`. One unmeasured warm-up initializes models and is reported separately. The default deterministic mode measures graph, embedding query, retrieval, routing, and Python overhead without claiming local-model inference performance. Use `--real-llm --workers 1` for a resource-conscious Ollama measurement. Results include latency percentiles, throughput, errors, and mean node-stage timing.

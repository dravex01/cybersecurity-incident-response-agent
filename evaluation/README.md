# Functional evaluation

`python -m evaluation.evaluate` runs exactly 15 varied cases with the deterministic FakeLLM while retaining real local embedding and Chroma retrieval. Add `--real-llm` to measure the configured Ollama model. Metrics are property- and concept-based rather than exact-string matching. The groundedness score is the agent verifier's prototype heuristic, not a scientific or human-judge score.


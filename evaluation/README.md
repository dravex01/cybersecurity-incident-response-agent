# Functional evaluation

`python -m evaluation.evaluate` runs 20 development cases with deterministic FakeLLM and real embeddings/Chroma. Use `--real-llm` for Ollama, repeat `--case-id ID` for a smoke subset, and set `--output-dir PATH` to retain a separate run. Per-case failures are recorded without aborting the dataset.

Risk is explicitly optional for general/out-of-scope cases and is excluded from risk-agreement averages when not required. Filename precision detects invented `.md`, `.txt` and `.pdf` citations; it does not establish claim-level support. Concept lists allow alternative bilingual terms. End-to-end success also requires verification to pass. The fake provider's fixed grounding heuristic is not an independent quality metric.

Committed examples are in `reports/functional/` and `reports/ollama-smoke/`; the root README explains limitations and reproducibility.

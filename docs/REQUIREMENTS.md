# Assignment compliance map

Reviewed against the three-page **Medior AI Engineer / Agentic RAG Chatbot Prototype** assignment on 2026-09-05. This map distinguishes required functionality from prototype limitations; it does not claim production certification.

| Assignment requirement | Implementation and review evidence |
|---|---|
| Relevant problem and user need, with rationale | README: incident responders need evidence-backed triage of incomplete incident descriptions; conditional retrieval and deterministic scoring justify agentic RAG. |
| Python and LangGraph, at least five main nodes | `app/agent/graph.py`: eight main nodes; the RAG subgraph's five nodes are additional and are not counted toward the minimum. |
| Autonomous decisions | Classification sets routing flags; conditional edges select retrieval/risk/direct response and bounded verification retries. |
| Decomposition and execution | `plan_response` creates a per-query plan; dedicated retrieval, risk, generation, and verification nodes execute the required subtasks. The plan is advisory; typed routing flags control tool execution. |
| Intermediate state | `AgentState` and `RAGState` TypedDicts contain artifacts, flags, retries, scores, errors, and accumulated timings. |
| Two tools, including a non-retrieval tool | `KnowledgeSearchTool.invoke` is called inside the RAG graph; `calculate_incident_risk` is called by the main risk node. Both are local Python tools, not automatic external actions. |
| Dedicated modular RAG subgraph | Separately compiled `app/rag/graph.py`, invoked and mapped into the main state. Standalone subgraph integration tests included. |
| Textual source and quality processing | 15 original demonstration procedures; Markdown/text/PDF loaders, overlapping chunks, metadata/page tracking, stable IDs, batched upserts and removal of obsolete chunks after successful embedding. |
| Free local model and trade-offs | Ollama `qwen3:8b`; CPU-compatible default, configured context/output/time limits. Deterministic dummy provider available explicitly for reproducible tests and evaluation. |
| Streamlit UI demonstrating agent and RAG | Live main-node progress, execution trace, per-stage timing, retrieved text and source metadata, risk and verification details, readiness checks, session history. AppTest exercises the chat flow. |
| Mandatory Dockerfile; Compose bonus | Digest-pinned Python image, pinned Linux runtime, non-root user, health check; Compose joins application and Ollama with durable model/index/cache volumes. Built from source with Docker, not from a manually committed container. |
| 10-20 question functional evaluation | `evaluation/questions.json`: 20 cases including Hungarian, uncertainty, unrelated text and quoted prompt injection. Runner emits per-case evidence and summary JSON/CSV. |
| 50-200 request load scenario | `load_tests/load_test.py`: 100-request submitted run, configurable within 50-200, concurrency, separate warm-up, percentiles/throughput/errors and accumulated stage timings. |
| Bottleneck and 1-2 optimizations | README and committed measurement artifacts distinguish dummy-mode retrieval overhead from real LLM inference. Suggestions are explicitly proposals, not unmeasured speed claims. |
| Git repository with documentation and results | README, this map, source, tests, pinned runtime, CI workflow, and `reports/` raw evaluation/load evidence. Secrets, model binaries and local vector databases are excluded. |

## Review boundaries

- A passing dummy-model evaluation is a development regression result. The fake generator repeats retrieved context and its verifier uses a fixed heuristic; those scores cannot establish real-model answer quality.
- Real-model smoke results are separate from the 20-case dummy evaluation. They do not represent a 20-case real-model benchmark or a real-model load test.
- The 20 cases are a small synthetic development set, not held-out research data. English concept checks permit explicit Hungarian alternatives for Hungarian cases; they remain coarse keyword checks.
- Risk weights are application policy. Model factors require verbatim input excerpts, with separate keyword-recovery metadata. Verbatim matching cannot establish semantic support; extraction and keyword recovery can misinterpret negation or hypothetical descriptions. Scores are provisional, not an industry-standard severity scale.
- Chat turns are independent. There is no cross-turn incident memory or concurrent multi-user isolation. The UI explains this explicitly.
- Ingestion is incremental replacement, not transactional: old chunks survive a failed update, but a failure after some batches may leave a mixed index. Re-run ingestion after fixing the error.
- UI health checks prove the server is alive; the sidebar separately checks the model tag and index contents. An actual model query is the stronger integration test.
- The provided Docker configuration is tested on Linux x86-64 containers under Docker Desktop. No GPU runtime configuration is assumed.

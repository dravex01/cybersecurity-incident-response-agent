# Reviewer walkthrough

1. Follow **Docker quick start** in the README. After explicit model download and ingestion, open `http://localhost:8501`.
2. Confirm the sidebar reports the configured model and 40 knowledge chunks from the supplied corpus.
3. Submit: `An external account downloaded a customer data export from cloud storage.` Watch each main step complete. Inspect **Agent execution**, **Retrieved context**, **Risk result**, and **System/debug information**.
4. The reported download should trigger retrieval and risk analysis. The exact example has two supported factors: external access and sensitive-data exposure, totaling 45/100 (High). Inspect their verbatim evidence and any keyword-recovered factors in **Risk result**. Do not infer administrator privileges, credential theft or critical infrastructure from an ordinary external account/cloud-storage reference. A short incident description is not proof that access was unauthorized: review the uncertainties.
5. Submit: `Egy külföldi IP-ről sikeres belépést és új MFA-eszközt látunk.` The explicit login/MFA recovery rules prevent an unrelated response and give at least 35/100 (Medium); context should include suspicious-login or MFA procedures.
6. Submit: `Describe the main phases of handling a cybersecurity incident.` This is guidance, so risk may be marked **Not calculated** instead of a misleading zero.
7. Submit: `How do I bake a chocolate cake?` The deterministic test covers a direct scope response without retrieval. The real classifier can vary; its trace makes that decision inspectable.
8. Review `reports/functional/`, `reports/load/`, and `reports/ollama-smoke/`. Compare provider mode, code/dataset hashes, settings, individual answers, failures and timings. Do not compare dummy latency directly with real-model latency.

The final CPU smoke run took 16 min 18 s for the export with two answer revisions, and 4 min 52 s for general guidance without revisions. Prepare the demo in advance. The progress display updates after completed nodes; a single model call can remain active between those updates. These are observed timings, not guaranteed upper bounds.

To stop the demo while retaining data: `docker compose down`.

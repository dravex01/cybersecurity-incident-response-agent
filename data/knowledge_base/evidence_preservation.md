# Evidence Preservation (Prototype Demonstration Material)

Preserve evidence that can answer what happened, when, how, which assets and identities were affected, and what the actor did. Record acquisition time, source, collector, tool, integrity hash, and every transfer. Use read-only collection or forensic images where appropriate and restrict access to collected evidence.

Prioritize volatile and short-retention evidence: memory, running processes, network connections, cloud audit logs, identity events, EDR telemetry, email headers, and firewall or proxy logs. Use synchronized UTC timestamps. Do not alter originals unnecessarily. Legal or regulatory cases require guidance from qualified internal teams.

Hungarian retrieval aliases: bizonyítékmegőrzés, digitális bizonyíték, eseményidővonal, naplók mentése, chain of custody, sértetlenségi hash, forenzikus másolat.

Prioritize sources by volatility and retention: memory and live connections first when justified, then short-lived cloud and identity logs, then durable disk and configuration evidence. Record timezone and clock drift. Store originals immutably where possible, perform analysis on copies, and document collection failures or gaps as uncertainties.

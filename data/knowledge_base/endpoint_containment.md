# Endpoint Containment (Prototype Demonstration Material)

Prefer EDR network isolation when it preserves management visibility. If unavailable, disconnect wired and wireless networking without shutting the endpoint down. Coordinate containment of critical servers with service owners. Record who isolated the host, when, why, and which connections remained.

Before destructive cleanup, collect volatile data when trained staff and tooling are available: logged-on users, running processes, network connections, memory where justified, system time, and security-tool alerts. Avoid using the suspect host for credential changes. Reconnect only after scope, eradication, validation, and monitoring plans are complete.

Hungarian retrieval aliases: végpont izolálása, hálózatról leválasztás, fertőzött gép kikapcsolása, EDR izoláció, bizonyíték megőrzése, karantén.

Choose containment based on ongoing harm, evidence value, safety, and service criticality. EDR isolation is usually preferable because telemetry remains available. Power-off can destroy memory-resident evidence; use it when physical safety, destructive activity, or inability to isolate makes the trade-off necessary and authorized. Document every containment exception and residual connection.

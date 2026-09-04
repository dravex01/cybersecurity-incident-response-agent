# Suspicious PowerShell Triage (Prototype Demonstration Material)

This original defensive procedure applies to PowerShell flashing after a Word or Excel attachment, encoded commands, hidden windows, download cradles, script execution, or EDR PowerShell alerts. Hungarian retrieval aliases: felvillant a PowerShell, Word melléklet után PowerShell, kódolt parancs, gyanús parancsfuttatás, rosszindulatú szkript, dokumentum makró.

## Triage decision

Office spawning PowerShell, `-EncodedCommand`, hidden-window flags, execution-policy bypass, direct web downloads, in-memory loading, credential access, or an unknown parent process materially increase suspicion. Do not treat the absence of an antivirus detection as proof of safety. Determine whether execution occurred; a file merely present on disk is lower confidence than a recorded process and command line.

## Immediate actions

Use EDR network isolation or disconnect networking while preserving management visibility. Keep the endpoint powered on unless safety requires shutdown. Record hostname, user, alert identifier, UTC time, parent and child processes, command line, script-block logs, hashes, files created, network destinations, and security-tool actions. Do not terminate processes or delete artifacts before evidence capture unless ongoing harm requires an explicitly authorized containment decision.

## Scope and investigation

Review process trees, PowerShell operational and script-block logging, AMSI or EDR telemetry, Prefetch where applicable, scheduled tasks, services, autoruns, registry changes, browser and email artifacts, DNS, proxy, firewall, and identity logs. Search other endpoints for the same command fragments, hashes, URLs, domains, parent-child relationships, user, sender, attachment, or message ID. Look for persistence, credential access, privilege escalation, lateral movement, defense evasion, and data access.

## Recovery

Quarantine confirmed malicious mail and indicators, remove persistence after capture, rotate credentials used on the host when credential access is plausible, and rebuild from trusted media when integrity cannot be established. Validate controls and monitor matching behavior before reconnecting the endpoint.


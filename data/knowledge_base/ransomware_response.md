# Ransomware Response (Prototype Demonstration Material)

Treat encryption, ransom notes, mass file renames, backup deletion, and rapid multi-host spread as urgent. Isolate affected hosts and network segments, disable compromised accounts, and restrict remote administration paths. Do not destroy volatile evidence and do not connect clean backups to an active environment.

Activate incident leadership, legal and executive escalation, and applicable insurance or regulatory processes. Determine initial access, privileged activity, lateral movement, exfiltration, encryption scope, and backup integrity. Preserve ransom notes, samples, logs, process telemetry, and affected-system images. Eradicate persistence, rotate credentials in a controlled order, rebuild from trusted media, restore offline tested backups, and monitor closely before reconnecting systems.

Hungarian retrieval aliases: zsarolóvírus, titkosított fájlok, váltságdíjüzenet, ransom note, tömeges fájlátnevezés, mentések törlése, több gépre terjedés.

## Priority decisions

First determine whether encryption is active and spreading. Prefer coordinated network isolation of affected segments and identities; avoid actions that destroy volatile evidence unless required to stop immediate harm. Protect identity infrastructure, hypervisors, backup systems, and management tooling. Do not assume encryption is the only objective: investigate data theft before encryption.

## Restoration gate

Do not restore into an environment with uncontrolled access, active persistence, or compromised administrative credentials. Validate backup date, integrity, isolation, malware scan, and test restoration. Reconnect services in an approved sequence with enhanced monitoring and documented business-owner acceptance.

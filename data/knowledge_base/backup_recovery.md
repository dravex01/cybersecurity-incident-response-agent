# Backup and Recovery (Prototype Demonstration Material)

Confirm backups predate compromise, are isolated from affected identities, and pass integrity and malware checks. Test restoration in a segregated environment. Rebuild operating systems and applications from trusted media when integrity is uncertain; do not merely restore potentially persistent system images.

Rotate credentials and remove persistence before production reconnection. Restore critical services in an approved order, validate functionality and security logging, then monitor authentication, process execution, network traffic, and data integrity. Preserve failed or suspicious backup artifacts for investigation.

Hungarian retrieval aliases: biztonsági mentés, visszaállítás, ransomware utáni helyreállítás, ismert jó állapot, offline backup, visszafertőződés.

Define recovery gates before restoring: controlled entry point, rotated administrative credentials, clean management plane, validated backup, patched systems, working telemetry, and an approved reconnection sequence. Measure recovery against business validation and security monitoring, not merely whether a server boots.

# Credential Compromise (Prototype Demonstration Material)

For a suspected stolen password, token, API key, session cookie, or MFA takeover, validate the alert through trusted contact channels. Disable or restrict the identity if active abuse is plausible. Reset passwords, revoke sessions and refresh tokens, rotate exposed secrets, and review registered MFA methods, recovery channels, OAuth grants, application passwords, mailbox rules, and forwarding.

Review authentication and authorization logs for source IPs, devices, impossible travel, unusual applications, privilege changes, data access, and persistence. Scope other accounts that reused the secret. Privileged and service-account compromise requires urgent escalation and careful rotation to avoid outages.

Hungarian retrieval aliases: kompromittált jelszó, ellopott hitelesítő adat, feltört fiók, kiszivárgott token, munkamenet visszavonása, jelszócsere, jogosulatlan MFA-eszköz.

## Impact assessment

Determine whether exposure is suspected or confirmed and whether the credential was successfully used. Check privilege, accessible data, token lifetime, service dependencies, MFA state, and activity after authentication. A new unrecognized MFA method or recovery channel is persistence and must be preserved and removed. Successful use from an external source plus persistence is more significant than a password exposure with no observed use.

## Closure criteria

Confirm all session and token revocation, secret rotation, approved MFA and recovery methods, removal of forwarding or OAuth persistence, review of accessed resources, and monitoring for reuse. Service-account rotation must include dependent systems and old-secret invalidation.

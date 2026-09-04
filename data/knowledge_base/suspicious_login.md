# Suspicious Login Investigation (Prototype Demonstration Material)

Validate suspicious sign-ins using identity-provider logs, device identity, IP reputation, geography, user agent, authentication method, MFA result, session identifiers, and subsequent actions. Impossible travel and foreign IP alerts are signals, not proof; VPNs, mobile networks, and proxies can explain them.

Contact the user through a trusted channel. If compromise remains plausible, revoke sessions, require password reset, review MFA methods and OAuth grants, and temporarily restrict access. Investigate mailbox rules, downloads, application access, privilege changes, and other accounts using the same device or source. Preserve timestamps and raw audit events.

Hungarian retrieval aliases: külföldi IP, sikeres belépés, gyanús bejelentkezés, lehetetlen utazás, ismeretlen eszköz, váratlan MFA, új MFA-eszköz, feltört felhasználói fiók.

## Decision points and severity

A foreign IP alone is not proof of compromise. Confidence rises when the sign-in is successful and accompanied by an unknown device, new MFA method, unusual token, impossible travel, disabled security control, suspicious OAuth consent, mailbox rule, bulk download, or activity denied by the user. Treat successful foreign access plus an unrecognized MFA registration as at least medium risk. Privileged access, sensitive-data access, persistence, or activity across multiple resources warrants high or critical escalation according to organizational policy.

## Evidence checklist

Preserve the raw sign-in event, conditional-access result, MFA detail, device and compliance identifiers, session and token identifiers, source IP and ASN, geolocation, user agent, application, resource, correlation ID, and actions after login. Compare the event with the user's normal location, corporate VPN egress, travel, mobile carrier, and managed devices. Record what the user confirms separately from analyst inference.

## Containment and closure

For plausible compromise, revoke all sessions and refresh tokens, reset credentials from a trusted device, remove unrecognized authentication methods, review recovery options and OAuth grants, and restrict access until scoping is complete. Closure requires a documented legitimate explanation or completed containment, review of post-login actions, validation of approved MFA methods, and monitoring for recurrence.

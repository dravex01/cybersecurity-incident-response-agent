# Phishing Response (Prototype Demonstration Material)

For a suspicious email, preserve the original message and headers, attachments, URLs, sender details, and user actions. Do not forward a live attachment. Determine whether the recipient clicked, entered credentials, approved MFA, downloaded a file, or executed content.

If credentials may have been entered, reset the password from a trusted device, revoke active sessions and tokens, review MFA methods and mailbox rules, and search identity logs. If execution may have occurred, isolate the endpoint and follow the malware procedure. Search mailboxes for matching sender, subject, URL, attachment hash, or message identifier; quarantine confirmed copies. Block validated malicious infrastructure and notify affected users with safe guidance.

Hungarian retrieval aliases: adathalászat, adathalász e-mail, gyanús levél, rosszindulatú link, káros melléklet, hamis bejelentkezési oldal, megadta a jelszavát, Word melléklet.

## Triage branches

Separate delivery-only, link-click, credential-entry, MFA-approval, download, and code-execution cases. Delivery-only events emphasize mailbox search and quarantine. Credential entry requires identity containment. Any observed process execution, such as Office spawning PowerShell, also requires endpoint isolation and malware triage. Record which branch is confirmed rather than treating every delivered message as endpoint compromise.

## Evidence and closure

Preserve the original message in a safe format, full headers, message and campaign identifiers, URLs, redirect chain, attachment hash, sender infrastructure, delivery time, and the user's exact actions. Close after matching messages are handled, affected identities and endpoints are scoped, malicious indicators are blocked where justified, and monitoring finds no continuing access.

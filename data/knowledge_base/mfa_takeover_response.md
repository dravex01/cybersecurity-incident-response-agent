# MFA Device and Account Takeover Response (Prototype Demonstration Material)

This original defensive playbook covers an unexpected MFA device, authenticator registration, phone-number change, passkey, recovery method, or authentication-policy change. Hungarian retrieval aliases: új MFA-eszköz, új MFA eszköz, ismeretlen hitelesítő alkalmazás, új telefonszám, váratlan MFA-jóváhagyás, fiókátvétel, feltört fiók, külföldi IP, sikeres belépés.

An unrecognized MFA method added after a suspicious or foreign successful sign-in is a strong account-takeover indicator. Treat the combination as at least medium risk until the user and logs establish a legitimate explanation. Escalate further for privileged identities, sensitive-data access, mailbox manipulation, token creation, security-setting changes, or continued attacker activity.

## Immediate containment

Contact the user through a trusted channel, not through the potentially compromised account. Revoke active sessions, refresh tokens, remembered devices, application passwords, and suspicious OAuth grants. Remove only the unrecognized MFA method after preserving its registration time, device details, actor, IP address, and audit event. Require a password reset from a trusted device and re-register approved MFA methods. Temporarily restrict the account if active abuse is plausible.

## Investigation

Build a UTC timeline covering the initial sign-in, authentication result, MFA registration, token issuance, privilege or policy changes, mailbox rules, forwarding, OAuth consent, file downloads, cloud access, and subsequent sign-ins. Compare IP, ASN, country, device ID, user agent, session ID, and authentication method. Check whether the same source or device touched other accounts. A VPN or mobile carrier can explain geography, but it does not explain an unauthorized MFA registration.

## Recovery and closure

Restore approved authentication methods, verify recovery channels, remove attacker persistence, rotate exposed secrets, and monitor the identity and accessed resources. Close only after the user validates the legitimate devices, suspicious sessions are revoked, downstream activity is scoped, and no further unauthorized access appears during the agreed monitoring period.


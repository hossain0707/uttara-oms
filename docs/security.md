# Security, sensitive data and privacy review

**Risk classification: HIGH.** Names associated with organizational categories can reveal political affiliation. Treat these records as highly sensitive personal information.

## Core safeguards in this version

1. **Default deny:** All business routes require a verified Supabase JWT with expected issuer, audience, asymmetric signature, and authenticated role.
2. **Independent authorization:** An approved local user record and a scoped grant are mandatory even after Google sign-in.
3. **Least privilege:** role checks happen on the API, with Thana-wide aggregate-only viewer access, Ward-descendant or Unit-only personal-data scopes.
4. **Critical change review:** category transfers, unit transfers and activation-state changes are not written directly. A different qualified reviewer must approve.
5. **Admin authentication:** MFA level `aal2` is required for Thana Admin sessions by default.
6. **Sensitive field encryption:** phone and address use Fernet; exact phone uniqueness uses a separate keyed HMAC. Data provider should additionally encrypt disks and backups.
7. **Audit:** logs contain action, target, timestamp and actor, without plain phone/address and without automatic request logging of HTTP bodies.
8. **Data export:** profiles are exported only by Thana Admin; the action is audit logged. All file responses request no browser caching.
9. **Public source control:** no production member data, database backups, keys or tenant configurations are committed.

## Before real-world launch (blocking)

- Perform a Bangladesh-law and jurisdiction-specific privacy review, clear organizational privacy notice and meaningful, documented, revocable consent or other lawful basis.
- Determine who is data controller, who is processor, legitimate purposes, data minimization, retention windows and secure correction/erasure workflows.
- Conduct a written threat model, independent application penetration test and automated dependency/SAST scanning.
- Implement backup encryption, tested restore, monitoring and security incident response.
- Restrict export to an explicit business purpose and implement rate limits, anomaly detection, a data-access log and high-risk operation alerts.
- Provision two independent named administrators using controlled procedures, enable MFA and avoid shared accounts.
- Enforce HTTPS, HSTS, dedicated private DB connectivity, secret-manager integration and restricted CORS. Avoid log body capture.
- Implement application-level backup/restore, key rotation (including HMAC), phone recovery rules, and retention/deletion schedules.
- Validate Supabase project JWT key type: this API **deliberately rejects HS256**.
- Validate large-record pagination, concurrent approvals, transfer races and all role boundaries.
- Replace basic browser session integration with production-hardened SSR/cookie strategy if the threat model requires it.
- Configure organizational record access logging separately from application mutation logs.

## Prohibited use

This platform must not be used to infer people's political preferences, conduct persuasion microtargeting, share lists for campaigning without a lawful basis, or register individuals without a valid privacy basis.

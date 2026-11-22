# Security, sensitive data and privacy review

**Risk classification: HIGH.** Names associated with organizational categories can reveal political affiliation. Treat these records as highly sensitive personal information.

## Core safeguards in this version

1. **Default deny:** All protected business routes require a verified Supabase JWT with expected issuer, audience, asymmetric signature and authenticated role; health endpoints are public.
2. **Independent authorization:** An active local account is required after sign-in; basic users have owner-only workspace access. Organizational routes additionally require approved grants and scope.
3. **Least privilege:** role checks happen on the API, with Thana-wide aggregate-only viewer access, Ward-descendant or Unit-only personal-data scopes.
4. **Critical change review:** category transfers, unit transfers and activation-state changes are not written directly. A different qualified reviewer must approve.
5. **Admin authentication:** MFA level `aal2` is required for organizational grants by default. Reviewed non-owner exceptions are server-enforced; owner and security decision reviewers always require AAL2.
6. **Sensitive field encryption:** phone and address use Fernet; exact phone uniqueness uses a separate keyed HMAC. Data provider should additionally encrypt disks and backups.
7. **Audit:** logs contain action, target, timestamp and actor, without plain phone/address and without automatic request logging of HTTP bodies.
8. **Data export:** profiles are exported only by Thana Admin; the action is audit logged. All file responses request no browser caching.
9. **Public source control:** no production member data, database backups or private credentials may be committed. Public deployment identifiers/configuration are documented separately.

## Before real-world launch (blocking)

- Perform a Bangladesh-law and jurisdiction-specific privacy review, clear organizational privacy notice and meaningful, documented, revocable consent or other lawful basis.
- Determine who is data controller, who is processor, legitimate purposes, data minimization, retention windows and secure correction/erasure workflows.
- Conduct a written threat model, independent application penetration test and automated dependency/SAST scanning.
- Implement backup encryption, tested restore, monitoring and security incident response.
- Restrict export to an explicit business purpose and implement rate limits, anomaly detection, a data-access log and high-risk operation alerts.
- Provision two independent named administrators using controlled procedures, enable MFA and avoid shared accounts.
- Enforce HTTPS, HSTS, dedicated private DB connectivity, secret-manager integration and restricted CORS. Avoid log body capture.
- Implement tested managed backup/restore, key rotation (including HMAC), phone recovery rules, and retention/deletion schedules.
- Validate Supabase project JWT key type: this API **deliberately rejects HS256**.
- Validate large-record pagination, concurrent approvals, transfer races and all role boundaries.
- Replace basic browser session integration with production-hardened SSR/cookie strategy if the threat model requires it.
- Configure access-log retention and monitoring; directory/detail reads are now audited without search values or personal fields.

## Prohibited use

This platform must not be used to infer people's political preferences, conduct persuasion microtargeting, share lists for campaigning without a lawful basis, or register individuals without a valid privacy basis.


## Hardening changes and limits

JWT algorithms are checked before key lookup; the JWKS client caches key sets for five minutes with a five-second fetch timeout, while JWT signature, expiry, issuer, audience and authenticated role remain mandatory. OAuth uses PKCE. The browser has a TOTP enrollment/challenge gate; Supabase manages recovery, with application password-reset screens and an enrolled-factor AAL2 check before password changes. Refresh callbacks defer session calls to avoid auth-lock deadlocks. Session tokens still use Supabase browser storage, so XSS prevention and a tested CSP remain mandatory; no server-cookie migration is claimed.

Strict write schemas reject unknown fields, blank required text and null mandatory patches. Validation responses omit submitted inputs. API responses are no-store and carry nosniff/frame/referrer restrictions. Readiness does not expose database errors or connection strings; production OpenAPI endpoints are disabled. PostgreSQL history triggers and unique indexes are defense in depth, not protection against a privileged database owner. The application is single-Thana; it is not a multi-tenant isolation design.

Dependency scans were used to update Cryptography to 50.0.2 and WeasyPrint to 70.0 and override the vulnerable transitive PostCSS with 8.5.33. See upstream [Cryptography changelog](https://cryptography.io/en/latest/changelog/), [WeasyPrint changelog](https://doc.courtbouillon.org/weasyprint/stable/changelog.html) and [PostCSS advisory](https://github.com/advisories/GHSA-qx2v-qp2m-jg93). Zero known audit findings at a given time is not a penetration test or a future security guarantee.

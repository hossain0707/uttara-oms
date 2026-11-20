# Threat model

Assets: names linked to organizational categories, encrypted contacts, phone HMACs, role grants, exports, identity tokens, encryption keys and accounting history. Trust boundaries: browser ↔ Supabase; browser ↔ API; API ↔ PostgreSQL; ingress ↔ API; privileged operator ↔ deployment/secrets/backups.

| Threat | Implemented mitigation | Remaining validation/control |
| --- | --- | --- |
| Forged, expired or wrong-project JWT | Asymmetric verification, issuer/audience/role/expiry, algorithm allowlist, bounded JWKS fetch | Live signing rotation and outage behavior |
| Valid Google identity with no membership permission | Explicit active app account + backend scoped grants | Production provider configuration and identity verification |
| Stolen administrator session | aal2 enforcement, independent approvals, PKCE, TOTP gate | Secure devices, CSP, recovery/reset and token revocation drill |
| Horizontal access to another ward/unit | Backend scope checks on directory/detail/history/approvals/aggregates | Staging role matrix and penetration test |
| Self-approved sensitive changes | Distinct requester/reviewer, server role+scope+version rechecks | Named independent admins, no shared accounts |
| Concurrent edits or privilege removal | PostgreSQL locks + version checks, global-role and pending-change uniqueness | CI concurrency test and throughput test |
| Historical misattribution/double count | Immutable event-scoped deltas, reversible legacy backfill, SQL scope-before-grouping | Production-data reconciliation in isolated staging |
| XSS and export injection | React escaping, explicit spreadsheet text, escaped PDF content, nosniff | Tested restrictive CSP; browser-token storage remains a risk |
| Data disclosure through logs/caches | no-store responses, input-free validation errors, read/mutation audit without contact/search values | Ingress/APM redaction and alerting |
| Compromised runtime database role | Encrypted contacts, append-only PostgreSQL triggers | Separate owner/runtime roles, no DDL/TRUNCATE; disk/backup encryption |
| Malicious privileged DB owner | External operational audit required | Triggers cannot contain an owner/superuser |
| Bulk extraction/denial of service | Scoped authorization, bounded directory pagination and date interval | Ingress limits, export limits, load test, alerting |
| Lost encryption keys or destructive deploy | Versioned migrations, no automatic downgrade | Key escrow/rotation and tested restore |

Changes to controller purpose, sensitive fields, tenancy, identity provider, retention or export behavior require this model to be reviewed. Do not use this system for political persuasion targeting or inference.

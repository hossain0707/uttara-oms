# Operations, deployment and recovery

Current architecture is [Cloudflare Pages + Render Free + Supabase Free](DEPLOYMENT_STATUS.md). This is a limited pilot, not a provisioned high-availability environment. Keep the owner-approved free-only configuration; do not attach a payment method, upgrade plans or enable paid overages without authorization.

## Release procedure

Use the exact configuration and ordering in [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md). Production branch is `main`. Lock dependencies with `requirements.lock` and `package-lock.json`; run relevant checks plus CI. Keep migrations owner-controlled and separate from the restricted API runtime. No startup command auto-runs migrations. Avoid concurrent migration jobs.

Frontend build values are public and embedded; server secrets stay in the backend/provider configuration. API Docker images install native PDF libraries and run as nonroot. Compose is a loopback local-development baseline, not a public production installation. Production CORS must be exact HTTPS origins. Check ingress/proxy behavior for the actual host rather than trusting arbitrary forwarded IP headers.

## Routine checks

| Check | Interpretation / action |
| --- | --- |
| `/health/live` | Process can answer, not proof of dependencies |
| `/health/ready` | SQL round trip and exact `0005_personal_workspace`; 503 needs migration/connectivity investigation |
| Provider deployment source | Compare actual frontend/API SHAs with release record; main branch alone is not deployment evidence |
| Auth test with synthetic identity | Email/Google/session/TOTP behavior; readiness does not test it |
| Database usage / egress | Watch free-plan headroom, profile photos, report history and audit growth |
| SMTP / Auth logs | Check delivery errors and rate-limit events without recording codes or credentials |
| Audit / role changes | Review authorized grants, exports, security exceptions, account suspension and history integrity |

No on-call alert routes, SLO or monitored restore schedule are claimed as deployed. A responsible operator must establish these before relying on the pilot for critical availability. Configure ingress/body/export rate limits and anomaly detection after testing; there is no implemented application request limiter to claim as present. Record thresholds and contacts outside public source.

## Upgrade and rollback

1. Identify exact running API/frontend commits and database revision.
2. Preserve a current backup and matching keys in separately controlled stores. Do not commit dumps.
3. Restore/rehearse migrations in isolated staging, review legacy data reconciliation, run `alembic check` and privilege tests.
4. Stop or coordinate writes during incompatible changes. Deploy compatible components in the reviewed order.
5. If rollback is needed, choose an application version that understands the current schema and security-policy events. Do not downgrade migrations or remove owner/MFA audit state to make older code work.
6. Verify official totals, sample synthetic scoped flows and readiness before reopening.

The free deployment does not include paid PITR or a completed restore drill. A provider restore feature's existence does not prove a usable backup, retained encryption key or measured recovery time.

## Recovery drill to establish

Assign a recovery operator, approved RPO/RTO and backup retention. Export backups through authorized tooling, encrypt them and keep Fernet/HMAC keys separately accessible to the recovery operator. Restore into an isolated environment with outbound integrations disabled and a separate Auth project. Do not leak restored personal data into test output.

Verify schema/revision, decryption, phone digest matching, append-only history, official ledger conservation, security-policy state, scope isolation, independent approvals and PDF/XLSX output. Record backup timestamp, restore start/end and measured loss/window. Securely dispose of temporary restored data under the approved retention policy. This drill remains open; no recovery guarantee is supplied by these instructions.

## Incident handling

Restrict ingress and suspend affected accounts through authorized owner controls; revoke affected identity sessions in Supabase. Preserve evidence without copying private payloads into public tickets. Review audit and provider logs, determine affected scope and notify the designated incident owner through the organization's approved channel. Restore only verified backups.

Rotate compromised credentials through reviewed procedures. **Do not replace Fernet or HMAC keys in place**: that breaks decryption or exact phone matching. Key migration/rotation tooling and retention/erasure workflows are not yet implemented. The immutable audit table is both history and security configuration; clearing it can change owner/exception authority.

## Troubleshooting

| Symptom | Checks |
| --- | --- |
| Slow first screen | Render Free may be waking; distinguish cold start from ongoing latency |
| Readiness 503 | DB connection, schema search path and exact Alembic head; preserve private errors in operator-only logs |
| Signed-in 403 | Active account, grant, scope, AAL2/exception expiry; do not disable global MFA |
| Directory empty | Saved name/consent, filters, member link and approved scope; unassigned personal summaries are Thana-Admin-only |
| Approval disabled | Requester cannot self-approve; obtain a different qualified reviewer |
| Approval 500 on runtime role | Check restricted-role regression; never grant audit UPDATE merely to permit row locking |
| Browser Failed to fetch | Availability, CORS, correct compiled API URL and server error; this message alone is not proof of CORS root cause |
| Email rejected | Matching sender/username, App Password, template Token, provider limits; owner enters credentials privately |
| Blank/missing TOTP QR | Verified factors use a code challenge; only unfinished enrollment can be reset in that screen |
| PDF render failure | Native libraries/fonts in API image and container smoke check |
| 409 conflict | Reload and reconcile current version; avoid blind resubmission |

Use the [release checklist](RELEASE_CHECKLIST.md) to collect named signoffs without marking unverified work complete.

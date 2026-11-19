# Release checklist

Release is BLOCKED pending evidence below. This is a deployment handoff, not a production certification. Do not record a gate as passed without attaching actual evidence.

| Gate | Required evidence | Accountable owner | Current state |
| --- | --- | --- | --- |
| Requirements | Remaining text after truncated “Clearly”; agreed scope | Product owner (unassigned) | Missing |
| PostgreSQL checks | New branch backend/migration/concurrency CI results | Engineering owner (unassigned) | Pending runner |
| Browser acceptance | Google OAuth PKCE, approved/unapproved accounts, TOTP enrollment, MFA refresh, signout, mobile/tablet, keyboard and errors | QA owner (unassigned) | Pending staging |
| Migration rehearsal | Snapshot restore, complete legacy backfill, scoped ledger reconciliation, alembic check | DB owner (unassigned) | Pending staging |
| Deployment | HTTPS/ingress limits/CSP, private DB, least-privilege runtime, secrets, image build/smoke | Operations owner (unassigned) | Not provisioned |
| Privacy | Lawful basis/notice, retention/erasure workflow, export policy, accountable controller | Privacy owner (unassigned) | Not supplied |
| Key management | Rotation and recovery tooling for Fernet/HMAC without data loss | Security + DB owners (unassigned) | Not implemented |
| Recovery | Encrypted backups and measured restore RPO/RTO | Operations owner (unassigned) | Not exercised |
| Security | Threat model acceptance, independent penetration test, dependency review | Security owner (unassigned) | Local checks only |
| Monitoring | Alert routes, audit retention and incident contact | Operations owner (unassigned) | Not configured |
| Load | Large directory/export and root-lock throughput under expected load | Engineering owner (unassigned) | Not measured |
| Official reporting | Read-only snapshot isolation and scoped reconciliation under concurrent writes | Reporting owner (unassigned) | Implemented; PostgreSQL validation pending |

## Deployment record

- Source commit / image digests: pending
- Environment / ingress origins: pending
- Database revision: required `0004_invariants`
- Migration and rollback operator: unassigned
- Deployment time / maintenance window: pending
- Backup snapshot / restore evidence: pending
- Approved RPO / RTO: pending
- Go/no-go decision and signatories: pending

Never paste production records, credentials, QR secrets or tokens into this document.

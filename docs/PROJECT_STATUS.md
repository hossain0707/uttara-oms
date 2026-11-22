# Current project status

Reviewed 2026-11-22, application baseline PR #18 / `f33c8bc`, schema `0005_personal_workspace`. Production branch: `main`. Old chronological progress notes are retained in Git history; they are not current deployment instructions.

## Implemented and shipped

- Scoped official records, one-Thana hierarchy, independent member/access decisions and immutable ledger reporting.
- Basic self-only signup, Google/email-code acceptance, password account/recovery UI and administrative authenticator gate.
- Personal saved-card editing, private identification, processed photos, separate reading saves and monthly report review.
- Bilingual address/vocabulary helpers with manual entry; source-linked syllabus/library snapshot.
- Owner security panel with reviewed MFA exceptions and protected owner identity; runtime lock and confirmation UI fixes.
- Unified authorized directory with partial saved-name matching and linked-profile deduplication.

## Evidence and limits

PR #18 release checks passed. Local baseline: 67 backend tests passed, four PostgreSQL-only skipped; 43 web tests passed, TypeScript and static export passed. CI supplies PostgreSQL for database-specific cases. Recorded live frontend/backend deployment success and partial-name lookup are in [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md).

Read-only 50-request bursts are recorded in [CAPACITY.md](CAPACITY.md); they do not certify authenticated concurrency or a 1,000-account workload. The free service has no claimed uptime or measured recovery guarantee. End-to-end new-user/password-recovery, mobile, privacy/retention, key lifecycle, restore, monitoring and independent security acceptance remain separately tracked.

Use [HANDOVER.md](HANDOVER.md) for prioritized continuation, [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) for named signoffs and [CHANGELOG.md](../CHANGELOG.md) for release history. No private user/permission inventory belongs in this document.

## Direct owner control follow-up

Implemented owner-only direct role/scope changes, immediate MFA exceptions, direct request/member decisions, paginated account/queue/activity search and guarded OMS workspace erasure. Other administrators retain their existing approval rules. No schema change or new database privilege is required. Current UI distinguishes suspension from deleting workspace payloads; Auth identity and official/audit history remain. See MASTER_ADMIN.md for exact boundaries and tests. Deployment evidence for this follow-up is recorded in its release PR; the PR #18 record above remains historical baseline evidence.

# Implementation plan

Baseline reviewed: `9baf58a3f2117eabc4db26801b906ee6418989d0` (main), 2026-11-20 Asia/Seoul.
Only remote branch: main; all 11 commits inspected. Latest Quality checks run 44549149392 succeeded for this SHA. No AGENTS.md found.

## Scope
Continue the existing FastAPI / Next.js / SQLAlchemy / PostgreSQL architecture. The supplied command stops at “Clearly”; requirements beyond that text are unknown. Do not claim production certification or deploy real data.

## Gap analysis and priority

| Priority | Finding | Implementation / acceptance |
| --- | --- | --- |
| P0 | Routine edits check versions without locking, allowing lost updates | Lock member for routine edits and proposals; PostgreSQL concurrency regression |
| P0 | Null/whitespace required fields and ignored unknown fields reach persistence | Strict normalized input contracts; 422 regression tests |
| P0 | Hierarchy reactivation and member reactivation can bypass inactive ancestors | Central active-unit validation; lock hierarchy mutations; preserve inactive historical rows |
| P0 | Access approvals do not revalidate scopes; admin revocations can race | Serialize access decisions and enforce active admin minimum; revalidate grants at decision time |
| P1 | Reporting attributes old events to current unit; no as-of/date/comparison support | Immutable event delta ledger, deterministic legacy backfill, SQL historical aggregation, scoped transfer accounting, calendar periods |
| P1 | UI lacks org editing, directory pagination and report date controls | Extend current screens and typed client, preserve layout |
| P1 | JWT verification fetches JWKS per request; missing adversarial auth tests | Cached key client, local signing-key tests, default no-store/security response headers |
| P1 | No frontend container; build reproducibility limited | Lockfile, npm ci, standalone nonroot container, Compose health checks |
| P1 | Tests use SQLite despite PostgreSQL CI service | Run route suite on PostgreSQL in CI plus targeted locking tests; migration/backfill verification |
| P2 | Production operations unverified | Explicit release gates, restore/incident procedures, dependency scan workflow; staging signoffs remain external |

## Sequence
1. Record baseline and status (this document and PROJECT_STATUS.md).
2. Fix validation, write races, inactive hierarchy and access decision invariants.
3. Add versioned ledger migration and reporting service, API date contracts and regressions.
4. Extend existing frontend controls and packaging.
5. Run backend, migration, frontend and dependency checks; document actual evidence and blockers.

## Release gates
No production claim until staging Google OAuth/MFA, scope and concurrency testing on PostgreSQL, browser acceptance, backup restore, privacy/retention policies, independent security review and operational owners are verified. Use synthetic fixtures only.


## Implementation outcome

Steps 1–4 are implemented on `hardening/production-foundation`. Local validation in step 5 passes (see PROJECT_STATUS.md). PostgreSQL tests are wired into CI; local socket restrictions prevent running them here. Docker images, real OAuth/MFA and operational signoffs remain unverified. GitHub source access became available in the next session; publication/PR validation is being resumed. Supabase browser sign-in and an identified deployment target are still needed.

Additional work discovered during validation: patched vulnerable Python packages and transitive PostCSS; locked dependency installs; added PKCE/TOTP challenge UI; input-free validation errors; schema-aware readiness and read-only PostgreSQL reporting snapshots. Existing root/ward/unit identities and member IDs were preserved.

Production completion remains blocked by explicit release gates, not by a claim that passing local tests certifies deployment. No work on requirements omitted by the truncated command is asserted.

## Automatic basic account onboarding

User requested normal users to sign up/sign in automatically. Implement idempotent Google-backed account registration and a signed-in basic account home. No organizational grants or membership records are created. Existing inactive accounts stay disabled; organizational APIs keep role checks and administrator MFA. Verify duplicate/concurrent registration, user-metadata privilege injection, protected endpoint rejection, and the frontend first-login flow. No schema migration is needed.

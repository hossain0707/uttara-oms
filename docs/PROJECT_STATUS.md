# Project status

**Engineering hardening implemented locally; production release BLOCKED.** Reviewed and tested on 2026-11-20 Asia/Seoul. No live deployment, production credentials or real records were used.

## Repository baseline

- Upstream main: `9baf58a3f2117eabc4db26801b906ee6418989d0`; only remote branch at inspection.
- All 11 existing commits and tracked application/configuration/documentation modules inspected. No AGENTS.md found.
- Baseline CI: [Quality checks run 44549149392](https://github.com/hossain0707/uttara-oms/actions/runs/44549149392), success for this SHA. This is **not** validation of the new local branch.
- Work branch: `hardening/production-foundation`.

## Delivered changes

| Area | Result |
| --- | --- |
| Historical reporting | New immutable membership delta ledger, validated legacy backfill, date ranges, as-of totals, preceding-period comparison, monthly history, ward/unit totals and scoped transfer accounting |
| Data integrity | Lock-before-version-check routine edits; serialized structural/high-risk writes; inactive-ancestor/reactivation checks; database uniqueness barriers |
| Access | Independent approval retained; scope revalidation at grant decision; serialized admin revocations count distinct active administrators |
| Identity/security | Cached JWKS and algorithm gate; RSA adversarial tests; PKCE; administrator TOTP enrollment/challenge; deferred refresh callbacks; no-store and response headers; input-free validation errors |
| Directory/organization | Normalized strict schemas; audited directory/detail reads; frontend pagination/status filters; existing-node rename/activation controls; self-review buttons disabled |
| Exports | Date-filtered aggregate XLSX/PDF; personal sheet explicitly remains current records; formula/URL injection defenses retained |
| Infrastructure | Nonroot standalone web Dockerfile, healthchecked Compose, schema-aware API readiness, environment exclusions, Python/Node dependency locks |
| CI | PostgreSQL schemas for integration tests, migration drift check, two PostgreSQL-specific tests, frontend component tests and dependency-audit workflow |
| Handoff | Updated architecture/security/operations/QA; threat model, release checklist and implementation plan |

## Actual local validation

| Check | Result |
| --- | --- |
| Python 3.12 compile | Passed |
| Backend suite from locked dependencies | 35 passed, 2 skipped (PostgreSQL only) |
| Actual Alembic 0002→head backfill and schema drift | Passed on SQLite; included in backend suite |
| Incomplete legacy history migration | Correctly rejected; included in backend suite |
| Vitest/jsdom | 4 passed across 3 files |
| TypeScript (`npm run lint`) | Passed; this command is a typecheck, not an ESLint run |
| Next.js production build | Passed on Next 15.5.29 |
| `npm audit --omit=dev` | 0 known vulnerabilities |
| `pip-audit -r apps/api/requirements.lock` | No known vulnerabilities found |
| `pip check` | No broken requirements |
| Compose/workflow YAML and `git diff --check` | Passed |

One Starlette/httpx test-client deprecation warning remains; tests pass. Dependency scans reflect the audit databases available during this run and are not security certification.

## Environment limits and publishing

This workspace has no Docker executable and blocks local socket creation. A temporary PostgreSQL start failed at socket creation; therefore PostgreSQL row-locking/snapshot/trigger checks and Docker image smoke tests were **not run locally**. CI now defines these checks against disposable PostgreSQL 16, but no new CI result is claimed.

GitHub source access became available in the next session. Source publication and PR checks are being resumed through the connected account. The earlier local-only limitation no longer describes the connection. This does not establish a live deployment: Supabase currently requires sign-in in the connected browser, and no matching Uttara Google Cloud project was found by name. Existing unrelated cloud projects have not been modified. Track actual branch/PR results and deployment settings before release.

## Remaining release blockers

See [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) for owners and evidence. In particular: PostgreSQL concurrency and snapshot checks, container smoke tests, Google PKCE/MFA enrollment/recovery and mobile/browser acceptance in staging, TLS/CSP/ingress limits, least-privilege DB permissions, load/export limits, backup restore evidence, independent security review, approved privacy/retention/erasure policy and key-rotation tooling. Do not ingest real sensitive records until those gates are satisfied.

The supplied command ends at “Clearly”. Requirements after that point were not received and are not claimed complete. Stable organizational codes and IDs are retained; names/activation are editable. No redesign of working architecture was performed.

## Continue from this branch

1. Read IMPLEMENTATION_PLAN.md, architecture.md and RELEASE_CHECKLIST.md.
2. Push `hardening/production-foundation` from an authenticated checkout; open a PR targeting main.
3. Require the new Quality checks and Dependency security workflows. PostgreSQL tests must run without skips in CI.
4. Rehearse migration/backfill on an isolated restored staging database with writes stopped; do not bypass incomplete-history failures.
5. Complete staging/manual/recovery/privacy gates, record accountable signoffs, then decide deployment.

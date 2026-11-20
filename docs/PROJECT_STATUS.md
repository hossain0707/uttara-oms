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
| Backend suite from locked dependencies | 38 passed on PostgreSQL CI (including fresh SQL renderer); original local suite: 35 passed, 2 PostgreSQL-only skips |
| Actual Alembic 0002→head backfill and schema drift | Passed on SQLite and PostgreSQL CI; included in backend suite |
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

Source is published in [PR #1](https://github.com/hossain0707/uttara-oms/pull/1), code commit `245381e13a9394dc1d180ab4556636c8d2d930b8`. [Quality checks](https://github.com/hossain0707/uttara-oms/actions/runs/44556745119) passed, including all 37 backend tests against PostgreSQL 16, migration drift/backfill/immutable-history checks, concurrent edits, read-only report snapshots, frontend typecheck/tests/build. [Dependency security](https://github.com/hossain0707/uttara-oms/actions/runs/44556744735) also passed.

Browser setup created a dedicated Google Cloud project `uttara-oms` and Free Supabase organization “Uttara OMS”. The user completed Supabase database project creation. Its separate OMS schema is initialized and verified (10 RLS-protected tables, migration 0004, 12 wards, no person records); Google policy/client setup is completed, Google provider enabled, email provider disabled and TOTP confirmed enabled. The user selected free-only hosting. Restricted runtime-role grants were approved, applied and verified. The Render Free backend is live; Cloud Run was not deployed. Frontend deployment and final auth/CORS origins remain pending. No unrelated apps were modified. See DEPLOYMENT_STATUS.md.

## Remaining release blockers

See [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) for owners and evidence. In particular: Google PKCE/MFA enrollment/recovery and mobile/browser acceptance in staging, TLS/CSP/ingress limits, least-privilege DB permissions, load/export limits, backup restore evidence, independent security review, approved privacy/retention/erasure policy and key-rotation tooling. Do not ingest real sensitive records until those gates are satisfied.

The supplied command ends at “Clearly”. Requirements after that point were not received and are not claimed complete. Stable organizational codes and IDs are retained; names/activation are editable. No redesign of working architecture was performed.

## Continue from this branch

1. Read IMPLEMENTATION_PLAN.md, architecture.md and RELEASE_CHECKLIST.md.
2. Review published PR #1 targeting main; the implementation commit has green CI.
3. Keep the Quality checks and Dependency security workflows required. PostgreSQL tests ran without skips in the verified code CI run.
4. Rehearse migration/backfill on an isolated restored staging database with writes stopped; do not bypass incomplete-history failures.
5. Complete staging/manual/recovery/privacy gates, record accountable signoffs, then decide deployment.


Latest code/container CI: commit `d685604692c98fac3a59e2f78657d3c0c52f3b88`, Quality checks run 44563457929, Dependency security run 44563457739, Container smoke checks run 44563457858 all passed. Both Docker images, runtime HTTP endpoints, native PDF support and nonroot execution are verified in CI. The Render Free backend was deployed at https://uttara-oms-api.onrender.com on 2026-11-20 (Asia/Seoul). The user selected free-only hosting; no payment method was added.

Latest deployed code: `e9faeb670cbdc66208aa45c6c5bb89c8dfd48a5f`. Quality checks 44672870065, Dependency security 44672870036, and Container smoke checks 44672869967 all succeeded. Live `/health/ready` returned `{"status":"ready"}` and unauthenticated `/api/v1/members` returned `{"detail":"Not authenticated"}`. Frontend is not deployed; this is not a completed production release.

## Live deployment and initial access — 2026-11-20 (Asia/Seoul)

Cloudflare Pages frontend https://uttara-oms.pages.dev is deployed and its login page was verified live. The user saved the Cloudflare repository integration and final backend CORS origin. Render redeployment `dep-dbvt47ec6qcc73ah9ucg` reported Live with HTTP 200 readiness checks. Google OAuth initially failed with invalid_client/invalid client secret; the user created and saved a corrected secret. A fresh Google-authenticated session was verified afterward.

After explicit owner approval, the first verified Google identity was provisioned as an active global THANA_ADMIN in a controlled owner transaction, with an INITIAL_ADMIN_BOOTSTRAP audit event. No identity identifiers or credentials are included here. The live app now correctly blocks entry at Administrator MFA required. Authenticator enrollment is pending direct user action. A second independent administrator and the remaining release gates are still required; production acceptance is not complete.

## MFA enrollment recovery fix

A page refresh during unfinished TOTP enrollment previously hid the one-time QR while showing a verification field for the unverified factor. The frontend now distinguishes verified and unfinished factors and offers an explicit Reset unfinished setup action. Reset rechecks factor status, removes only the selected still-unverified TOTP factor, and never starts a new enrollment automatically. Verified factors remain protected. Six frontend tests and TypeScript checks passed, including unfinished-enrollment recovery and a factor verified in another tab. Deployment validation is pending.

## Normal-user automatic signup

Implemented POST /api/v1/account/register for a verified Supabase JWT whose server-managed app_metadata identifies Google. First registration creates one active basic AppUser and ACCOUNT_REGISTERED audit event, with no RoleGrant or Member. Repeat registration is idempotent; concurrent insert conflicts resolve to the existing account; disabled accounts cannot reactivate. GET /me permits self-account identity without an organizational role; all organizational endpoints retain current_actor role requirements and administrator MFA. The frontend automatically registers new Google identities and displays a basic account home instead of the approval gate. Local verification: 43 backend tests passed, four PostgreSQL-only skips; seven frontend tests and TypeScript passed. CI PostgreSQL and deployment evidence pending. Google audience remains Testing; the Google console currently requires completed branding before publishing. Do not claim unrestricted Google production availability yet.

Automatic signup release `5f6f7e91f9574ba6014162f1765ccea16ce02737`: Quality checks 44683537033 (PostgreSQL backend and frontend builds/tests), Dependency security 44683537340 and Container smoke checks 44683537012 all succeeded. Cloudflare production deployment 1d75c491 and Render deployment dep-dbvtvqajnfac738edlr0 are live. Existing administrator session was verified through the live dashboard after deployment; automatic fresh-account behavior is covered by integration tests but a separate normal Google identity was not exercised in this browser session. No organizational role was automatically granted.

Correction to earlier audience notes: Google documents an exception allowing basic identity-only scopes (openid/email/profile) without a test-user allowlist even in Testing status. This app requests Google authentication without additional scopes. Branding publication/verification remains incomplete; it is distinct from OMS registration. Reference: https://developers.google.com/identity/protocols/oauth2/production-readiness/overview . Homepage and owned frontend domain were saved in Google Branding.

## Personal workspace, email OTP and master approvals

User approved implementing a usable personal profile/report/target workspace, email OTP signup/sign-in, and master-admin-controlled leader permissions. THANA_ADMIN is the existing master-administrator role; no role is automatically elevated. All organizational roles will require authenticator AAL2; basic users will not. Leader applications are self-submitted and reviewed by a master administrator, independent of the requester. Sensitive organizational changes keep existing independent approval. Personal report reviewers are explicitly assigned by the master; report data is encrypted and private to its owner and assigned reviewer. Goals have explicit units; no unconfirmed 140/300/90 target units or automatic promotion rules will be invented.

Delivery gates: additive Alembic migration, runtime policies for the new tables, regression tests and CI; Supabase email provider and Token-based email templates; custom SMTP for real recipients. Supabase built-in mail is not production email delivery. Provider credentials and any credential enrollment must be entered by the user. Keep all services free-only.

Implemented (not yet production-deployed): email OTP form, automatic email/Google basic registration, owner-only profile/reading list and monthly daily-entry reports, XLSX/PDF personal export, submitted/returned/reviewed states, explicit reviewer assignment, unit-labelled monthly targets, self-submitted responsible-person applications and master approval. All organizational role holders require AAL2; ordinary accounts have no MFA requirement. Goals are snapshotted into saved reports. No membership, count or privilege is created by a self-reported category or target completion.

Live provider inspection on 2026-11-20: Email remains disabled; custom SMTP is off. Supabase's Templates screen explicitly requires custom SMTP to edit email bodies. Public OTP delivery cannot be completed without a configured sender. Existing Google sign-in remains the deployed route. Migration `infra/supabase/upgrade_0005.sql` adds two encrypted-data tables in the isolated `oms` schema and grants the server-only runtime SELECT/INSERT/UPDATE, with RLS and no public/anon/authenticated access. It must be applied before the new backend/frontend release. No new permission grant or live authentication setting was applied during implementation.

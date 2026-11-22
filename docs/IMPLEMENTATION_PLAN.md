# Implementation plan

**Historical foundation plan, not the current backlog or deployment state.** Use [HANDOVER.md](HANDOVER.md), [PROJECT_STATUS.md](PROJECT_STATUS.md) and [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md) for current instructions.

Current follow-up (2026-11-20): fix and verify end-to-end workspace operations after owner-reported profile/book save failure. Sender setup and returning-user email OTP acceptance are complete. Baseline sections below are historical, not current deployment claims. See DEPLOYMENT_STATUS.md for the live topology.

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

## Personal workspace, email OTP and master approvals

User approved implementing a usable personal profile/report/target workspace, email OTP signup/sign-in, and master-admin-controlled leader permissions. THANA_ADMIN is the existing master-administrator role; no role is automatically elevated. All organizational roles will require authenticator AAL2; basic users will not. Leader applications are self-submitted and reviewed by a master administrator, independent of the requester. Sensitive organizational changes keep existing independent approval. Personal report reviewers are explicitly assigned by the master; report data is encrypted and private to its owner and assigned reviewer. Goals have explicit units; no unconfirmed 140/300/90 target units or automatic promotion rules will be invented.

Delivery gates: additive Alembic migration, runtime policies for the new tables, regression tests and CI; Supabase email provider and Token-based email templates; custom SMTP for real recipients. Supabase built-in mail is not production email delivery. Provider credentials and any credential enrollment must be entered by the user. Keep all services free-only.


## End-to-end operations follow-up — 2026-11-20

P0: reproduce blank-book/profile save coupling and isolate tab saves; show actionable validation errors instead of JSON. P1: prevent uncommitted daily editor values from being omitted by report save or month changes; validate book progress and provide loading/retry/reload paths. Audit assignment user switching and save-state races. Run regression tests for profile/books, reports, assigned reviewer return/resubmit, scoped permissions and exports using synthetic data. Publish and deploy only after relevant checks; distinguish completed acceptance from missing setup such as uncreated units or reviewer assignments. Never populate real member data or consent as test fixtures.


## Bilingual guided catalogs — 2026-11-20

Add an accessible bilingual keyword suggestion control, locally bundled Bangladesh division/district/upazila/union lists with provenance/license, cascading current/permanent address helpers that preserve existing free text, and category filters for the legible owner-supplied syllabus book titles. Add occupation and descriptive responsibility suggestions to personal and official member entry/edit forms. Keep manual values, official category permissions and membership approval boundaries. No remote autocomplete or transmission of typed private addresses. Test bilingual matching, parent resets, keyboard choice, save compatibility and production builds. Ambiguous photo titles and editions are not invented.


## Form wording cleanup — 2026-11-21

Replace repeated language instructions with field-specific example placeholders throughout shared search/address controls and personal/member forms. Shorten address labels within their fieldset and remove duplicate translated headings. Keep bilingual matching and editable user values; examples must never prefill or save fake address data.

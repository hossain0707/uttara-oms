# Deployment status

Updated 2026-11-20 Asia/Seoul. Application is NOT live.

## Source and verification

- Published: [PR #1](https://github.com/hossain0707/uttara-oms/pull/1), `hardening/production-foundation`.
- Verified implementation commit: `245381e13a9394dc1d180ab4556636c8d2d930b8`.
- Quality checks run 44556745119 passed: PostgreSQL backend **37 passed**, frontend tests/typecheck/build passed.
- Dependency security run 44556744735 passed both Python and Node audits.

## Browser setup completed

- Created dedicated Google Cloud project `uttara-oms` (display name Uttara OMS).
- Enabled Cloud Run Admin API while preparing the deployment form.
- Draft backend service name `uttara-oms-api`, request billing, min 0/max 1 instances, require authentication. The service has NOT been created or deployed.
- Created Supabase organization Uttara OMS on the Free plan ($0/month).
- Supabase project `uttara-oms` is created and Healthy in Singapore (`ap-southeast-1`); the user completed database password creation.
- Initialized dedicated `oms` schema from the existing migrations in one transaction, using the fresh-database renderer. Verified revision `0004_invariants`, 10 tables, RLS on all tables, 12 wards, 0 people, and no schema USAGE for anon/authenticated roles. PUBLIC schema/table/function privileges were revoked. No administrator grant or login role was created.
- Supabase Google provider is not enabled: Client IDs/Client Secret are blank. Observed callback: `https://ahlgssvkdrbrsebkgafa.supabase.co/auth/v1/callback`.
- Prepared Google Auth Platform branding (Uttara OMS, External/testing) up to the unchecked Google API Services User Data Policy agreement. User review/acceptance and OAuth client credential creation are pending.
- Cloudflare account is accessible; no Uttara application, integration or domain change was created.

## Required next steps

1. User reviews/accepts the prepared Google User Data Policy step, creates a Web OAuth client for the observed Supabase callback, and enters Client ID/Secret directly into Supabase. Do not paste secrets in chat or commit them. Browser handoff is required for credential creation and action-time policy acceptance.
2. Confirm a cloud spending ceiling and billing account before launching paid/usage-billed resources. Min 0/max 1 instances reduces exposure but is not a monetary cap.
3. Inspect the created Supabase project, choose matching cloud region, configure Google OAuth and TOTP, and set exact redirect origins.
4. Use managed secrets and a dedicated least-privilege database runtime identity. The `oms` schema currently has RLS enabled with no runtime-role policies, so do not deploy until that identity, its required policies and table privileges are provisioned. Set the connection search_path to `oms` (for example, via psycopg options `-csearch_path=oms`). Any new security-sensitive grants or public ingress exposure require action-time confirmation in the browser.
5. Connect the authorized source, build containers, configure port 8000 for the API, run migrations in a controlled job, bootstrap organization and named administrators, then validate readiness and unauthorized rejection.
6. Build/configure the frontend using only public Supabase settings and the verified API origin. Choose Cloudflare static export or a compatible container deployment; current web Dockerfile is standalone Next.js.
7. Validate the complete login/MFA, role, approval, browser/mobile, backup/recovery and privacy release gates before production use.

Existing Trippy/AgentVerse resources were inspected only to distinguish targets; no changes to their services or configuration were made. No secret, real member record or database dump is included here.


## Fresh database renderer

Run `python scripts/render_fresh_sql.py --schema oms` from `apps/api` to generate initialization SQL without deployment credentials. It deliberately fails if the schema already exists. Do not rerun it against the provisioned project. Existing databases must use Alembic migrations instead. The ledger backfill is skipped only because a newly created schema has no legacy rows; this is not a populated-database migration shortcut. The script enables RLS and revokes PUBLIC privileges; backend runtime policies must be separately reviewed/provisioned.

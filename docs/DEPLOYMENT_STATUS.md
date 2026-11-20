# Deployment status

Updated 2026-11-20 Asia/Seoul. Application is NOT live.

## Source and verification

- Published: [PR #1](https://github.com/hossain0707/uttara-oms/pull/1), `hardening/production-foundation`.
- Verified application/container-check commit: `d685604692c98fac3a59e2f78657d3c0c52f3b88`.
- Quality checks run 44563457929 passed: PostgreSQL backend **38 passed**, frontend tests/typecheck/build passed.
- Dependency security run 44563457739 passed both Python and Node audits.
- Container smoke run 44563457858 passed both Docker builds, HTTP startup, native PDF generation, expected 503 for an unmigrated test database, and nonroot users. Initial smoke failure was a transient startup connection reset; bounded retries fixed the readiness check.

## Browser setup completed

- Created dedicated Google Cloud project `uttara-oms` (display name Uttara OMS).
- Enabled Cloud Run Admin API while preparing the deployment form.
- Draft backend service name `uttara-oms-api`, request billing, min 0/max 1 instances, require authentication. The service has NOT been created or deployed.
- Created Supabase organization Uttara OMS on the Free plan ($0/month).
- Supabase project `uttara-oms` is created and Healthy in Singapore (`ap-southeast-1`); the user completed database password creation.
- Initialized dedicated `oms` schema from the existing migrations in one transaction, using the fresh-database renderer. Verified revision `0004_invariants`, 10 tables, RLS on all tables, 12 wards, 0 people, and no schema USAGE for anon/authenticated roles. PUBLIC schema/table/function privileges were revoked. No administrator grant or login role was created.
- Supabase Google provider is enabled and saved; email/password sign-in is disabled. Credentials were entered directly by the user and were not extracted. TOTP MFA is Enabled, with the existing 15-minute AAL1-session limit retained. Observed callback: `https://ahlgssvkdrbrsebkgafa.supabase.co/auth/v1/callback`.
- Google Auth Platform branding and Web OAuth client were created by the user after their policy review. Current Supabase JWT signing uses ECC (P-256), compatible with the backend ES256 verification; the old HS256 key is marked Previous. Live end-to-end login and final frontend redirect origin remain unverified.
- Cloudflare account is accessible; no Uttara application, integration or domain change was created.

## Required next steps

1. The user selected Free only. Render Hobby/no card was verified; the new backend form selects Free ($0/month), Singapore, Docker context apps/api, health /health/ready and auto-deploy Off. The service is not deployed. Google OAuth configuration is saved; do not recreate its credentials.
2. Keep deployment on the free-only topology below. Do not add billing or launch usage-billed resources.
3. Supabase Singapore, Google OAuth and TOTP are configured. Set exact frontend redirect origins after its deployment URL is confirmed.
4. Use managed secrets and a dedicated least-privilege database runtime identity. The `oms` schema currently has RLS enabled with no runtime-role policies, so do not deploy until that identity, its required policies and table privileges are provisioned. Set the connection search_path to `oms` (for example, via psycopg options `-csearch_path=oms`). Any new security-sensitive grants or public ingress exposure require action-time confirmation in the browser.
5. Connect the authorized source, build containers, configure port 8000 for the API, run migrations in a controlled job, bootstrap organization and named administrators, then validate readiness and unauthorized rejection.
6. Build/configure the frontend using only public Supabase settings and the verified API origin. Choose Cloudflare static export or a compatible container deployment; current web Dockerfile is standalone Next.js.
7. Validate the complete login/MFA, role, approval, browser/mobile, backup/recovery and privacy release gates before production use.

Existing Trippy/AgentVerse resources were inspected only to distinguish targets; no changes to their services or configuration were made. No secret, real member record or database dump is included here.


## Fresh database renderer

Run `python scripts/render_fresh_sql.py --schema oms` from `apps/api` to generate initialization SQL without deployment credentials. It deliberately fails if the schema already exists. Do not rerun it against the provisioned project. Existing databases must use Alembic migrations instead. The ledger backfill is skipped only because a newly created schema has no legacy rows; this is not a populated-database migration shortcut. The script enables RLS and revokes PUBLIC privileges; backend runtime policies must be separately reviewed/provisioned.


## Free-only hosting decision

The user selected **Free only**. Do not deploy Cloud Run or Cloudflare Containers, add a payment method, enable paid plans, add paid disks/databases, or authorize automatic overages. The proposed zero-cost topology is Cloudflare Pages static export + Render Free Docker web service + the existing Supabase Free project. Check Render billing before creation: with no payment method, exceeding bandwidth suspends free services and exceeding pipeline minutes stops builds. Render's free backend sleeps after 15 idle minutes and can be restarted/suspended by the platform; this is a limited pilot and does not establish a production availability SLA.

`render.yaml` explicitly requests one Free Docker backend in Singapore and no Render database, disk or paid job. Existing migrations are already applied in Supabase; Free Render has no paid pre-deploy job, so future migrations must run as controlled operator tasks rather than automatic startup migrations. Set actual secrets directly in the provider; never use CI placeholders for deployment.

The frontend supports `npm run build:static` in `apps/web`; Cloudflare Pages output is `out`. The build requires the actual public backend URL, Supabase URL and publishable key and emits security/no-store headers with a CSP limited to the configured API/Auth origins. Standalone Docker builds remain the default. Do not publish using the `example-api.onrender.com` CI validation origin.

References: [Render Free limits](https://render.com/docs/free), [Render Docker hosting](https://render.com/hosting/docker), [Cloudflare Next.js static exports](https://developers.cloudflare.com/pages/framework-guides/nextjs/deploy-a-static-nextjs-site/).

## Runtime login handoff completed

The user created `oms_runtime` in the original Uttara OMS Supabase project. Verified LOGIN true, SUPERUSER/CREATEROLE/CREATEDB/REPLICATION/BYPASSRLS false. The restricted grants in `infra/supabase/runtime_permissions.sql` are prepared but NOT applied. They permit backend data operations only in `oms`, keep events/ledger/audit insert-only, allow deletion only of role grants for the existing revocation workflow, and make migration metadata read-only. Server-side RBAC remains the end-user authorization boundary; runtime policies do not provide per-user isolation. Apply only as owner after action-time approval. No credential is included. The user briefly accessed another Supabase account; no Trippy project was paused, modified, or reused, and no replacement OMS project was created.

# Current deployment status

Updated 2026-11-20 (Asia/Seoul). This supersedes historical setup notes in earlier revisions and chronological project-plan entries.

## Source and live services

- Repository: https://github.com/hossain0707/uttara-oms
- Deployment branch: **hardening/production-foundation**. Default `main` still contains the original foundation at `9baf58a3f2117eabc4db26801b906ee6418989d0`; do not deploy it accidentally.
- PR #1 is the open draft to main. PR #2 and #3 were merged into the deployment branch.
- Frontend: https://uttara-oms.pages.dev — Cloudflare Pages static export.
- Backend: https://uttara-oms-api.onrender.com — Render Free Docker service, Singapore.
- Database/Auth: Supabase Free, project `ahlgssvkdrbrsebkgafa`, Singapore. PostgreSQL database `postgres`, isolated application schema `oms`.
- No OMS Cloud Run service, Render PostgreSQL, paid disk or Cloudflare container was deployed. Unrelated applications are not reused.

## Last verified releases

| Component | Source | Deployment |
| --- | --- | --- |
| Backend | `ee3bcef3b8f864a39f34348ca4292a2e910a25ae` | `dep-dbvv11942hec7387ikug`, Live; `/health/ready` returned `ready` |
| Frontend | `2ca020fb4fbb2241be7229d59ec8352631bf9687` | `81b123e3-f073-49c0-91c2-dcd042497d71`, successful production build |
| Database | `0005_personal_workspace` | Additive upgrade applied once after owner approval; do not rerun fresh initialization or the 0004-only upgrade script |

The subsequent packaging/documentation follow-up does not change the database revision or API. Consult the GitHub branch head and provider deployment source before claiming a newer release is live.

CI at `9864a9e`: quality 44692642884, dependency security 44692643047, containers 44692643139 all passed. PostgreSQL backend: 59 tests; frontend: 11 tests. Container checks include nonroot users, HTTP startup and native PDF rendering. Passing checks does not certify a production service.

## Current authentication and authorization

- Google OAuth signup/sign-in works. Basic signup creates an active self-only account, no official membership and no role grant.
- Personal profile, reading progress, daily/monthly report drafts and owner exports are deployed. Submitted reports require an explicitly assigned reviewer.
- Main admins approve user role applications and assign reviewers/monthly targets. Administrator-initiated permission changes retain independent admin approval.
- Every organizational role requires authenticator AAL2. Basic users do not require an authenticator. Enrollment QR is distinct from a verified factor's normal code challenge.
- Supabase Email is enabled; Confirm email on, anonymous sign-in off, Google/TOTP preserved. Email OTP length 8, expiry 600 seconds.
- **Public email OTP delivery is unfinished.** A fresh SMTP inspection still shows custom SMTP disabled. A previous checked toggle was an unsaved setup form, not a working sender.
- Keep `NEXT_PUBLIC_EMAIL_OTP_ENABLED=false` until the sender, both code templates and real delivered-code tests are ready. Google remains available.

## Immediate email completion sequence

1. Owner creates/enters the chosen sender's credential privately and saves SMTP. For the discussed Gmail option: host `smtp.gmail.com`, port `465`, matching sender/username, sender name Uttara OMS, and a Google App Password. Google verification/credential creation must be completed by the owner, not inferred or bypassed.
2. Confirm SMTP is actually saved without revealing its password.
3. Set **Confirm sign up** and **Magic link or OTP** email bodies to `infra/supabase/email-otp.html`, including `{{ .Token }}`; do not leave a magic-link-only body.
4. Preserve email confirmation, Google and role MFA. Review rate limits within the chosen free sender allowance.
5. Enable `NEXT_PUBLIC_EMAIL_OTP_ENABLED=true` in the frontend build environment and rebuild. Pages, Docker and Compose consume it at build time; a runtime restart cannot replace the compiled value.
6. Owner privately enters received codes for new/returning-user tests. Verify incorrect/expired code rejection, role isolation and leader AAL1/AAL2 behavior before declaring email signup operational.

## Deployment configuration

### Backend

Render service `srv-dbvsonec6qcc73ag9t70`, Free Singapore; branch hardening/production-foundation; Docker context `./apps/api`, Dockerfile `./apps/api/Dockerfile`; port 8000; health `/health/ready`; auto-deploy off. The service root can return 404 normally.

Secrets in Render: DATABASE_URL, ENCRYPTION_KEY, PHONE_HASH_KEY. Preserve existing keys; replacing them in place breaks decryption/deduplication. Non-secret configuration:

```dotenv
ENVIRONMENT=production
PORT=8000
REQUIRE_ADMIN_MFA=true
JWT_AUDIENCE=authenticated
SUPABASE_ISSUER=https://ahlgssvkdrbrsebkgafa.supabase.co/auth/v1
SUPABASE_JWKS_URL=https://ahlgssvkdrbrsebkgafa.supabase.co/auth/v1/.well-known/jwks.json
CORS_ORIGINS=https://uttara-oms.pages.dev
```

Runtime DB role `oms_runtime` uses the shared session pooler (host verified during setup: `aws-1-ap-southeast-1.pooler.supabase.com`, port 5432, username `oms_runtime.ahlgssvkdrbrsebkgafa`, database postgres), TLS and `search_path=oms`. The password is not recorded in source. Recheck Supabase Connect before changing connectivity.

Use a separate migration owner. Runtime privileges exclude schema CREATE/DDL, TRUNCATE, member DELETE and history UPDATE/DELETE. All deployed tables have RLS; the server role's policies make FastAPI RBAC/ownership the end-user boundary. The new personal tables were checked live: runtime SELECT/INSERT/UPDATE true, DELETE false; anon/authenticated SELECT false.

### Frontend

Cloudflare Pages project uttara-oms; root `apps/web`; command `npm ci && npm run build:static`; output `out`; automatic production deployments enabled for hardening/production-foundation. Public build variables:

```dotenv
NEXT_PUBLIC_API_URL=https://uttara-oms-api.onrender.com
NEXT_PUBLIC_SUPABASE_URL=https://ahlgssvkdrbrsebkgafa.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=<project publishable key; never service-role/private key>
NEXT_PUBLIC_EMAIL_OTP_ENABLED=false
```

The static builder emits no-store/security headers and CSP restricted to configured API/Auth origins. Preview hosts are separate origins; do not replace CORS with a wildcard for testing. Supabase Site URL is the canonical frontend. Google callback is `https://ahlgssvkdrbrsebkgafa.supabase.co/auth/v1/callback`. OAuth client is configured in the dedicated Google project; do not recreate working secrets.

Google audience was last observed External/Testing. Basic identity-only scopes have a documented test-user allowlist exception; production branding review remains separate. Do not request broader Gmail API scopes just for app login.

## Deploying the next change

1. Branch from the current deployment branch, inspect concurrent changes, run the relevant checks and open a PR to that branch.
2. For schema changes, preserve backups/keys, rehearse in isolated staging and migrate once as owner before compatible API/frontend deployment. Readiness requires the exact current revision.
3. Merge reviewed green changes. Pages auto-builds; Render requires Manual Deploy -> Deploy latest commit or an exact verified source.
4. Verify the actual build SHA, status, readiness, authenticated routes and browser errors. Record evidence without credentials or personal records.
5. Do not downgrade/drop new tables to roll back user data. Old 0004-ready backend code will need a reviewed readiness compatibility plan after the 0005 migration.

## Production gates still open

Keep the owner’s **free-only** constraint. Do not add a card, paid plans/disks/PITR/overages or usage-billed services without a new explicit instruction. Render Free sleeps after inactivity; no availability SLA is claimed.

Email delivery acceptance, full normal-user/leader browser acceptance, backup/restore drill and RPO/RTO, privacy/retention review, monitoring/alerting, upstream abuse controls and independent security review remain open. No complete Bengali paper-book transcription, pixel-perfect mockup match or offline sync is claimed. Initial setup created 12 wards, no invented units/member records. Do not fill production with test people or fabricated consent to demonstrate a feature.

See operations.md, RELEASE_CHECKLIST.md, EMAIL_OTP_AND_PERSONAL_WORKSPACE.md and PROJECT_STATUS.md. Early versions of this file are preserved in Git history rather than presented as current setup instructions.

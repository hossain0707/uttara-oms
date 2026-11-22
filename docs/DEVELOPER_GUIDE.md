# Developer setup and continuation

Use the current `main` branch. Application baseline reviewed: `f33c8bc` / PR #18. No production secrets, user data or working owner account are supplied. Read [architecture](architecture.md), [authorization](ADMIN_GUIDE.md) and [handover](HANDOVER.md) before altering data contracts.

## Prerequisites

- Python 3.12 (the locked Linux/container target), Node 22, npm, Git.
- PostgreSQL 16; Docker Compose is the easiest local database option.
- A dedicated development Supabase project, asymmetric JWT signing (RS256 or ES256), email/Google providers as needed and TOTP enabled. Legacy HS256 is deliberately rejected.
- Native PDF libraries when running Python outside Docker. Debian/Ubuntu: `libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi8 fonts-noto-core fonts-beng-extra`. Use the API Dockerfile as the source of truth. A successful import alone does not prove PDF rendering works.

Commands below use Bash; on Windows use WSL or Docker, or adapt activation/environment syntax for PowerShell. Never use the live Supabase database for local development or tests.

## 1. Clone and configure

```bash
git clone https://github.com/hossain0707/uttara-oms.git
cd uttara-oms
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r apps/api/requirements.lock
```

Generate **development-only** keys in your private terminal, then put them in the API `.env` (never commit their output):

```bash
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
python -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Use the first as `ENCRYPTION_KEY`, the second as `PHONE_HASH_KEY`. Preserve keys for as long as you need to decrypt that environment. Do not regenerate production keys during deployment.

### Configuration reference

| Variable | Used by | Meaning |
| --- | --- | --- |
| `DATABASE_URL` | API / Alembic | SQLAlchemy PostgreSQL+psycopg URL; server-only; separate owner URL for migrations |
| `SUPABASE_ISSUER` | API | Exact `https://<project>.supabase.co/auth/v1` |
| `SUPABASE_JWKS_URL` | API | Exact issuer + `/.well-known/jwks.json` |
| `JWT_AUDIENCE` | API | `authenticated` |
| `ENCRYPTION_KEY` | API | Valid Fernet key; encrypted profile/report/contact data depends on it |
| `PHONE_HASH_KEY` | API | Separate random HMAC secret, minimum 32 characters |
| `CORS_ORIGINS` | API | Comma-separated exact browser origins; local `http://localhost:3000` |
| `REQUIRE_ADMIN_MFA` | API | Keep `true`; production rejects disabling it |
| `ENVIRONMENT` | API | `development` locally, `production` deployed; production disables OpenAPI routes |
| `NEXT_PUBLIC_API_URL` | Web build | Local `http://localhost:8000` or chosen API origin |
| `NEXT_PUBLIC_SUPABASE_URL` | Web build | Dedicated Auth project URL |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Web build | Public publishable key only; never service-role/private keys |
| `NEXT_PUBLIC_EMAIL_OTP_ENABLED` | Web build | `false` until SMTP, code templates and real delivered-code tests pass |
| `LOCAL_DB_PASSWORD` | Compose | Development database password, supplied in shell |
| `TEST_DATABASE_URL` | Tests only | Disposable PostgreSQL with create/drop-schema privileges |

Supabase Google client secrets and Gmail App Passwords belong in provider dashboards, not the web build or OMS profile/database settings. The API does not send SMTP directly.

## 2. Start and migrate the local database

Compose parses the web build variables even when selecting only the database. Set these values for your **development** project in the shell first:

```bash
export LOCAL_DB_PASSWORD='replace-with-local-only-password'
export NEXT_PUBLIC_SUPABASE_URL='https://YOUR-DEV-PROJECT.supabase.co'
export NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY='YOUR-DEV-PUBLISHABLE-KEY'
export NEXT_PUBLIC_API_URL='http://localhost:8000'
export NEXT_PUBLIC_EMAIL_OTP_ENABLED='false'
docker compose up -d db
```

For Python on the host, put `DATABASE_URL=postgresql+psycopg://oms:<URL-encoded-local-password>@localhost:5434/oms` in `apps/api/.env`. The sample uses `@db:5432` for containers; do not use that host from host Python. `environment=development` permits localhost CORS. The local default schema is `public`; deployed SQL scripts use `oms`. If reproducing production schema isolation, configure the dedicated schema/search path consistently for owner, runtime and Alembic.

```bash
cd apps/api
python -m alembic upgrade head
python -m alembic check
python -m app.bootstrap init-org
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Current head: `0005_personal_workspace`. Bootstrap is idempotent for root/ward placeholders and inserts no members. Use a privileged local owner for initial migrations, then a restricted runtime for realistic boundary testing. `infra/supabase/runtime_permissions.sql` is a one-time, schema-specific setup script with policy creation; it is **not** a general idempotent migration runner. Do not run it repeatedly against a configured project. `upgrade_0005.sql` is for its documented 0004-only hosted upgrade path, not fresh installs or already-upgraded databases.

## 3. Configure Auth and the frontend

In the development Supabase dashboard, configure the Site URL and exact allowed localhost redirects, including `/reset-password/`. Google Console's authorized callback is the development Supabase `/auth/v1/callback`, not the OMS API. Use a separate client/project from production.

For email-code support, configure custom SMTP privately and use `infra/supabase/email-otp.html` in both **Confirm sign up** and **Magic link or OTP**. Preserve the recovery template's confirmation URL for password-reset links. Verify delivery before enabling the build flag. Codes are not passwords or TOTP seeds.

In a second terminal:

```bash
cd apps/web
npm ci
npm run dev
```

Open `http://localhost:3000`. `.env.local` values must match the development Auth/API origins. API runs from `apps/api` so its `.env` is found. Swagger UI is at `http://localhost:8000/docs` only outside production. `/health/ready` should return `{"status":"ready"}` after migrations.

## 4. Provision initial administrators in a new development environment

Sign in using synthetic development identities first. An authorized operator verifies each exact Auth user `sub` and email in the development Auth dashboard, then runs this from `apps/api` with privileged development DB access:

```bash
python -m app.bootstrap admin --sub '<verified-auth-user-uuid>' --email 'first-admin@example.invalid'
```

Repeat for a second independently controlled development account so approvals can complete. Do not reuse the example email or change a production identity to make a test pass. Each administrator enrolls TOTP in the UI. Basic accounts remain self-only.

The CLI grants `THANA_ADMIN`; it does **not** configure a Master Admin owner. Owner binding/transfer is an out-of-band, authorized, audited operation described in [MASTER_ADMIN.md](MASTER_ADMIN.md). There is no general owner-install wizard or public owner-transfer API. A new developer should not create owner events in production just to unlock a screen.

## 5. Run checks

From the repository root with the venv active:

```bash
(cd apps/api && python -m pytest -q)
(cd apps/web && npm run lint && npm test && npm run build)
(cd apps/web && npm run build:static)
```

Static export requires all three public URL/key values configured. It writes `out/_headers` with CSP/security headers and uses the existing FastAPI for data. The ordinary Next build produces a standalone Node app for Docker; Cloudflare uses the static export. Generated `next-env.d.ts` changes are not intended source modifications; inspect and restore generated-only diffs before committing.

For full PostgreSQL checks, set `TEST_DATABASE_URL` to a **disposable local** PostgreSQL URL in the test shell, then run pytest from `apps/api`. Fixtures create/drop isolated schemas. Without this variable four PostgreSQL-only checks were skipped in the baseline local run. SQLite does not validate row locks, PostgreSQL grants, triggers or reporting isolation. CI supplies PostgreSQL 16.

The container workflow verifies nonroot images, HTTP startup and native PDF output. Its synthetic API intentionally has no migrated database, so readiness **503** there is expected. CI also audits Python dependencies and production Node dependencies.

## Source map

| Path | Responsibility |
| --- | --- |
| `apps/api/app/auth.py`, `policies.py` | JWT verification, account/role gates, scopes, root lock |
| `apps/api/app/routes/` | Members, directory, access, master security, personal workspace, reporting, organization |
| `apps/api/app/analytics.py` | Historical ledger and snapshot report calculations |
| `apps/api/app/models.py`, `schemas.py` | SQL models and official-record write contracts |
| `apps/api/app/security_policy.py` | Append-only owner/MFA security policy state |
| `apps/api/alembic/versions/` | Ordered migrations 0001–0005 |
| `apps/web/components/AuthScreen.tsx`, `EmailOtpSignIn.tsx`, `MfaChallenge.tsx` | Identity screens and TOTP gate |
| `apps/web/components/PersonalWorkspace.tsx`, `ProfileCard.tsx` | Personal forms, reports and saved cards |
| `apps/web/app/members/page.tsx`, `components/MasterSecurity.tsx` | Directory UI and owner/reviewer security controls |
| `apps/web/data/` | Geography, vocabulary, syllabus and library snapshots |
| `apps/web/lib/api.ts`, `supabase.ts` | Authenticated client calls and browser PKCE session |
| `.github/workflows/` | Quality, dependencies and container checks |

## Working rules

Use synthetic fixtures and a feature branch; preserve strict validation and version guards. A display-only change must not expand API visibility. Add a migration for a schema change and update readiness plus upgrade/recovery documentation coherently. Never weaken independent approvals to work around a missing second administrator. Keep history `SELECT/INSERT` only: locking immutable `audit_logs` with `FOR UPDATE` caused an actual restricted-runtime failure and must not be reintroduced.

The next maintainer's prioritized backlog and acceptance criteria are in [HANDOVER.md](HANDOVER.md). Application source remains rights-restricted; obtain permission before redistribution.

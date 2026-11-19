# Deployment and operations runbook

## Environments

Use separate **development**, **staging**, **production** projects and separate Supabase/Auth and PostgreSQL resources. Each should have distinct signing keys, encryption keys, HMAC secrets, and allowed origins. Restrict production operator access.

## Suggested deployment

- Web: private-access Next.js hosting (Vercel or Cloud Run) with HTTPS; do not allow search engine indexing.
- API: container-based hosting with restricted service-to-database networking, TLS, read-only file system where supported, minimal IAM.
- DB: managed PostgreSQL with private access, point-in-time backups, retention policy and audited administrative access.
- Identity: dedicated Supabase Auth project, Google provider, asymmetrically signed JWT and MFA for privileged accounts.
- Secrets: managed secret storage, not source control or runtime build logs.

## First deployment

1. Create private deployment environments and assign owners.
2. Configure OAuth callback origins and restrictive identity access.
3. Configure production secrets and DB connectivity.
4. Run `alembic upgrade head` once as a controlled migration job.
5. Run `python -m app.bootstrap init-org` once to initialize Thana + 12 Ward placeholders. Add valid Units through the authenticated admin UI.
6. Run separate audited admin provisioning with the exact Supabase `sub`; turn on MFA.
7. Verify `/health/live`, `/health/ready`, JWT rejection, scope isolation, and independent approval.
8. Verify encrypted backup and restore in staging before importing any real records.
9. Enable alerting on authentication failures, export use, migration failures and backup failures.

## API endpoints

- `GET /health/live`, `GET /health/ready`
- `GET /api/v1/me`
- `GET/POST /api/v1/organization/nodes`; `PATCH /api/v1/organization/nodes/{id}`
- `GET/POST /api/v1/members`; `GET/PATCH /api/v1/members/{id}`
- `GET /api/v1/approvals`; `POST /api/v1/approvals/members/{id}`
- `POST /api/v1/approvals/{id}/decision`
- `GET /api/v1/reports/dashboard`, `/export.xlsx`, `/export.pdf`

## Backup and rollback

Snapshots should be encrypted and tested for recovery. Application rollback must never automatically downgrade migrations containing user data. Freeze sensitive operations during schema changes, verify DB compatibility, and use a staged rollback plan. Never commit database dumps to GitHub.

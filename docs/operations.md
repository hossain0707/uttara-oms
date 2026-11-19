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


## Reproducible builds

Use `pip install -r requirements.lock` and `npm ci`. `requirements.txt` is the maintained direct-dependency constraint input; regenerate the lock in a clean Python 3.12 Linux environment, then audit and test it. Python lock currently targets Linux containers. Both app containers run as nonroot users; build contexts exclude environment files. Node public environment values are embedded at build time and must contain only the Supabase publishable key, never a service-role key. Next.js remains on 15 with a tested patched PostCSS override; re-evaluate this override on upgrades.

Compose now includes web, API and PostgreSQL. Export `LOCAL_DB_PASSWORD` and the three `NEXT_PUBLIC_*` values before any Compose command; keep API settings in `apps/api/.env`. For local host Python use `@localhost:5434`, and for containers use `@db:5432`. Bindings are loopback only. Compose is a local/staging baseline, not a complete public production deployment. Migrate with `docker compose run --rm api alembic upgrade head`, bootstrap with `docker compose run --rm api python -m app.bootstrap init-org`, then start `docker compose up -d`. Do not start multiple migration jobs. API readiness checks DB connectivity and exact Alembic revision; stale/missing schema returns 503. Uvicorn proxy headers trust loopback only by default; explicitly configure the actual trusted proxy network before placing containers behind a proxy.

## Deployment security boundary

Terminate TLS at the managed ingress. Enforce HTTPS redirects, HSTS and an application-specific CSP after staging validation. Configure per-client API rate limits, a stricter export limit, body-size limits and upstream timeouts at ingress; never key limits on an untrusted forwarded address. Restrict API/DB networking and deny public PostgreSQL access. Production settings reject non-HTTPS browser origins, wildcard CORS, missing MFA enforcement and non-PostgreSQL databases. This repository does not provision TLS certificates, cloud secrets, ingress, monitoring or managed database backups.

Use a separate migration owner and runtime role. The runtime role should receive schema USAGE, SELECT/INSERT on audit/events/deltas, SELECT/INSERT/UPDATE on organization/users/members/requests, SELECT/INSERT/DELETE on role_grants, SELECT on alembic_version, and no CREATE/ALTER/DROP/TRUNCATE, superuser or owner privileges. Verify permissions and immutable triggers in staging. The migration owner can disable triggers; audit its access separately. Offline admin bootstrap is privileged and should not be exposed as a network route.

## Recovery drill (required before launch)

1. Define approved RPO, RTO, retention, recovery operator and incident owner in the release checklist. Enable managed PITR and encrypted snapshots.
2. Keep database backups and encryption/HMAC keys in separately access-controlled stores. A DB backup without the matching keys cannot recover phone/address or stable phone matching.
3. Restore a snapshot into an isolated staging DB with outbound integrations disabled. Use a separate staging identity project; do not log or export restored personal information.
4. With writes stopped, migrate to the intended application revision. Verify `alembic current`, `alembic check`, encrypted-field round trip, ledger totals vs active members, scoped access and independent approval with authorized recovery operators.
5. Record restoration start/end, backup timestamp, recovered revision, integrity checks and measured RPO/RTO in the deployment record. Destroy temporary restored data under the approved retention policy.

## Incident response

On suspected unauthorized access, restrict ingress and disable affected AppUser accounts through an authorized DB operator, revoke identity sessions in Supabase, preserve audit/ingress evidence without copying PII into tickets, and notify the assigned incident owner. Establish scope from audit actions and identity logs. Rotate compromised credentials through a reviewed procedure; **do not replace Fernet/HMAC keys in place**, which would break decryption/deduplication. Contain first, restore only verified backups, validate approvals/RBAC before reopening, and record required notifications and corrective work. Retention, erasure and key-rotation tooling remain release blockers.

## Operational alerts to configure

Alert on readiness failures, DB pool exhaustion, migration failure, sustained 401/403/5xx bursts, personal exports, unexpected access grants, immutable-history violations and overdue/failed backups. Keep authorization headers, request bodies, search text and personal fields out of HTTP/APM logs. Directory audit entries record only actor, result window and count; search input is omitted. Set alert thresholds, retention and on-call destination with the deployment owner.

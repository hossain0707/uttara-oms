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
- Prepared Supabase project name `uttara-oms`, Asia-Pacific, Data API disabled (the application uses Supabase Auth plus direct PostgreSQL). Database password is blank and project creation has NOT been submitted.
- Cloudflare account is accessible; no Uttara application, integration or domain change was created.

## Required next steps

1. User creates/saves a strong database password and submits the prepared Supabase project form. Do not paste the password in chat or commit it. The browser requires user handoff for creating authentication credentials.
2. Confirm a cloud spending ceiling and billing account before launching paid/usage-billed resources. Min 0/max 1 instances reduces exposure but is not a monetary cap.
3. Inspect the created Supabase project, choose matching cloud region, configure Google OAuth and TOTP, and set exact redirect origins.
4. Use managed secrets and least-privilege database/runtime identities. Any new security-sensitive grants or public ingress exposure require action-time confirmation in the browser.
5. Connect the authorized source, build containers, configure port 8000 for the API, run migrations in a controlled job, bootstrap organization and named administrators, then validate readiness and unauthorized rejection.
6. Build/configure the frontend using only public Supabase settings and the verified API origin. Choose Cloudflare static export or a compatible container deployment; current web Dockerfile is standalone Next.js.
7. Validate the complete login/MFA, role, approval, browser/mobile, backup/recovery and privacy release gates before production use.

Existing Trippy/AgentVerse resources were inspected only to distinguish targets; no changes to their services or configuration were made. No secret, real member record or database dump is included here.

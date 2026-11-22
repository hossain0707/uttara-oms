# Email OTP, personal workspace and approvals

Current flow notes; reviewed 2026-11-22. See [deployment status](DEPLOYMENT_STATUS.md) for the shipped main release. The migration sequence below is historical upgrade guidance, not an instruction to rerun it on the current database.

## Implemented flow

1. Ordinary user requests an email code, enters it in the app, and receives an active basic account automatically. Google remains an optional first factor. No role or official member record is created.
2. A basic account opens My workspace: profile, current/permanent address, requested unit, self-reported category, joining/worker/candidate/oath dates, reading list, daily metrics and monthly reports.
3. Save profile consent first. Save reports as drafts. A user submits to an explicitly assigned reviewer. Only the owner and assigned reviewer can read report contents through the API; main-admin assignment metadata is separate.
4. Main admin opens Access control to approve user-submitted leader applications and assign report reviewers and monthly targets. Ward/unit roles are scoped. Self-requesting THANA_ADMIN is forbidden. Administrator-initiated role changes retain independent administrator approval.
5. Organizational roles, including report viewers, require authenticator AAL2 by default; an active reviewed non-owner exception can lift that gate. The owner and security decision reviewers still require AAL2. A normal basic account does not. Email/Google supplies the first factor; TOTP is the additional factor.
6. Reviewers open Personal report reviews, add a note and mark reviewed or return for correction. Reviewed/submitted reports cannot be edited until returned. Targets and reviews never promote a membership category automatically.

## Historical 0004 → 0005 upgrade sequence

- Verify migration 0004, preserve the encryption and phone-hash keys, and obtain permission for the runtime grants.
- Run `infra/supabase/upgrade_0005.sql` once as schema owner. It is transactional, checks the old revision and adds only the new private tables. Do not rerun fresh initialization on a live schema. Alembic users run `alembic upgrade head` and apply equivalent runtime grants.
- Verify migration 0005 and RLS, runtime SELECT/INSERT/UPDATE only on the two tables, no anonymous/authenticated/public privileges, and no runtime DDL/delete grants.
- Deploy the matching backend, then frontend. Until both are ready, retain the previous frontend and Google login. The new backend readiness requires migration 0005.
- Configure an SMTP sender within the user's free-only limit. The user enters provider credentials directly; never commit them or put them in chat/SQL history. Supabase default email service is restricted and is not a public signup sender.
- In Supabase Email templates, use `infra/supabase/email-otp.html` for **both Confirm sign up and Magic link or OTP**. Use a subject such as “Your Uttara OMS verification code”. `{{ .Token }}` is essential; a default magic link does not satisfy the code form.
- Enable Email, preserve Confirm email, signup enabled, anonymous disabled, existing Google and TOTP. Configure rate limits and short OTP expiry without disabling verification.
- The frontend gates the code form with `NEXT_PUBLIC_EMAIL_OTP_ENABLED` (default false). Keep it false while the sender/template setup is incomplete. Enable it in Cloudflare production build variables and rebuild only when code delivery can be tested. Google login remains available during setup.
- Verify a real newly delivered code and returning-user code in the browser. Users enter their own codes. Verify an invalid/expired code fails, normal user sees only their records, leader AAL1 is blocked and AAL2 works. Never include codes/QR secrets in screenshots.

## Units and scope

Report months use Asia/Dhaka dates. Prayers are counts, literature and Quran are pages, organization is minutes, hadith is items. Blank metrics are unreported; explicit zero is preserved. No targets are seeded until their units and period are agreed. The proposed 140/300/90 values are not silently interpreted. Report snapshots preserve the targets used when saved.

Personal reports are encrypted JSON, versioned and audited. They are not a replacement for the official Member/MemberEvent/MembershipDelta model. Linking a profile to a member is a main-admin metadata operation with a unique-member constraint, not automatic registration. Profile edits do not update official records. Organizational category/unit/status changes still use the independent approval module.

The scanned syllabus supplies provisional vocabulary, and BJILibrary supplies source-linked tracks; see LIBRARY_INTEGRATION.md. This release supports personal book progress; it does not claim exact transcription of every syllabus page, pixel-perfect mockups, configurable worship metrics or automatic spiritual/political eligibility scoring.

## Recovery

Do not drop the new tables to roll back application code after real reports exist. The old backend may run with an additive schema but its old readiness requires 0004, so use a reviewed rollback that adjusts readiness appropriately. Never change the encryption key during this release. Preserve encrypted backups and test restore separately before claiming production certification.

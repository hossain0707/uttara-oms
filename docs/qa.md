# Acceptance and security testing checklist

**Status: not yet production-certified.** Use test identities and artificial records only.

## Functional acceptance

- [ ] 12 configurable Wards appear under root; Units can be created, edited and disabled appropriately.
- [ ] Unit officer can add a consent-attested record in their own Unit.
- [ ] Missing consent is rejected by API.
- [ ] Name, member ID and exact normalized Bangladesh phone search work.
- [ ] Phone duplicates in +880/01 formats are blocked.
- [ ] All categories render separately; promotions do not increase total active count.
- [ ] Deactivation decreases active count; reactivation increases it.
- [ ] An authorized routine edit saves and increments record version.
- [ ] A critical change remains pending until a different authorized reviewer approves.
- [ ] Self-approval is rejected; cross-ward review cannot be completed by a ward-only administrator.
- [ ] Stale version approvals fail with conflict.
- [ ] Unit/ward boundaries are enforced for reads, writes, search, reports and exports.
- [ ] PDF and Excel files open successfully and contain accurate aggregate data.
- [ ] Only Thana Admin can initiate the personal-data export; export actions are audited.
- [ ] Desktop, tablet, and mobile layouts are usable.

## Security gate

- [ ] Unsigned, malformed, expired, wrong-audience, wrong-issuer and HS256 JWTs rejected.
- [ ] Unapproved Supabase user cannot access any organizational record.
- [ ] Admin cannot access without `aal2` when MFA policy enabled.
- [ ] No production data, passwords, JWTs or keys in GitHub, logs or analytics.
- [ ] Automated API integration tests and browser E2E tests pass.
- [ ] Penetration test, privacy review, data retention, deletion workflow and recovery drill completed.

## Release signoff

Do not ingest real sensitive member records until all security gates have named accountable signoffs and a documented incident-response process.


## Automated checks added during hardening

- API: historical category/status/transfer accounting, original-unit attribution, Dhaka midnight cutoff, date validation, personal/aggregate export boundaries, valid XLSX/PDF containers, stale updates/approvals, inactive hierarchy/reactivation, strict writes, input-free errors, readiness and response headers.
- Identity: locally generated RSA signatures; expired, wrong issuer/audience/role, missing expiry, invalid signatures, future-issued, malformed, unsigned and HS256 rejection; unapproved identity and admin MFA denial.
- Migration: actual 0002→head legacy backfill, accounting conservation, no duplicate people, refusal of missing creation history, model/migration drift check; PostgreSQL additionally tests immutable-history trigger.
- PostgreSQL concurrency: two simultaneous routine edits at the same version result in exactly one success and one 409. Requires TEST_DATABASE_URL; not simulated on SQLite. A second PostgreSQL-only test verifies read-only REPEATABLE READ reporting.
- Frontend: date filter/reset behavior, report failure state, administrator organization rename/deactivation and authenticator challenge error handling (Vitest/jsdom; mocked API/identity provider).
- CI: dedicated PostgreSQL schemas per route/migration fixture, exact Alembic head, model drift check, backend suite, frontend tests/typecheck/build and separate dependency audits.

jsdom component tests do not prove browser OAuth, mobile layout, accessibility or live MFA enrollment. Those acceptance gates require staging and real browsers with synthetic identities. A successful dependency audit does not replace penetration testing.

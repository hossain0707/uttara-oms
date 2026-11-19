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

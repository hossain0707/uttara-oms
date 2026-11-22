# Maintainer handover and continuation plan

Baseline: PR #18 / `f33c8bc`, schema `0005_personal_workspace`. This handbook update changes documentation and visual assets only. Current release configuration and evidence are in [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md). Source rights remain restricted; this handover is not a new license.

## First day checklist

1. Read README, architecture, developer setup, data visibility and admin approval rules.
2. Obtain authorized repository/provider access from the owner through a private handover. GitHub access alone does not grant database, Auth, Render, Cloudflare or Master Admin access.
3. Create isolated development Auth/SQL resources. Run migrations and synthetic tests; never restore live data into a casually shared development workspace.
4. Verify two independent development Thana Admins, TOTP and all relevant scope boundaries.
5. Inspect actual deployment SHAs, database head, free-plan usage and unresolved release gates. Do not assume older chronological notes describe current state.
6. Agree one bounded next change, acceptance criteria and release/rollback order. Branch from fresh `main`; keep unrelated application behavior unchanged.

## Private handover inventory

| Item | Where it belongs / requirement |
| --- | --- |
| GitHub maintainer access | Repository owner grants appropriate access; preserve PR/CI workflow |
| Cloudflare Pages control | Project/deployment settings; public build values; no server secrets |
| Render control | Service deployment/environment, runtime DB URL and encryption/HMAC secrets |
| Supabase control | Auth providers/templates/rates, database owner and restricted runtime, signing keys |
| Google OAuth / SMTP ownership | Dedicated provider project and sender owner; App Password entered privately |
| Recovery materials | Authorized encrypted database backups plus separately controlled matching Fernet/HMAC keys |
| Owner/admin identity verification | Private account inventory; do not hardcode new owners from display names/emails |

No secrets are intentionally supplied by this documentation. Do not request credential values through public issues or commit history.

## Priority backlog with acceptance criteria

| Priority | Work | Done when |
| --- | --- | --- |
| P0 before critical reliance | Backup/restore drill, incident ownership and monitoring | Measured restore/RPO/RTO, recovery key access, named operators and tested alerts |
| P0 governance | Privacy/retention/erasure decisions and independent security review | Written accountable signoffs; tested deletion/retention design compatible with immutable security authority |
| P1 capacity | Real authenticated 50-user staging test near 1,000-account dataset | Agreed workload/SLO, sanitized metrics, bottleneck analysis; no extrapolation from readiness alone |
| P1 auth acceptance | New email/password signup, OTP, password recovery, lost-factor procedure and browser matrix | Synthetic real-browser evidence for success/error/expiry/role isolation and recovery |
| P1 controls | Upstream abuse/body/export limits and security alerts | Thresholds, trusted-client identification and tests; no wildcard CORS or global MFA bypass |
| Shipped follow-up | Owner accounts, pending requests and activity now use paginated endpoints | Legacy ordinary-admin lists remain bounded; assess their pagination separately |
| P1 indexing/storage | Profile search and photo scaling | Measured authorized scan/storage cost; reviewed privacy-preserving index/object-storage design if needed |
| P1 key lifecycle | Fernet/HMAC rotation without data loss | Reversible/recoverable migration, key-version plan, backups and digest reconciliation |
| P2 workflow | Historical month-specific target assignment | Explicit versioned data model and migration; distinguish current goals from report snapshots |
| P2 data/editorial | Verify full syllabus transcription, editions and geography updates | Owner-reviewed source coverage, preserved attribution and regression tests |
| P2 product QA | Mobile/tablet/keyboard/accessibility acceptance | Real device evidence and resolved critical issues; responsive CSS alone is insufficient |
| P2 deploy hygiene | Refresh historical `render.yaml` in an intentional infra change | Matches approved main/free/manual configuration, reviewed without creating paid resources |

These are documented open items, not silently authorized infrastructure changes or claims that no safeguards exist. Use the release checklist for current signoffs.

## Regression traps

- Old README branch/SMTP instructions were stale; use current source/configuration.
- Empty unfinished reading rows once blocked profile saving. Preserve separate profile/reading merges and API enforcement.
- Selected tabs once had white text on a white button. Keep component presentation checks.
- Native browser confirmation stalled security decisions. Preserve the explicit in-page confirmation and cancel behavior.
- `FOR UPDATE` on append-only audit rows caused restricted-runtime failures. Preserve the root lock and narrow DB privileges.
- Personal-profile search was missing because official members and profiles are separate. Preserve unified projection, deduplication and scope checks; do not auto-create official members.
- A role title or self-reported category must never grant access. Master owner identity and MFA exceptions are server-side authority.
- Historical global transfers/category changes must not add people. Joined dates do not backdate ledger events.

See [CONTRIBUTING.md](../CONTRIBUTING.md), [API_REFERENCE.md](API_REFERENCE.md) and the baseline test suites before refactoring.

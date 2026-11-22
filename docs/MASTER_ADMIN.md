# Master Admin direct control panel

The configured owner is bound to a verified existing app-user UUID through durable `MASTER_OWNER_CONFIGURED` audit state. This is not an assignable dropdown role and cannot be created by editing a profile/email/browser flag. Owner routes require a global Thana Admin grant and actual authenticator AAL2. The owner cannot suspend/delete themselves, remove their protected global permission or exempt themselves from MFA.

## Direct authority

The owner opens **Master Admin** (also shown when the owner opens Access control). Owner actions apply after an explicit in-page confirmation, without a second administrator's approval. Other administrators retain their existing independent-review and scope rules.

| Control | Behavior |
| --- | --- |
| Registered OMS accounts | Search name/email, filter active/suspended/deleted state, page through all matching accounts; no 500-row UI window |
| Permissions | Grant, replace role/scope atomically, or remove a precise grant; stale permission fingerprints return 409 |
| Authenticator policy | Apply 1/7/30/90-day or until-revoked exception directly; restore requirement immediately; ordinary sign-in and existing scopes remain |
| Pending requests | Paginated permission, official membership and legacy security queues; owner can approve their own proposal while ordinary admins cannot |
| Official membership | Owner proposals from People & records apply category/transfer/status changes directly with ledger/audit transactions |
| Account status | Suspend/reactivate immediately; permission grants cannot silently reactivate an account |
| Assignments | Search reviewers and official members, set the current reviewer/member link/targets directly; private report payloads remain hidden |
| Activity | Paginated administrative audit metadata; immutable events remain authoritative |

Direct actions supersede conflicting pending access/security requests where applicable. Expiry/revocation is checked server-side on authenticated requests; no cron or redeployment is needed. Owner can act even when no second administrator is available, while other administrators' minimum-review protections remain.

## Workspace deletion is distinct from suspension

**Delete workspace data** first retrieves a preview and revision. The owner must type the exact target email, read the consequences and confirm. A changed profile/report/permission state invalidates the preview. No actual account is deleted during automated or live read-only acceptance.

The operation clears the target's encrypted personal profile, photo, NID/passport, reading list, current goals, report payloads and review-note content; removes their grants; anonymizes their OMS email (including target-email fields in access requests); blocks the OMS account permanently; and resolves pending target permission/security requests. Deleted workspaces cannot be reactivated or granted permissions by normal application controls.

It **retains** the minimal account/Auth-subject tombstone, immutable audit/security history, official membership records/history, other users' data and provider backups. It does **not** delete the separate Supabase Auth identity, Google/Gmail account or backup copies. The UI explicitly states this boundary. A provider identity purge or official-record erasure requires its own authorized operator process; no service-role Auth key is added to the app. Do not claim this is blanket legal erasure of all organizational/provider records.

## Persistence and compatibility

No schema migration or expanded DB grants are required; revision remains `0005_personal_workspace`. Mutable workspace rows are cleared using existing UPDATE permissions, grants use existing DELETE permission, and audit history remains SELECT/INSERT only. New `MASTER_ACCOUNT_DELETED` audit events are durable tombstones, not disposable logs. Existing owner configuration and MFA exceptions remain valid; no real grants or exceptions are changed simply by installing the feature.

Role mutations serialize on the organization root, lock the target account and check the current grant fingerprint. Membership changes reuse the existing ledger decision implementation. Workspace erasure locks the account against normal profile/report writes and checks its preview revision. Never add `FOR UPDATE` to immutable audit rows: that requires UPDATE privilege and broke restricted-runtime approvals previously.

## Initial activation and transfer

A new environment still needs controlled first-admin provisioning and an authorized out-of-band owner binding. Verify the exact existing app UUID/Auth subject/global grant and existing owner state; append the authorized owner event through a trusted operator process. There is no public owner-transfer endpoint. Application deployment does not create or replace the owner identity.

## Verification

Synthetic tests cover direct owner changes, forged owner flags, missing MFA, ordinary-admin self-approval denial, role replacement/stale state, active scope validation, owner protection, legacy decisions, expired/revoked exceptions, >1,000-account pagination, Bengali matching/minimal summaries, typed deletion confirmation, stale deletion previews, post-deletion access denial and retained official history. PostgreSQL CI exercises direct policy and workspace deletion under restricted runtime privileges. UI tests cover confirmation/cancel, owner controls, pagination/search and ordinary review.

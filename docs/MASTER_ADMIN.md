# Master Admin security panel

The owner is a separately provisioned account, not another assignable role in the ordinary Thana Admin dropdown. Provisioning binds the existing app_users UUID, preserving the account's verified Auth subject; it does not use an email from a client request or editable user metadata. The selected deployment owner is najmul.eee1996@gmail.com. No other account is automatically an owner.

## Interface

- Owner-only sidebar: Master Admin (/master/), using the approved OMS emblem.
- Owner sees registered accounts, actual role/scope names, account status, authenticator policy and security activity.
- Request a 1/7/30/90-day exception, or until revoked, with a short reason. No exception is automatically created by installation.
- A different authenticator-verified Thana Admin approves or rejects requests in Access control. Requesters and exception recipients cannot approve their own request. Exempt administrators must still verify an authenticator to participate in security decisions.
- Owner can revoke an exception immediately. Expiry/revocation is checked server-side on every authenticated API request; no cron, frontend-only flag or new deployment is needed.
- Owner can suspend/reactivate other accounts with a current-state guard. Suspension blocks subsequent API requests. Keep two active Thana Admins. A routine permission grant cannot reactivate a suspended account.
- Existing role/scope grants and removals retain their independent approval workflow. Owner role removal and owner suspension/exemption are blocked.
- Basic personal accounts retain the existing normal sign-in policy. Administrative accounts require MFA by default. Password recovery retains its existing authenticator checks for enrolled users.

## Persistence and authority

Security configuration is event-sourced in the existing durable, append-only audit_logs table. MASTER_OWNER_CONFIGURED identifies the owner; MASTER_MFA_REQUEST stores pending requests; MASTER_MFA_APPROVED/REJECTED resolve them; MASTER_MFA_POLICY records the effective per-account policy; MASTER_ACCOUNT_STATUS records account changes. Version guards use the prior policy event UUID. Policy events are never updated/deleted by the application. Review/mutation transactions serialize on the organization root and lock mutable account rows. Immutable request events are read without FOR UPDATE because audit history is intentionally SELECT/INSERT-only for the runtime. New audit details fit the existing 250-character limit. No schema migration is needed; revision 0005 remains current.

These audit records are authoritative security state and must be backed up and retained, not purged as disposable telemetry. Removing owner configuration makes MFA exceptions fail closed. Application routes never accept arbitrary audit actions or owner transfer requests. Owner provisioning/transfer is an out-of-band controlled operation, not a public API.

## Initial activation

Publish and deploy both API and frontend. Verify the existing owner account UUID, verified Auth subject, active global THANA_ADMIN grant and absence of another owner binding. After explicit authorization, append exactly one MASTER_OWNER_CONFIGURED audit event targeting that app user, recording the current owner as actor and the authorized owner setup as detail. Do not change any role grant, MFA factor, global MFA setting or existing request. Refresh /me and the workspace; only that account receives is_master_admin=true.

## Validation

Synthetic API tests cover owner-only requests, independent approvals, requester/target self-approval denial, duplicate/stale requests, live AAL1 exception checks, expiry, immediate revocation, owner MFA and role protection, suspension, minimum administrators and fail-closed missing configuration. Frontend tests cover owner-only controls and separate reviewer controls. No real account was exempted or suspended during testing.

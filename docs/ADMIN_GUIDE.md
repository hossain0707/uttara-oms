# Administrator and reviewer guide

Administrative rights are approved application grants, checked on every API request. The Master Admin is a separately configured owner identity with a global Thana Admin grant; choosing a title in a profile cannot create that identity.

## Role matrix

| Account / grant | Official records | Structure / access management | Review and exports |
| --- | --- | --- | --- |
| Basic account | Own workspace; no official directory | May apply for a role | Own reports and own report PDF/XLSX |
| `UNIT_EDITOR` | Read/routine write in assigned unit; propose sensitive changes | No hierarchy or role administration | Scoped aggregate reports; no sensitive-change approval |
| `WARD_ADMIN` | Read/routine write in its ward and descendant units | No global access administration | Independent member-change approval within ward; scoped aggregates |
| `THANA_VIEWER` | Aggregate reporting only from this grant; no personal directory | No role administration | Global aggregate reporting; no personal-data export |
| `THANA_ADMIN` | All official records; consented unlinked profile summaries | Structure, access requests, reviewer/member links and targets | Independent decisions; global aggregates and official personal-data XLSX export |
| Master Admin owner | Thana Admin rights plus protected owner controls | Direct grants/replacement/removal, MFA exceptions, suspension and guarded workspace deletion | Direct pending-request decisions; owner remains MFA-protected |

Multiple grants can coexist. An assigned report reviewer with an organizational role can read **submitted reports assigned to them**, independent of the official-record scope matrix. Merely being Thana/Master Admin does not open every private report or NID/passport number.

The configured Master Admin uses direct controls described in [MASTER_ADMIN.md](MASTER_ADMIN.md). References below to a second reviewer apply to ordinary administrators; the owner can act directly after confirmation.

## Configure the hierarchy

Use **Organization** to edit names or add real wards/units with stable codes. Initial bootstrap creates one Thana and 12 ward placeholders, no units or people. An official member needs an active unit under an active ward and root. Do not invent units or consent merely to fill the UI. Renaming does not create historical name versions; reports show current organization labels.

## Maintain official records

In **People & records**, choose **Add person**, enter a unique member number, name and valid normalized Bangladesh phone, select an active unit/category and attest the required consent. Routine name/contact/address/occupation/position changes save directly with a version guard. Category changes, transfers, deactivation and reactivation create requests in **Approvals**.

For ordinary administrators, a different qualified reviewer checks the request, scope and expected version before approving. A ward reviewer cannot approve a transfer out of their ward. If a conflict occurs, reload and review current facts rather than retrying stale values. Changing category does not add a second person to the total; transfers preserve global totals.

## Grant or remove permissions

1. Open **Access control** and select the registered account. Verify its identity and responsibility outside the form; do not rely on a similar display name.
2. Choose grant/remove, role and matching scope (Thana roles have no unit scope).
3. Submit the request. Administrator-created approvals require another Thana Admin. The requester may reject their own access request but cannot approve it.
4. The independent reviewer uses the pending list to approve/reject.
5. After approval, inspect **Accounts and approved permissions**. Assigned grants display **Remove**; removal creates its own independently reviewed request.

A basic user's own role application can be decided by a Thana Admin other than that user. Ordinary administrator workflows retain the two-active-admin safeguard; the protected owner can act directly without a second administrator. Ordinary removal cannot strip the protected owner role; grants cannot reactivate a suspended account. Historic owner-authorized bootstrap interventions were exceptional operations, not a recurring self-approval feature.

## Link a personal account and assign a reviewer

Under **Personal reviewers & monthly targets**, select the account, assign a different active user with an organizational role, optionally link an existing official member record, enter targets and save. Only one personal account can link to a given member. Linking deduplicates the directory; self-requested units are not a substitute for the official link.

Targets use fixed units: prayers=count, literature=pages, organization=minutes, Quran=pages, hadith=items. The assignment is the current goal set, not a scheduled history of month-specific assignments. Report saves snapshot the current goals; changing an assignment does not rewrite existing report snapshots. The UI's month/progress display does not implement a historical target scheduler.

## Review a personal report

Open **Personal report reviews**. Only assigned submitted reports appear. Read the permitted profile/report, enter a short relevant note and mark **Reviewed** or **Returned**. Only the assigned independent reviewer can decide. Returned reports become editable to the owner; reviewed reports remain locked. Document numbers are excluded even from this response.

## Use Master Admin security controls

See [Master Admin reference](MASTER_ADMIN.md). The owner selects an account and confirms direct role, scope, authenticator or status changes. Exceptions support 1/7/30/90 days or until revoked with a short reason. No second approval is needed for the owner. Ordinary administrators still need AAL2 and independent review for any legacy security queue decisions.

Guarded workspace deletion is separate from suspension and retains Auth identity/official/audit records; read the deletion preview. Exceptions remove only the administrative MFA gate while active; they do not remove ordinary sign-in or add a role. The owner can revoke an exception immediately. Owner suspension/exemption is blocked; suspension of other users takes effect on subsequent API authorization. A permanent owner transfer or first-owner binding is a controlled offline operator procedure, not a dropdown permission.

## Exports and accountability

Use **Reports** for date-filtered aggregate totals and XLSX/PDF. The date window is inclusive in Asia/Dhaka, up to 367 days, without future end dates. Official personal-data XLSX is Thana-Admin-only and always current state, even when aggregate dates are historical. Export only for an approved purpose and keep downloaded files access-controlled. Audit history is append-only; it must not be cleared to repair a UI problem.

# API reference

Base path: `/api/v1`. Public health endpoints are outside that prefix. In development, generate exact schemas from FastAPI `/openapi.json` or `/docs`; production intentionally disables both. Python route/input models are authoritative. Never publish an authenticated OpenAPI example containing real data or tokens.

## Authentication and errors

OMS data requests use `Authorization: Bearer <Supabase access JWT>`. The browser obtains credentials directly from Supabase Auth. The API accepts only authenticated RS256/ES256 tokens with the configured issuer/audience and required timestamps. Active account, approved grants, MFA policy, ownership and scope are rechecked server-side. CORS accepts configured origins and Authorization/Content-Type headers; it is not authorization.

| Status | Meaning |
| --- | --- |
| 200 / 201 | Successful operation / created entity where specified by the route |
| 401 | Invalid or expired identity token |
| 403 | Insufficient account/role/scope/MFA authority; missing Bearer responses depend on the authentication layer |
| 404 | Entity not found or intentionally concealed |
| 409 | Stale version, duplicate, resolved request or invariant conflict; reload/reconcile |
| 422 | Invalid input/prerequisite; validation errors omit submitted values |
| 503 | Readiness cannot confirm database connectivity/current schema |

API responses use `Cache-Control: no-store`. Never log Authorization, request bodies, search terms, document numbers or private response content.

## Endpoint map

| Method | Path | Purpose / required authority |
| --- | --- | --- |
| GET | `/health/live` | Public process liveness |
| GET | `/health/ready` | Public SQL + exact schema readiness |
| POST | `/account/register` | Verified Google/email JWT; idempotent self-only registration, no role |
| GET | `/me` | Current account, grants, actual MFA level and owner flag |
| GET | `/self/profile` | Own decrypted profile and current goals |
| PUT | `/self/profile` | Own profile or reading-only save, version/consent checks |
| GET | `/self/organization` | Active unit choices for own form, not a grant |
| GET / PUT | `/self/reports` | Own saved monthly reports / draft or submission |
| GET | `/self/reports/{report_id}/export/{extension}` | Owner-only `xlsx` or `pdf` report export |
| GET | `/directory` | Unified scoped official records + permitted personal summaries |
| GET / POST | `/members` | Scoped official member list / consent-attested creation |
| GET / PATCH | `/members/{member_id}` | Scoped official record / versioned routine fields |
| GET | `/members/{member_id}/history` | Scoped member activity |
| GET / POST | `/organization/nodes` | Approved hierarchy list / Thana Admin creation |
| PATCH | `/organization/nodes/{node_id}` | Thana Admin structure edits |
| GET | `/approvals` | Pending member-change queue by scope |
| POST | `/approvals/members/{member_id}` | Propose category/transfer/deactivate/reactivate |
| POST | `/approvals/{request_id}/decision` | Independent authorized member decision |
| GET | `/access/users` | Thana Admin registered-account/grant directory |
| GET / POST | `/access/requests` | Thana Admin permission queue / proposal |
| POST | `/access/requests/{request_id}/decision` | Independent approval; authorized rejection |
| GET | `/access/my-requests` | Own permission applications |
| POST | `/access/apply` | Basic/approved account requests responsible-person role |
| GET / PUT | `/access/personal/{user_id}` | Thana Admin assignment metadata / reviewer, member link and current goals |
| GET | `/reviews` | Submitted reports assigned to current independent reviewer |
| POST | `/reviews/{report_id}` | Assigned reviewer marks REVIEWED or RETURNED |
| GET | `/master/security` | AAL2 Thana Admin security view; owner gets additional management fields |
| POST | `/master/exceptions` | Owner applies another administrative account's MFA exception directly |
| POST | `/master/exceptions/{request_id}/decision` | Owner direct or ordinary AAL2 independent legacy-request decision |
| POST | `/master/exceptions/{user_id}/revoke` | Owner revokes effective exception immediately |
| POST | `/master/accounts/{user_id}/status` | Owner guarded suspend/reactivate; owner protected |
| GET | `/reports/dashboard` | Scope-authorized historical aggregate report |
| GET | `/reports/export.xlsx` | Aggregate workbook; `include_personal=true` restricted to Thana Admin |
| GET | `/reports/export.pdf` | Aggregate PDF |

All paths in the table except health are relative to `/api/v1`.

## Owner account controls

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/master/accounts` | Owner-only name/email search, state, limit and offset; minimal profile summary/grants/policy |
| POST | `/master/accounts/{user_id}/roles` | Direct GRANT/REVOKE/REPLACE with expected_roles_version; replace/remove uses exact grant_id |
| GET | `/master/requests` | Paginated owner queue: kind access/member/security |
| GET | `/master/activity` | Paginated administrative audit metadata |
| GET | `/master/accounts/{user_id}/deletion-preview` | Owner-only counts, retained boundaries and revision |
| POST | `/master/accounts/{user_id}/delete-workspace` | Exact confirmation_email + expected_revision; permanent OMS payload erasure, not Auth/official/history deletion |

The owner exception applies to existing access/member proposal and decision routes too; owner proposals can return APPROVED immediately. Other admins retain their prior independent-review rules. The owner always requires AAL2.

## Legacy bounded management lists

`/access/users` and the owner account list in `/master/security` each cap results at 500 accounts. Access requests and pending security request scanning cap at 200; own report listing caps at 120 and review queue at 200. These legacy endpoints do not expose general pagination parameters. The current owner panel instead uses the paginated /master/accounts, /master/requests and /master/activity endpoints. These are result windows, not signup limits.

## Important contracts

**Directory:** `q` up to 120 characters, optional official category/status filters, `limit` 1–100 (default 30), nonnegative `offset`. Response `{items,total}`; each item has `source: MEMBER|PROFILE` and `self_reported`. Unlinked summaries are read-only projections. Saved names retain original spelling; matching is partial, normalized and case-insensitive in English. The older `/members` query is official-record-only and is not the unified search contract.

**Profile save:** `{section: "profile"|"reading", expected_version, details}`. New profile version is 0 before the first save. Profile saves require name, NID/passport and consent; reading saves merge only books into the saved profile. GET owner profile returns full owner details; the rendered owner card masks document display. Do not use this endpoint to build a public directory.

**Report save:** `{month:"YYYY-MM-01", expected_version, entries, summary, submit, consent:true}`. Up to 31 unique daily entries. Keys: `day`, `prayers`, `literature`, `organization`, `quran`, `hadith`, `notes`. Units and bounds live in `routes/personal.py`. Submitted reports require an active assigned independent reviewer. A returned report can be corrected; submitted/reviewed rows cannot be edited directly.

**Assignments:** `{expected_version, reviewer_id, member_id, goals:[{metric,target}]}`. Only current goals are persisted here; saving a report captures its goal snapshot. Assignments do not expose private report content.

**Official member routine patch:** `expected_version` plus allowed name/contact/address/occupation/position fields. Category/unit/status mutations use the approval route rather than this patch. Strict schemas reject unknown fields. Separate official and personal sources do not share a write endpoint.

**Reporting dates:** optional `start_date`, `end_date` (inclusive Asia/Dhaka). Up to 367 days; no future end or reversed interval. Official personal XLSX is current-state information, not a historical person listing.

**Security decisions:** `{approve:true|false}` plus exact path request UUID. Owner policy changes apply directly; ordinary administrators retain independent legacy-request checks. Effective policy uses append-only audit events and guarded prior event IDs; read the owner/security models for request, revoke and account-status bodies. No public endpoint can write arbitrary audit events or transfer ownership.

## Safe read-only smoke check

```bash
curl --fail --max-time 70 https://uttara-oms-api.onrender.com/health/ready
```

This checks readiness only. It does not test identity, permissions, business writes, email or 50 authenticated users. Test authenticated requests in a separate environment with synthetic identities; do not copy live tokens into scripts or documentation.

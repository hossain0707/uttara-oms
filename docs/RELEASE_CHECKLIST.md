# Release and production-readiness checklist

Reviewed 2026-11-22. The pilot is deployed; this checklist distinguishes shipped evidence from readiness work that remains open. Do not mark a gate complete without current evidence and an accountable reviewer. No production certification is claimed.

| Gate | Evidence / status | Next responsibility |
| --- | --- | --- |
| Source/release | PR #18 / `f33c8bc`, main; [deployment record](DEPLOYMENT_STATUS.md) | Release operator verifies every new frontend/API SHA |
| Automated checks | Quality, dependency and container workflows passed for baseline | Engineering reviews current PR results |
| PostgreSQL boundaries | CI covers migrations, immutable history, concurrent writes, runtime privileges and report snapshot semantics | Re-run for data/authorization changes |
| Authentication | Google/email OTP owner-confirmed; password/recovery implementation tests present | QA verifies new/returning/recovery/expired-code and real-browser matrix |
| Application acceptance | Live scoped partial-name result verified; automated profile/report/access regressions | QA completes synthetic user/admin/reviewer journeys and mobile/keyboard tests |
| Schema upgrade | Deployed `0005_personal_workspace`; no PR #18 migration | DB operator rehearses future upgrades and reconciliation |
| Deployment safeguards | Restricted runtime, explicit CORS, no-store/security headers and static CSP implemented | Operations validates ingress/proxy/body/export/abuse controls |
| Privacy/retention | Sensitive-data boundaries documented; formal signoffs not recorded | Privacy owner approves notice, consent, retention and correction/erasure process |
| Key lifecycle | Existing encryption/HMAC keys preserved; rotation tooling absent | Security/DB operator designs and tests lossless rotation |
| Recovery | No completed restore/RPO/RTO evidence supplied | Operations performs encrypted backup/key recovery drill |
| Independent security | Threat model and automated audits exist; penetration review not recorded | Security reviewer provides findings and closure evidence |
| Monitoring | No configured on-call/alerting evidence supplied | Operations defines alerts, contacts, retention and incident drill |
| Capacity | Read-only burst evidence only; 50 authenticated / 1,000 accounts untested | Engineering defines SLO/workload and runs staging test |
| Editorial data | Geography and library are reviewed snapshots with coverage limits | Product/editor verifies syllabus editions and administrative updates |

## New release record template

Copy into a private or sanitized release record, without secrets or personal data:

- Source commit / PR / CI links:
- Intended and actual frontend/API source SHAs and provider status:
- Database revision (current baseline `0005_personal_workspace`):
- Migration necessity, owner, backup and rehearsal evidence:
- Compatibility and rollback plan:
- Synthetic acceptance cases and results:
- Known failures / open risks / limitations:
- Operational and product go/no-go reviewers:
- Deployment time (include timezone):

Passing tests is not a substitute for backup, privacy, threat-model or capacity acceptance. Preserve the free-only resource constraint unless the owner explicitly authorizes a change.

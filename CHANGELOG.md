# Release history

This is a source-based summary, not a claim that every historical deployment had full acceptance. Exact application release/deployment evidence is in [DEPLOYMENT_STATUS.md](docs/DEPLOYMENT_STATUS.md). PR links refer to this repository; no private account inventory is included.

## Documentation handover — 2026-11-22

- Replaced stale README/deployment instructions with current main/free-hosted topology.
- Added user/admin/developer/API/data/capacity/continuation guides and animated architecture assets.
- Preserved failed and successful burst-test attempts and production-readiness limitations.
- Documentation/visual assets only; no role, security setting, application behavior or database migration change.

## Direct owner controls — 2026-11-22

Owner-only direct roles/scopes, MFA policy, pending decisions, suspension and guarded workspace deletion; paginated account/name/email search, queues and administrative activity. Ordinary admins retain independent review. No migration or global MFA relaxation. Auth identity, official membership and audit records remain outside workspace deletion.

## Application releases

| PR | Result |
| --- | --- |
| [#18](https://github.com/hossain0707/uttara-oms/pull/18) | Unified saved-profile and official-record directory; partial Bengali/English names, deduplication and approved scopes. Baseline `f33c8bc`. |
| [#17](https://github.com/hossain0707/uttara-oms/pull/17) | Explicit in-page security confirmation instead of unreliable native dialog |
| [#16](https://github.com/hossain0707/uttara-oms/pull/16) | Security approvals work under immutable-history runtime DB privileges |
| [#15](https://github.com/hossain0707/uttara-oms/pull/15) | Protected owner panel, reviewed MFA exceptions, expiry/revocation and account suspension |
| [#14](https://github.com/hossain0707/uttara-oms/pull/14) | Saved profile cards, photo processing/sharing and private NID/passport fields |
| [#13](https://github.com/hossain0707/uttara-oms/pull/13) | Owner-approved green/gold emblem across application branding |
| [#12](https://github.com/hossain0707/uttara-oms/pull/12) | Permission decision feedback, requester rejection, approved grants with removal workflow |
| [#11](https://github.com/hossain0707/uttara-oms/pull/11) | Reference-style password login/signup and recovery screens |
| [#10](https://github.com/hossain0707/uttara-oms/pull/10) | Source-linked library/syllabus tracks, cover links and reading-list staging |
| [#9](https://github.com/hossain0707/uttara-oms/pull/9) | Cleaner field labels and meaningful example placeholders |
| [#8](https://github.com/hossain0707/uttara-oms/pull/8) | Guided bilingual geography and book/occupation/responsibility vocabulary |
| [#1](https://github.com/hossain0707/uttara-oms/pull/1) and early follow-ups | Production foundation, scoped records/history/reporting, personal workspace, email OTP gating/acceptance, operation fixes and main deployment consolidation |

Read original PR diffs for implementation details. Historic one-time operator interventions do not define a public permission bypass; the current reviewed workflow remains authoritative.

# Uttara OMS documentation

Reviewed 2026-11-22 against application baseline `f33c8bc` (PR #18). Production branch: `main`. This handbook documents the implemented free-hosted pilot, not an unqualified production certification.

## Choose your task

| Task | Guide |
| --- | --- |
| Sign up, edit a profile, submit a report | [User guide](USER_GUIDE.md) |
| Create units, approve permissions, assign reviewers | [Admin guide](ADMIN_GUIDE.md) |
| Manage authenticator exceptions and suspension | [Master Admin](MASTER_ADMIN.md) |
| Install and continue development | [Developer guide](DEVELOPER_GUIDE.md) |
| Understand components and workflows | [Architecture](architecture.md), [data model](DATA_MODEL.md), [animated explorer](visuals/architecture-explorer.html) |
| Integrate with the API | [Endpoint reference](API_REFERENCE.md) |
| Deploy, verify or recover | [Deployment status](DEPLOYMENT_STATUS.md), [operations](operations.md) |
| Assess capacity | [Free-tier limits and test evidence](CAPACITY.md) |
| Take over maintenance | [Handover](HANDOVER.md), [release history](../CHANGELOG.md), [contribution rules](../CONTRIBUTING.md) |
| Review safety and release evidence | [Security](security.md), [QA](qa.md), [release checklist](RELEASE_CHECKLIST.md), [threat model](THREAT_MODEL.md) |

## Focused implementation notes

- [Account screens and password recovery](PASSWORD_AUTH.md)
- [Email OTP and personal workspace](EMAIL_OTP_AND_PERSONAL_WORKSPACE.md)
- [Saved profile presentation and identification](PROFILE_PRESENTATION.md)
- [Bilingual address and vocabulary catalogs](BILINGUAL_CATALOGS.md)
- [Source-linked library](LIBRARY_INTEGRATION.md)
- [Unified directory](DIRECTORY_SEARCH.md)
- [Permission decisions and removal](ACCESS_ACTIONS.md)

Current-status and operations documents supersede old chronology. The [original implementation plan](IMPLEMENTATION_PLAN.md) is historical context; it is not the current backlog. Provider quotas and dashboard values can change. Recheck them before a new release.

# Contributing and maintaining Uttara OMS

Start with [developer setup](docs/DEVELOPER_GUIDE.md) and [handover](docs/HANDOVER.md). Application rights are reserved; coordinate contributions and redistribution with the rights holder. No open-source license is added here.

## Change workflow

1. Branch from current `main` and read affected route/model/UI contracts.
2. Reproduce the issue with synthetic fixtures or a dedicated development identity.
3. Keep the change bounded; preserve existing records, scope boundaries, consent and independent approval.
4. Run relevant tests, TypeScript/build checks and PostgreSQL integration checks for authorization/data changes. Open a PR explaining the trigger, resulting behavior, validation and limitations.
5. Wait for quality, dependency-security and container checks. Merge the expected reviewed head, then follow the deployment guide if application code changed.
6. Update current documentation, migration/rollback instructions and release evidence together. A green PR alone is not a live deployment.

## Required boundaries

Never commit `.env`, real records/photos/documents, tokens, SQL dumps, QR secrets or provider credentials. Public web values must be publishable only. Use private disclosure to the repository owner for security issues; include sanitized reproduction, affected commit and impact, not real personal data.

Do not bypass MFA, self-approval protection or scope checks for convenience. Do not grant runtime UPDATE on immutable histories to fix a lock error. Do not replace encryption/HMAC keys without a reviewed migration. Do not turn self-reported profiles into official counts or roles. Review search/serializer allowlists for each new field.

## Documentation and visual assets

Documentation is rooted at [docs/index.md](docs/index.md); source links are relative so a clone works offline. Current baseline is distinguished from historical evidence. Provider allowances need a checked source/date; measured results need method and limitations. Do not fabricate adoption, uptime, coverage or security certification.

The architecture explorer is self-contained under `docs/visuals/`, uses only local assets and illustrative flows, and needs no production credentials. It must remain usable without motion and at narrow widths. The README GIF is a preview; GitHub does not execute HTML. Regenerate the diagram/GIF with the supplied Python script (Pillow dependency) and inspect the output before committing binary assets.

Offline link/structure verification: `python docs/check_docs.py`. The explorer UI control checks require the existing web jsdom development dependency; application suites and provider acceptance remain separate.

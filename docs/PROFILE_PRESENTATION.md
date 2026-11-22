# Saved profiles and private identification

Saving a personal profile switches to a read-only card. Edit profile reopens the form; Cancel restores saved fields without clearing unsaved reading-list work. Profile and reading saves use distinct sections; the API enforces that reading saves can change only books. Existing profiles still open as cards and require identification at their next profile save.

The owner supplies either NID (10, 13 or 17 digits, Bengali digits accepted) or passport (5–20 letters/digits). These checks validate format only, not identity or document authenticity. Numbers remain inside the existing encrypted personal-profile JSON, excluded from review responses, member search, exports and directory responses. The owner card shows only the last four characters. No document scans are requested.

Photo selection accepts JPG/PNG/WebP up to 5 MB, processes locally into a 384px square JPEG and submits it through the authenticated profile API. The API verifies JPEG decoding and dimensions (max 512px), caps bytes, strips metadata by re-encoding and encrypts the result. No public bucket, external photo URL or schema migration is needed. Pillow is already pinned in requirements.lock and is now an explicit direct requirement.

Directory photos require explicit sharing opt-in (except the owner viewing their own summary). The unified directory can show unlinked consented profile summaries to Thana Admins; ward/unit visibility requires an approved PersonalProfile.member_id link in scope. See DIRECTORY_SEARCH.md. Existing personal-record scope and MFA checks still apply. No automatic member creation/linking or unrestricted public profile access is introduced. Directory summaries use official member fields, rather than treating self-reported category/position as an official grant. Removing photo or opting out immediately removes it from subsequent directory responses. The same ProfileCard component renders owner and directory views, with owner-only fields omitted in directory mode.

Dashboard search navigates to the existing scoped people directory; View profile opens the summary, and Edit profile opens routine record editing. Routine saves return to the card. Sensitive organizational transitions retain the independent approval workflow.

Deployment: API first (Render, main, manual latest-commit deployment), then frontend automatic Cloudflare Pages build. Existing 0005 schema and encryption configuration remain unchanged. Do not put identity numbers or private photos into source control or logs. Validation uses synthetic records only.

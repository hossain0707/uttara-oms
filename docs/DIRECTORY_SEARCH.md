# Authorized people search

People & records uses `/api/v1/directory`, combining organizational members with saved, consented personal-profile summaries. A linked profile appears once as its official member record. Self-reported categories remain visibly marked and do not change membership counts, permissions, or official categories.

One name field accepts either Bengali or English. Results preserve the saved spelling. Search normalizes Unicode, whitespace, punctuation and English letter case and matches partial keywords. Bengali marks are retained. Cross-script transliteration is not performed. Full phone search is retained for organizational records only.

Thana Admins can see consented unlinked profile summaries. Ward and unit staff see only official members within their approved scope and their linked profiles. A self-requested unit cannot grant visibility. Report-only viewers have no personal directory access.

Unlinked summaries expose only name, occupation, responsibility, self-reported category and account status. Photos require directory-sharing consent, except the profile owner's own view. Identity document numbers, private addresses, phone numbers, email, reading lists and reports are excluded. Organizational records retain existing authorized fields. Profile edits remain with the owner; this view does not automatically create a membership record.

Names remain encrypted at rest. Matching currently scans only authorized rows on the server, with stable sorting and pagination after deduplication. This suits the current small deployment; larger datasets will require an explicitly designed encrypted search index. No migration or plaintext name backfill is required. Audit logs record result counts, never search text.

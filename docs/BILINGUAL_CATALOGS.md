# Bilingual guided catalogs

Release follow-up: 2026-11-21 Asia/Seoul. Suggestions are bundled locally; typed addresses, occupations and book queries are not sent to a third-party search provider.

## Coverage and provenance

- Geographic snapshot: nuhil/bangladesh-geocode, https://github.com/nuhil/bangladesh-geocode, retrieved 2026-11-20. Included 8 divisions, 64 districts, 495 upazilas and 4,540 unions. This is a third-party administrative snapshot, not a verified current street/building directory. Preserve apps/web/data/GEODATA_LICENSE.txt (MIT, copyright Nuhil Mehdy).
- Source files: divisions/divisions.json, districts/districts.json, upazilas/upazilas.json, unions/unions.json. Only ID, parent and bilingual display names are bundled. Upstream URLs and coordinates are omitted. Dataset updates require reviewing parent integrity tests and current naming.
- Uttara local search labels supplement upazilas with Uttara Model Thana/East/West and numbered-sector suggestions. These are navigation labels, not declarations of administrative jurisdiction or OMS permission scope; unlisted/corrected addresses can always be entered manually.
- Book catalog: 83 distinct working title transcriptions across 10 topic sections from the owner-supplied report-book syllabus photos. English names are search transliterations, not verified published English editions. Authors, edition/page totals and ambiguous text are not invented. Some uncertain entries were omitted; owner editorial verification remains needed before calling the transcription complete. Full book text is not included.
- Occupation list: 22 generic bilingual suggestions. Responsibility list: 21 descriptive thana/ward/unit suggestions. These are editable vocabulary examples, not official appointment records.

## Behavior

Type Bengali or English, including partial words. Matching uses Unicode normalization, case-insensitive keywords and explicit alternate names. Results are limited to 30; type more to narrow them. Arrow keys/Enter choose results; Escape dismisses them; IME composition does not trigger selection. Manual custom values remain supported.

Addresses support direct location search or division → district → upazila/thana → union/area selection. Changing a parent clears its dependent selections. Selecting suggestions alone does not overwrite an existing saved address: use the explicit apply button, then edit house/road/manual text. Save the normal profile/member form to persist it. Existing plain-text encrypted fields and API contracts remain intact; no migration is required.

Books are filtered by topic section. Category selection, book reading and descriptive position selection never grant roles or change official membership. Existing approval and authentication checks are unchanged.

## Verification

Tests cover Bengali/English prefix/alias matching, keyboard choice, manual values, direct Uttara search, parent clearing, preservation of saved address text, dataset parent integrity and bounded unique book titles. Existing profile/books/report operation regressions remain required.

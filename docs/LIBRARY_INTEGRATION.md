# Source-linked library — 2026-11-21

The personal workspace now has a Library & syllabus tab, also linked in the organizational sidebar at /my/#library. All signed-in users can browse it. It reuses the existing own-profile reading form and encrypted API persistence; no database, auth, or permission migration is required.

## Source and coverage

Metadata was collected from the visible BJILibrary syllabus pages on 2026-11-21: Worker (35 unique book links), Rukon A (44), Rukon B (73), annual educated/B (24), higher study (165). These are book-link counts, not required-book totals. Tracks can overlap; headings, alternatives, chapter/volume restrictions and non-book memorization requirements remain authoritative on the linked full syllabus. Browsing a track does not assign it, and book completion never grants membership or roles.

Data lives in apps/web/data/library.json. Original label and source URL are retained per entry; book labels are stripped of list numbering/author suffixes for compact titles. The annual continuing-study block is explicitly separated from Seerah. English subject names and selected keyword aliases support browsing alongside original Bengali book titles. It is a reviewed snapshot, not a live synchronization service.

Observed book-cover thumbnails from the library's Worker category pages are linked where available (34 of the 35 Worker links). Missing/failed images use a typographic title card, never an invented edition cover. Thumbnails remain hosted by the original library; no PDFs or full book text are copied. Image requests and outbound links use no-referrer. The static CSP img-src allows only the additional https://bjilibrary.com origin; scripts, frames and connections are not broadened. Availability and edition correspondence can change at the source.

## Reading behavior

Add to my reading stages a zero-page entry in the existing form. It does not immediately write a profile or claim completion. My reading list opens Targets & books; Save reading progress persists the list with existing optimistic version checks and profile consent. Duplicate identical titles and the 100-entry bound disable adding. Existing manually entered titles remain editable and unchanged. Page totals must be entered for the actual edition; totals are not invented. Counts explicitly include unsaved changes and are based only on the user's own list, not inferred syllabus progress.

No new assignment model, automatic target import, external-site reading tracking, direct audio player, paid dependency or role grant is introduced. Audio and report resource links open the original source.

## Verification

24 frontend tests cover existing behavior plus English keyword search, track selection, source-origin restrictions, duplicate prevention, staging, and saving reading entries while preserving unsaved profile edits. TypeScript passes. Production static export is checked with the existing public production configuration. CI and live deployment evidence are recorded separately after release.

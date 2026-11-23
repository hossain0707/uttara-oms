# User guide

Start at [Uttara OMS](https://uttara-oms.pages.dev). The first API-backed screen can take longer when the free backend wakes up. An account gives access to your own workspace; administrative tools require separate approval.

## 1. Create an account or sign in

| Method | Steps |
| --- | --- |
| Email and password | Choose **Create an Account**, enter email and matching passwords (minimum eight characters), then complete the emailed confirmation code. Returning users use **Login**. |
| Email code | Choose the email-code alternative, enter your email, request a code and verify the six-digit code from your inbox. No Google password is entered in OMS. Availability depends on email delivery and the enabled build flag. |
| Google | Choose **Continue with Google**, complete Google's sign-in and return to OMS. This is separate from receiving an email code in Gmail. |
| Forgot password | Open **Forgot Password?**, request the email, open its recovery link in the requesting browser, set a new password and sign in again. Enrolled authenticator accounts must complete that verification before changing the password. |

Use the newest email code, check Spam and wait for the resend timer instead of sending repeatedly. The configured email code expires after ten minutes. Your email code and authenticator code are different. Never share either code or your authenticator QR.

## 2. Complete My workspace → My profile

1. Enter your full name **once**, in Bengali or English. A second-language name is not required. It is displayed as saved.
2. Enter contact details, occupation and responsibility. Suggested positions are descriptions, not appointments or access permissions.
3. Search an address directly, or choose division → district → upazila/thana → union/area. Apply the selection explicitly, then add house/road details. Manual and unlisted addresses are supported.
4. NID or passport information is not required or displayed. Enter your name and consent to save your profile.
5. Optionally choose a JPG/PNG/WebP photo up to 5 MB. The app processes it before saving. Photo sharing in the authorized directory is a separate checkbox.
6. Select a requested unit/category if appropriate, read the consent statement and choose **Save my profile**.

After saving, a profile card appears. Choose **Edit profile** to reopen the form or **Cancel editing** to restore saved profile fields. NID and passport fields are absent from both the form and saved card. Private profile information and reports have different visibility rules described in [the data model](DATA_MODEL.md).

If no active units exist, save without a unit and ask an administrator to configure the hierarchy. Requested units and self-reported categories do not change official membership or administrative access.

## 3. Find books and record progress

Open **Library & syllabus**. Choose a syllabus track or subject and search for a title. Book covers link to the source where available; missing covers use a title card. The full source syllabus remains authoritative for chapters, alternatives and memorization requirements.

**Add to my reading** stages an entry; it does not save automatically. Open **Targets & books**, enter the page totals for your edition, then **Save reading progress**. A wholly empty new row is ignored; a partially filled row needs a title. Up to 100 reading entries are supported. Completed pages cannot exceed a nonzero total. Reading a book does not automatically promote a member or grant a role.

## 4. Enter daily and monthly reports

1. Save your profile and consent first.
2. Open **Daily & monthly reports**, choose a current or previous month and enter a day's values.
3. Add/update the daily entry in the month's list before saving. Dates must belong to that month and cannot be in the future; there is one entry per day.
4. Save a draft while working. Enter a monthly summary if needed.
5. Ask the main administrator to assign a different responsible reviewer before submitting.
6. Submit when complete. A submitted or reviewed report cannot be edited until returned by its assigned reviewer. A returned report can be corrected and resubmitted.

| Metric | Unit |
| --- | --- |
| Prayers | Count of prayers |
| Literature | Pages |
| Organizational work | Minutes |
| Quran | Pages |
| Hadith | Items |

Targets are assigned by an administrator; there are no universal automatic targets. For example, 140 prayers, 300 literature pages and 90 organizational minutes are possible configured targets, not evidence that every user has those assignments. Report progress compares entered totals with the targets captured when that report was saved. Choose the available PDF/XLSX export for your own saved report.

## 5. Request an organizational role

Open **Request permissions** in My workspace, choose an available role and an active matching scope, then submit. A saved application remains pending until a qualified main administrator decides. Approval can unlock the authenticator setup screen. Normal accounts do not need an authenticator just to use their own workspace.

## 6. Set up the authenticator if required

Choose **Set up authenticator** in the verification screen. Open a trusted TOTP authenticator on your phone, add an account by scanning the displayed QR from another screen, then enter the generated six-digit code in OMS and choose **Verify code**. Keep the QR private. If setup was never verified, use **Reset unfinished setup** and enroll again. If a verified factor is lost, contact the authorized administrator; resetting an unfinished setup does not recover a lost verified factor.

## 7. Search people when authorized

Open **People & records** and type part of the saved name. `hos` can match `Hossain`; Bengali fragments match Bengali saved names. The app does not automatically translate or transliterate between scripts. Filters apply to category and status. **View profile** opens the permitted summary.

Thana Admins can discover saved consented profile summaries; ward/unit officials see approved linked records within their scope. A missing result can mean the profile has not been saved, the name differs, a filter is active or the record is outside your scope. Only official member cards offer organizational editing; unlinked personal profiles are edited by their owner.

## Common problems

| Message or symptom | Action |
| --- | --- |
| No code received | Check the address, latest message and Spam; wait for cooldown. Ask the operator to check delivery/rate limits if it persists. |
| Profile/report changed; reload | Another save changed the version. Preserve your unsaved text, reload and reconcile before retrying. |
| Missing reviewer | Ask the main administrator for a reviewer assignment; draft saving remains available. |
| Approval disabled for your request | A separate authorized reviewer must approve. Creating the request is not the approval. |
| Failed to fetch | Check connectivity, allow the free backend to wake and retry once. Report the time and screen, without screenshots containing codes or private documents. |
| Wrong authenticator code | Check the phone's automatic time and use the current code for the correct OMS entry. |

Sign out when finished on a shared device. Do not put identity numbers, private reports, codes or credentials into GitHub issues.

## Why dashboard totals can differ

Registered people reflects current saved profiles and their self-reported categories. Official membership reflects confirmed organizational records, assigned units and historical reporting dates. Saving a profile does not automatically confirm official membership or grant permissions. The Master Admin reviews and links/creates an official member; the dashboard shows how many saved profiles await this confirmation.

## Reporting book

Open **My workspace → Daily & monthly reports**. The reporting book has a daily page, monthly summary and day-by-day ledger. On phones, pages stack vertically.

1. Choose the reporting month and date. Calendar checkmarks identify recorded dates; choosing one loads its values.
2. Enter daily values and notes, then choose **দিন যোগ / হালনাগাদ করুন**. This updates the local monthly form; it is not saved yet. Blank means unreported; zero means none.
3. Check monthly totals and assigned targets, write the monthly evaluation/next-month plan, consent, then choose **খসড়া সংরক্ষণ**.
4. When a reviewer is assigned, use **মাসিক রিপোর্ট জমা দিন** and confirm. Submitted/reviewed reports are locked; returned reports can be corrected.
5. PDF and Excel download the latest saved report, excluding unsaved changes. The PDF uses the green-and-gold reporting-book layout with monthly totals and a daily ledger.

Measurements retain their original meaning: prayers (count), Quran/literature (pages), Hadith (items), organizational work (minutes). No sample values are inserted automatically. Month/day switches warn before discarding unsaved edits; closing/reloading warns while report edits remain unsaved. Targets never grant membership or administrative permissions.

Daily Salah accepts whole numbers from 0 to 5; congregational Salah must be no greater than the entered total. Monthly totals simply add reported values. There is no monthly maximum calculation or summary widget.

The daily book includes Quran studied, Hadith count, literature pages, Salah and congregational Salah, aggregate meetings/contacts, books distributed, family meetings, social work, donated hours, visits, report kept and self-evaluation. Check a completed activity; uncheck it for an explicit No, or use Clear to leave it unknown. Monthly checkbox totals count Yes days and show how many days were reported. Time donated accepts hours to two decimals (0–24). Original Quran page counts and organizational minutes remain separate, unchanged fields.

The third page stores achievements, incomplete work and next-month plans separately, alongside additional comments. The assigned reviewer sees all submitted fields and can review or return the report. PDF and Excel include the expanded fields, reflections and reviewer comments. This does not change membership, permissions or report privacy. Meeting/contact fields are aggregate counts, not named target lists.

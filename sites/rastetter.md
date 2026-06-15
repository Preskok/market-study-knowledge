# rastetter (DE, buyer-stock)

## Current status
🔴 **2026-06-05 OPEN** — Full site rewrite: homepage now redirects to `/shop/`, no trace of `audaris` API or client IDs. Needs full crawler rewrite. Ticket MAR-2113 created. Part of same pattern as ahm/schmidt-automobile. Part of a group of sites that regularly fail to prepare listingUrls at midnight.

## History & quirks (newest first where known)
- **2026-06-05** — Full site rewrite discovered: `rastetter.de` homepage now redirects to `/shop/`. No trace of `audaris` API or client IDs in browser network tab. Was an API crawler visiting `api.audaris.de`. Full rewrite of crawler needed — ticket MAR-2113 created (unassigned, Medium priority). Also: deactivation prevention check missed this site because it was disabled before the check ran (`shouldSiteRunToday()` logic). [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780304827309509)
- **2026-06-05** — First 302 status exception not caught by any `isResponse*()` → 302 HTML saved to S3 as valid → all subsequent reruns read poisoned cache and fail. Matea investigated and deleted S3 key for rerun — but then discovered full site rewrite (above). [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780304827309509)
- **2026-05-25** — Problem preparing listingUrl messages (alongside ahm and schmidt-automobile). 6AM auto-rerun succeeded ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1779682055148269)
- **2026-05-14** — Problem preparing listingUrls at midnight; automatic rerun at 6AM succeeded ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1778485086288569)
- **2026-04-21** — Automatic rerun triggered and completed successfully ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1777349596109229)
- Site-side duplicates (~700).
- Wrong API URL → 400-600 dupes/day.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

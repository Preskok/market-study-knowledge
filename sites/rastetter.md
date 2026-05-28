# rastetter (DE, buyer-stock)

## Current status
✅ **2026-05-25 OK** — Recurring midnight listingUrl prep failure; 6AM auto-rerun succeeded. Part of same pattern as ahm/schmidt-automobile. Part of a group of sites that regularly fail to prepare listingUrls at midnight.

## History & quirks (newest first where known)
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

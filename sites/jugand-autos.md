# jugand-autos

## Current status
✅ **2026-06-09 RESOLVED** — All vehicles crawled the following day. ECONNRESET was transient proxy issue, self-resolved.

## History & quirks (newest first where known)
- **2026-06-09** — All vehicles crawled; ECONNRESET proxy issue self-resolved. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
- **2026-06-08** — 586/1060 vehicles prepared. Root cause: ECONNRESET with proxies on listing requests. Monitoring next crawl. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
- Full site 404/500 outage 2+ days (external).
- Intermittent "Prepared 0 listingUrl" — 6/7/8 AM rerun fixes.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

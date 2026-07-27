# jugand-autos

## Current status
✅ **2026-07-16 RESOLVED** — Site recovered same day and we got all vehicles after the 05:00 UTC 502 Bad Gateway.

## History & quirks (newest first where known)
- **2026-07-16** — Site back up and all vehicles crawled, following the 05:00 UTC 502 outage below. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784182438927749)
- **2026-07-16** — 502 Bad Gateway at 05:00 UTC crawl (selector returned 0 brands → intentional auto-rerun throw). Site still down at test time; waiting for recovery. Monitoring next crawl.
- **2026-07-07** — Got all vehicles today; removed from deactivation lock. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1783311314203489)
- **2026-07-06** — Problem preparing listingUrl messages: ECONNRESET and failed requests, reproduced locally too. Same pattern as the 2026-06-08/09 episode. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1783311314203489)
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

# autocenter81

## Current status
✅ **2026-07-23 CONFIRMED OK — false alarm** — A slow multi-day drop (128→119, later 125) initially looked concerning against the site's HTML-stated 191/194 vehicles, but the site's own API `filtered_result_count` (127) matches what we crawl — the HTML-displayed number is stale/inaccurate. No action needed.

## History & quirks (newest first where known)
- **2026-07-23** — 125 vehicles crawled; site HTML still states 194, but the underlying API's `filtered_result_count` field actually returns 127 — confirming the crawl is correct and the HTML count is just stale. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784807117439059)
- **2026-07-21** — Slow drop in numbers over the last 7 days, steady at 119 (down from 128) for the last 3 days; site HTML currently states 191. Flagged to check further on Thursday — see 07-23 resolution above. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784633323659949)
- Supplier/partenaire catalogue (not on-stock).

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

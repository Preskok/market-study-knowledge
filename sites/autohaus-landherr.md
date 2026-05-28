# autohaus-landherr

## Current status
✅ **2026-05-27** — Healthy. Apparent inflated count is ES rollover duplicates, not a bug.

## History & quirks (newest first where known)
- **2026-05-27** — Alert showed 629 total vs 444 on site. 7-day cardinality query on URL field returned 442 unique — matches the real site count. Extra 187 are ES rollover duplicates: same `storeId` re-indexed into a new backing index after a rollover event, search alias returns both copies. Use `cardinality` on `URL` field (not raw doc count) to get the true vehicle count. Code confirmed healthy locally.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

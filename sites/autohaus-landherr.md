# autohaus-landherr

## Current status
🟡 **2026-06-05 WATCH** — ~150 duplicates still present (crawled 502, unique 352). Unique number matches site stock. Same self-resolving pattern as March 2026 — monitoring until next week. Apparent inflated count is ES rollover duplicates, not a bug.

## History & quirks (newest first where known)
- **2026-06-01→06-05** — ~150 duplicates persistent (crawled 502, unique 352). Stock dropped to 351 on site. Same pattern as March 2026 duplicate episode which self-resolved within days. Matea monitoring; unique number matches site correctly. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780304827309509)
- **2026-05-27** — Alert showed 629 total vs 444 on site. 7-day cardinality query on URL field returned 442 unique — matches the real site count. Extra 187 are ES rollover duplicates: same `storeId` re-indexed into a new backing index after a rollover event, search alias returns both copies. Use `cardinality` on `URL` field (not raw doc count) to get the true vehicle count. Code confirmed healthy locally.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

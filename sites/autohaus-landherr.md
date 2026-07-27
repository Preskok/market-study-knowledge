# autohaus-landherr

## Current status
ℹ️ **2026-07-06 INFO** — Vehicle count down ~14% (334 vehicles on site) confirmed as a genuine stock decrease, not a crawler issue. Earlier duplicates watch (2026-06-08) status unconfirmed since — recheck if it resurfaces.

## History & quirks (newest first where known)
- **2026-07-06** — Vehicle count down ~14%; checked against the site directly — 334 vehicles currently listed, confirming a genuine stock decrease rather than a crawler/duplicate issue. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1783311314203489)
- **2026-06-08** — Second check in week 08.06: duplicates still remain, unique count still correct. Matea monitoring further. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
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

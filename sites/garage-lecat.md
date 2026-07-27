# garage-lecat

## Current status
🟡 **2026-07-24 WATCH — same-day recovery (again)** — Did not crawl; the site's own API was returning 0 vehicles (reproduced independently in browser too — confirmed site-side, not our bug). API came back later the same day; Matea deleted the poisoned S3 response and reran manually on prod, recovering all vehicles. Same recurring midnight-fails/rerun-recovers pattern as 07-13 and 06-29 — still not permanently fixed.

## History & quirks (newest first where known)
- **2026-07-24** — Did not crawl; site's own API returned 0 vehicles (confirmed in browser too, not a crawler bug). Fixed itself later the day; Matea deleted the poisoned S3 response and reran manually on prod — all vehicles recovered. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784877596835139) / [resolved](https://preskok.slack.com/archives/C0859KQ45B2/p1784896584889989)
- **2026-07-13** — 98% drop in vehicles today; local run was ok, ran manually on prod and got all vehicles back same day. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1783921161295049)
- **2026-06-29** — Rerun at 6am successful. Pattern: midnight crawl may fail requiring 6am rerun. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782709643021479)
- **2026-06-08** — Second check: gap persists. Site 327, we crawled 312 (15 missing, <5%). Matea monitoring. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
- **2026-06-01→06-05** — Persistent ~5% gap: site 332→327 vehicles, we crawled 315→312. Gap consistent over multiple days. Matea monitoring until next check. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780304827309509)
- 9 vehicles one day (self-recovers).

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

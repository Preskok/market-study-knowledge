# gruppo-piccirillo (IT)

## Current status
✅ **2026-07-23 CONFIRMED OK** — Slight drop noted, but it matches the number on site — legitimate fluctuation, not a regression of the 06-05 API-params fix below.

## History & quirks (newest first where known)
- **2026-07-23** — Slight drop in vehicle numbers observed; confirmed it corresponds to the number on site — no issue. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784806871131969)
- **2026-06-05** — Drop in numbers noticed after moving to general queue. Root cause: API query params were not matching what the site uses → fewer vehicles returned. Fix: updated query params to match site. Deployed via PR #54 and crawler rerun. Monitoring next week for numbers match and unique vehicle count. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780304827309509)
- `buildId` removed, details API gone — full refactor (MAR-2069).
- Since 25.11.2024: crawler gets listings but details URL generation fails (API `//filtri/...` double-slash). Vehicles go to Old index WITHOUT URL (can't dedup by URL → "missing all vehicles" email fires because unique-URL count is 0). Data index and S3 get nothing. Buyer-stock site — we've lost months of data until refactor lands.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

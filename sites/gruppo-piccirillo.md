# gruppo-piccirillo (IT)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
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

# autodiler (ME?)

## Current status
✅ **2026-06-04 RESOLVED** — Site was down (Cloudflare unable to connect to host). Local run worked; Matea reran on prod → all vehicles recovered ✅.

## History & quirks (newest first where known)
- **2026-06-04** — Website down (Cloudflare unable to connect to host). Crawler prepared 0 vehicles. Matea ran locally — worked fine. Reran on prod → all vehicles recovered ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780304827309509)
- Crawls commercial vehicles (kombi vozila) — ~950/day.
- 500 responses = ad no longer exists → must go through `isResponseNotFound()` (also verify body-text indicator) to avoid wasted retries.
- Added value `Metan` to fuel-type regex mappings.
- "Vehicle count mismatches" when same URL appears across listing pages — handle in `iterateThroughVehicleListPages()` (PR 2022 reference).

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

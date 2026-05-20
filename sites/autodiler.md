# autodiler (ME?)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
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

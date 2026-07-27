# oglasnik (HR)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- Removed `www.` from baseUrl; beta-site migration (307).
- 100% drop one-day blip → OK next day.
- **dateOfFirstRegistration**: Site only provides production year (not month/day). Workaround: for used vehicles, store `[year]-07-01` (production year + 6 months) as synthetic DOFR approximation. This gives downstream users a usable date while the `16`-day convention (used on avto-net) could also work. Document whichever convention is chosen.
- **~1000 vehicles with brand/model only in title** (Jan 2023): Not on any brand+model sub-listing — only accessible via full listing without brand/model filter. Crawled by iterating those listings separately. Fix `getNextPageUrl()` if pagination breaks (+500 found after that fix).

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

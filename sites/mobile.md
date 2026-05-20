# mobile (DE)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- Akamai on base HTML (2026-03). Mobile API NOT blocked.
- One-day ~200k saved-volume drop (recovered after Marko consult — root cause not pinned, likely transient anti-bot blip).
- Hardcoded brand list fallback when HTML unreachable.
- Added `"Allradantrieb"` AWD keyword.
- 2025-04-06 429 wave; 2025-04-30 device API returned 403 for hit-count endpoint.
- 2025-04-30: `promo.mobile.de/sites/umlackiert/` announced site redesign → mobile devices API endpoints started returning 403 for listings/details (still worked for brands/models + filter counts). Disabled crawler through holidays; deactivation split over 2 days (600k+600k) to avoid mass-deactivating. Restored May 2025.
- 130k+ requests/day — moving to ScraperAPI not viable at full crawl (too expensive).
- fuelType parsing added on listings (Jul 2025) — hybrid priority over diesel fix. Electric vehicles also now save fuelType on mobile.
- Brands JSON was missing `XPENG` (Jul 2025) — periodically diff brands JSON against site to avoid whole-brand misses. 19 brands missing/obsolete vs GS discovered at audit.
- dealer `branchName` missing → ~180-320 "Dealers transforming" logs/day (low-pri to fix given scale).

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

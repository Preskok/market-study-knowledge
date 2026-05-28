# mobile (DE)

## Current status
🟡 **2026-05-13 DATA QUALITY OPEN** — ~65k vehicles incorrectly assigned country=DE (non-EU/unrecognized countries fall back to DE). Fix: add Denmark + Czech Republic to country list, skip vehicles with unrecognized countries. Added to MAR-2067.

## History & quirks (newest first where known)
- **2026-05-13** — Data quality issue: only 8 non-DE countries hardcoded (behaviour from 3 years ago). ~65k vehicles with non-EU/unrecognized countries saved as DE (<5% of total mobile.de stock). Also found: `trimLine` attribute in API response can be used as `rawVersion` directly (improvement also added to MAR-2067). Decision: add DK + CZ to country list, skip all other unrecognized countries. [Slack](https://preskok.slack.com/archives/C04K2LP3AG0/p1778679073096599)
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

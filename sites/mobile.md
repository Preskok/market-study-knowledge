# mobile (DE)

## Current status
🟡 **2026-05-13 DATA QUALITY OPEN** — ~65k vehicles incorrectly assigned country=DE (non-EU/unrecognized countries fall back to DE). Fix: add Denmark + Czech Republic to country list, skip vehicles with unrecognized countries. Added to MAR-2067.

## History & quirks (newest first where known)
- **2026-07-21** — Drift-detection flagged increased null values (missing `engineType`/`driveTrain`/`engineCapacity`/`numberSeats`/`numberDoors`) for `mobile`. Investigated at length: the reference dataset turned out to have been captured right during a temporary dip in null values around 2026-02-23→02-26, so the "current" numbers are actually just a return to the real baseline, not a regression. `autoscout-ch` (a newer crawler, not in the reference dataset since it launched 2025-08-29) was separately found to have a similar pattern of missing the same 5 fields. Decision: extend the drift-detection reference window to ~1 week to avoid this kind of narrow-window artifact going forward. [Slack](https://preskok.slack.com/archives/C04K2LP3AG0/p1784538476356069)
- **2026-06-24→2026-06-26** — `engine` field was being set to the same value as `version` when an exact version was present on the ad. Correct behavior: `rawEngine` should remain title-based; only `rawVersion` should use the version field. Matea flagged it; Filip prepared and deployed fix. Confirmed working 2026-06-26: 93k vehicles crawled, 28% validation logs, version fix + engine rollback both working ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782105347592299)
- **2026-06-16** — `fetchMakes()` refactored to extract brands from `window.__INITIAL_STATE__` in homepage HTML (makes API redirects to homepage). HTML has no semicolons between `window.*` declarations — use `split('\n')[0]` to extract the JSON string. Brand shape is `{ i: number; n: string }` at `shared.referenceData.categoryData.Car.data.ms`.
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

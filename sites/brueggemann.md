# brueggemann (DE, buyer-stock)

## Current status
✅ **2026-06-09 RESOLVED** — B&M selector fix deployed; Matea reran on prod, all vehicles recovered.

## Test brand+model
- brand: Abarth
- model: 500
- verified: 2026-05-09
- notes: First brand alphabetically in dropdown. Strategy A. `crawl.general.#` queue. parseDealer not overridden (N/A). `shouldValidateListingVehicle: true`. `rejectUnauthorized: false, followRedirect: false` required — 303/500 = not-found.

## History & quirks (newest first where known)
- **2026-06-09** — B&M selectors changed on site; crawler preparing 0 listing URLs. Fix: updated B&M selectors (only selector change, no structural change). Deployed by Filip, rerun on prod by Matea → all vehicles recovered. Deactivation lock unlocked. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
- **2026-05-09** — Flow test passed: getBrandsAndModels ✅, 2 Abarth 500 vehicles ✅, equipment ✅. `IsListingValidatedVehicle: false` (fresh URLs). parseDealer not overridden → N/A.
- Full refactor (MAR-2064).

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

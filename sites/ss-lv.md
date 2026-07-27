# ss-lv (LV)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- Transmission HTML changed.
- ECONNRESET site-side issues.
- Same vehicle on multiple listings (supermodel + model) → name field alternates daily (partial trim as vehicle toggles between listings). Mitigation: ignore SVL name-only changes for this site. Backup sources researched (auto24.lv ~289 vehicles, longo.lv ~1.1k, pp.lv ~4k).


<!-- merged from second source section -->

- Title (`name`) from listing = random free-text description, NOT a structured field. Saved as-is (max 2048 chars, \n present). DataAPI should not rely on it for model extraction.
- Skip ads with raw price = `"buy"` — they are want-to-buy listings, not for sale.
- Skip ads with `"changing"` indicator (owner wants to exchange for another vehicle). These appear in the wrong brand listing.
- Vehicles **without** price → save (Gregor decision — they're still market listings).
- `"Others"` category contains non-vehicle ads (parts, accessories) — filter by vehicle type flag.
- `coverImageUrl` excluded from `partialVehicle` (deleted to avoid SVL failure from image URL changes).
- Categories: `/en/transport/cars/` (personal), `/en/transport/cargo-cars/` (trucks). LCVs like Crafter/Ducato/Trafic come through the cars category and ARE crawled. Heavy trucks → skip.
- Field limits: rawBrand/rawModel/rawVersion/engine/bodyType = 2048; transmission/driveTrain/fuelType = 32.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

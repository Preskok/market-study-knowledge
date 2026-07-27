# vozi (HR)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- **2025-09-22** — MAR-1952: null guard added for `rawVehicles` being undefined (`rawVehicles.Free ?? []` crashes if `rawVehicles` itself is null — the `?? []` only guards `Free`, not the parent). Spike on Sept 22 likely from DL messages redelivered after fix deployed.
- **2025-07-31** — MAR-1909: `parseVehicleParams.additional = { countryName, countryKey }` was replacing the entire `additional` object, wiping `additional.url`. Vehicles were still saved daily (with `url: null`, `storeId = md5(null)` is consistent so bulk saver found them as "existing"). The fix (assigning `countryName`/`countryKey` as properties instead) restored real URLs → new storeId for every vehicle → mass re-index spike on deployment day.
- `additional` overwritten before `url` assigned — pattern: replacing `additional` entirely (not mutating) silently wipes `url` and `vehicle` fields stored there.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

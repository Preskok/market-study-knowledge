# commauto (BE)

## Current status
🟢 **2026-05-09 OK** — Formal crawler-test-flow run. 1 Alfa Romeo GT vehicle saved. SVL fired (vehicle already in S3 from prior run) — `IsListingValidatedVehicle: true`. getBrandsAndModels ✅, listing→ES ✅, parseDealer N/A.

## Test brand+model
- brand: Alfa Romeo (first from getMappings API)
- model: GT (first model of Alfa Romeo)
- verified: 2026-05-08
- notes: Strategy B (single getMappings() API call, no per-brand HTTP). Pipeline reaches ES in ~20s. Equipment sub-arrays empty (notCategorised only). parseDealer not overridden. ES field is `URL` (uppercase), not `Url`.

## History & quirks (newest first where known)
- **2026-05-09** — Formal crawler-test-flow: getBrandsAndModels ✅ (1 msg), listing→ES ✅ (1 vehicle). SVL fired (`IsListingValidatedVehicle: true`) — vehicle was already in S3 from 2026-05-08 run. parseDealer not overridden → N/A. Equipment empty (this model has no listed equipment).
- **2026-05-08** — Flow test passed: getBrandsAndModels ✅, vehicle saved to ES with correct URL ✅. Previous "Url: null" finding was a false alarm — wrong ES field name queried.
- Safeguards removed to allow auto-rerun.
- Full URL + selector change Q1 2026 — disabled.
- Mar 2026: `www.commauto.it` → `commauto.it`, full ID structure changed, legacyUrl not reconstructable → disabled.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

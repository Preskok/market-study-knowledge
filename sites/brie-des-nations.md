# brie-des-nations (FR, buyer-stock)

## Current status
🟢 **2026-05-09 OK** — Flow test passed. 11 vehicles (Renault/Clio new stock), 6 dealers extracted, full detail pipeline.

## Test brand+model
- brand: Renault
- model: Clio
- verified: 2026-05-09
- notes: First brand+model alphabetically. Strategy A. Uses `crawl.general.#` queue. Single-dealer site — all vehicles have dealer. Equipment sparse (new-car stock). Base URL still `sofibrie.fr` (not `renault-noisiel.briedesnations.fr`).

## History & quirks (newest first where known)
- **2026-05-09** — Flow test passed: getBrandsAndModels ✅, 11 Renault Clio vehicles ✅, 6 dealers ✅. All `IsListingValidatedVehicle: false` (URLs changed since April 3 run — no SVL hits).
- Moved to `renault-noisiel.briedesnations.fr`.
- Two branches (Val d'Europe, Noisiel).
- **Pricing:** `listPrice` = catalog/factory price, `price` = seller price. Negative discounts are NORMAL here (dealer markup on limited-availability / custom configs) — not a bug.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

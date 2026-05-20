# cardoen (BE)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- bodyType filter removed. Later family-cars category narrowed.
- "Cardoen Advantage" = catalogPrice - cardoenPrice. Gregor decision 2025-02: this is NOT a discount and must NOT be saved as `discount`. Save only `catalogPrice` (from details) and `price` (from listing = cardoenPrice). Same pattern as star-terre negative discount.
- Listing has only `discountedPrice` (cardoen price), details have `catalogPrice` — OK to save only price from listing, catalogPrice from details.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

# e-motors (FR, buyer-stock)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- ~200 vehicle intermittent drops.
- Not collecting all vehicles — open ticket MAR-1726.
- Price structure: `basic price France + options + color = total price France`. Save `total price France` as `price`. `Total - customer advantage = Price E-motors TTC` → save TTC as `discountedPrice`. Fallback: basic price France if total missing.
- `isUsed` parsed from HTML flag — some vehicles have `isUsed=false` with mileage up to 16.5k (not a parsing bug — site labels them that way).
- Discount parse bug: periodic 80k+ DL messages logged against `e-motors` bulk insert (Nov 2024).

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

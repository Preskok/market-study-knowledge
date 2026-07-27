# sixtcarsales (DE, buyer-stock)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- New `JAHRESWAGEN` type — sum all keys.
- **Pricing trap:** `publicPrice` (incl. 19% VAT) → save as `price`. The field literally named `price` in their API is the NETTO price (ex-VAT) — do NOT use it. Classic brutto/netto trap.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

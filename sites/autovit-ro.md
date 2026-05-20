# autovit-ro

## Current status
**LEGACY — retired.** Removed; vehicles now ingested via olx-ro (same inventory).

## History & quirks (newest first where known)
- `followRedirect:false` in `getFetchRequestOptionsForDetailsUrlValidation()` blocks post-redirect validation.
- Dec 2024: URL structure inserted `-ver-` segment (`.../mazda-2-1-3i-ce-plus-ID…` → `.../mazda-2-ver-1-3i-ce-plus-ID…`). Old URL still works with `ID…` suffix. Disabled Feb 2025 after olx-ro (which also serves autovit-ro ads) went live — running both created duplicates.


<!-- merged from second source section -->

- Some vehicles priced in RON currency (not EUR). Decision: convert to EUR, save original currency. Open ticket MAR for conversion logic.
- HTML change (PR 1406, Aug 2024) → mass SVL for vehicles not revisited since listing unchanged. Normal to see PVL spike after HTML fix while details back-fill.
- CloudFront protection → frequent 403 blocks. Expected 26-37k vehicles/day; drops to 8k some days.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

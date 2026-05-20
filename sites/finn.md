# finn (NO)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- "Solgt" (sold) vehicles show no price on listing → skip, don't crawl.
- `mileage` / `rawOriginalPriceBrutto` SVL fails — known fragile fields.
- Both finn and biltorvet have leasing ads requiring explicit skip.
- finn shares some crawler logic with blocket — see `blocket.md` for shared-logic context.
- Price on listing = WITH re-registration fee (Norwegian law: re-registration fee ~1800 kr). Price on details = WITHOUT fee.
- Decision: save listing price (with re-registration fee). This allows SVL to work (prices match between listing and saved). If details price (without fee) were saved, SVL would fail every day since listing shows different price.
- Fee visible as separate field `(re-registration fee)` on details page.
- Sept 2024: details script removed from page — had to parse price from HTML with fee component split.
- MS_DL errors on DL queue for some parse errors — trace via request-id chain.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

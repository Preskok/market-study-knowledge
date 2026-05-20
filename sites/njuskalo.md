# njuskalo (HR)

## Current status
🟢 **2026-05-09 OK** — Flow test passed with VPN. 70 Abarth 500 vehicles, 1 dealer extracted ("AUTO SALON DENI"), equipment on 3/70 (private-seller sample). `IsListingValidatedVehicle: true` (S3 cache hit). Requires VPN to reach proxy — fails without it.

## Test brand+model
- brand: Abarth
- model: 500
- verified: 2026-05-09
- notes: Strategy A (break-on-first-push) works in ~60s and reliably yields rows. Site lists brands alphabetically; first-brand-first-model gives Abarth/500 with ~14 vehicles. Equipment field fully populated (Croatian terms). DealerId absent on Abarth sample (likely all private sellers — retest with a larger brand if dealer parsing needs verification). Strategy B would walk all brands first — slow on this site.

## History & quirks (newest first where known)
- **2026-05-09** — Flow test passed (VPN required): getBrandsAndModels ✅, 70 Abarth 500 vehicles ✅, 1 dealer ✅ ("AUTO SALON DENI"). `IsListingValidatedVehicle: true` (S3 cache, no detail fetch). Equipment 3/70 (expected low — private sellers). Without VPN: ShieldSquare blocks all HTTP+browser, never completes.
- **ShieldSquare** anti-bot (also branded as "DataDome for SEE"). Hardcoded brands list as fallback when ShieldSquare blocks brand/model API. Fallback triggers if API returns 0 brands — uses static list in code. Check brands list stays up to date when ShieldSquare starts blocking.
- **URL reuse**: Site reuses expired ad URLs for new vehicles of different brand. A VW may appear on a URL that previously had an Opel. Can cause brand mismatch in ES if vehicle is matched by storeId to old URL. Awareness only — not fixable at crawler level.
- 503 floods during maintenance.
- Partial model list → backup brand list fallback.
- Two URL paths: `/` and `/novi-auti/`.
- Highest proxy-end errors.
- 302/500 oscillation, no stable follow-redirect config.
- Private/dealer parser bug (MAR-1793), CO2 decimal.
- retryNr-not-reset → whole-brand loss.
- Covers HR market for us — `auti-hr` is not needed (product decision).

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

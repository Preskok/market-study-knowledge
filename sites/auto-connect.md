# auto-connect

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## Test brand+model
- brand: Volkswagen
- model: Golf
- verified: 2026-05-08
- notes: ~26 listings, all private sellers (DealerId=null is expected). For dealer-flow testing try BMW/7 Series (`albkor.import` account), but parseDealer is currently broken (see history).

## History & quirks (newest first where known)
- **2026-05-08** — `parseDealer` confirmed broken: selector `svg.bi-person + span:contains(Shitësi)` matches 0/416 cached pages. Seller section is React/Next.js client-side rendered (skeleton placeholders in the HTML the browser captures). All 968 auto-connect rows in local ES have `DealerId=null`. Fix path: extract dealer info from listing API response (`contact.address`, `vendorId`, `accountName`) instead of detail HTML — those fields are already in `partialVehicle.additional`.
- **2026-05-08** — local testing requires VPN: `fetchRequest` hardcodes `useProxy=true` with `PRESKOK_SET_2` (proxy.b2b-carmarket.eu:9001/9005). Direct curls to `autoconnect.al/api/data/makes` work without proxy, so the proxy is optional for the site itself but mandatory because of the crawler config.
- **2026-05-08** — first model alphabetically of many brands has 0 listings (e.g. AC's first model, Volkswagen's first model `181` is a vintage type). Don't pick `brandsAndModels[0]` for tests — pick a known-popular model (VW Golf, BMW 7 Series).
- **2026-05-08** — `shouldValidateListingVehicle: true` + previous run's data in local ES = SVL idempotency: pipeline runs in <2s, no "Finished saving data vehicles" log fires. Verify with `Site:auto-connect AND CreatedAt:[older]` in ES before running again.
- 403 from Cloudflare if multipart boundary is missing in request.
- 402 status not handled by default — must add to `isResponseNotFound()`.
- Site counter inaccurate.
- `"Diskutohet"` = "to discuss" in Albanian → treat as null price.
- ~25% of listings without price → save with `null` price (market representation).
- ~60% success rate with browser requests only, ~67% with ScraperAPI premium — premium not used (7% gain not worth the cost).
- "all" model listings (supermodel) must be parsed — some models not mapped to their own listing on site.

## Dealer accounts (for testing)
- `albkor.import` — sells BMW 7 Series, Audi A7, etc. Address: `Tiranë, Rruga Ali Shefqeti; Prishtinë, Lagja Kalabria`.
- `autokorea.al` — sells BMW i8 etc. Address: `Durrës`.
- `autookazion`, `shesblej_auto_vetura` — private sellers, no `contact.address`.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance: newest-first, YYYY-MM-DD format -->

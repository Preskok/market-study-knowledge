# auto-connect

## Current status
**2026-06-01** — Refactored to HTML/RSC listing parsing + scrape.do 1cr for makes+models. Branch `bugfix/MAR-2039-refactor-autoconnect` ready, not merged. Local test confirmed vehicles reach ES.

## Test brand+model
- brand: Volkswagen
- model: Golf
- verified: 2026-05-08
- notes: ~26 listings, all private sellers (DealerId=null is expected). For dealer-flow testing try BMW/7 Series (`albkor.import` account), but parseDealer is currently broken (see history).

## History & quirks (newest first where known)
- **2026-06-01** — **Full crawler refactor (branch `bugfix/MAR-2039-refactor-autoconnect`).** Site now uses Next.js App Router with RSC streaming — no `__NEXT_DATA__` script tag. Vehicle data (`posts` array) and brand list (`makes` array) are embedded in static HTML as `self.__next_f.push([1,"..."])` inline script tags — parsed without JS execution. Listings fetch via browser + preskok_set_2 → 200 OK (CF passes). Makes + models fetched via scrape.do **1-credit tier** (not super, `superAtRetry: null`). Confirmed: ~100 brands × 1 credit = ~100 credits/crawl for makes+models. `autoconnect.interoffice.al` is an internal backend domain — DNS does not resolve externally, XHR to it fails even with JS-enabled Puppeteer. **Listing URL format that has `posts` in RSC:** query-param form `?make1=BMW&model1=3-Series&type=car&page=N` — path form `/BMW/3-Series?...` returns only ~4 featured posts. Pagination: increment `page` param, stop when non-promoted count < `maxResultsPerPage` (32). `getNextPageUrl` calls `extractFromRscPayload` twice (once in `getVehicleListPageResponse`, once in `getNextPageUrl`) — minor inefficiency, acceptable.
- **2026-06-01** — **3000 alert email flood (2026-05-31 Saturday).** Root cause: Cloudflare returned HTTP 526 (SSL handshake failed) on `/api/car-details/search` calls. `isServerError()` only covered 500–507 → 526 was cached as valid → every subsequent listing consumer read the poisoned cache → `TypeError: listingVehicles is not iterable` → DL queue → alert × 3000. Fix: override `isServerError()` to include 520–527 in `AutoConnect.service.ts`. The `getVehicleListPageResponse` guard `listingVehicles ?? []` is additional defense-in-depth. PR #28 (MAR-2108, retry on 0 listings) was **not** the cause — that only retries the producer, not listing consumers.
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

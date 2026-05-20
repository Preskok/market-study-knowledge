# car-gr (GR)

## Current status
🟢 **2026-05-09 OK** — Flow test passed with VPN/ScrapeDo access. 2 Mercedes-Benz CLS 53 AMG vehicles saved. `IsListingValidatedVehicle: false` (no pre-existing S3 state — first local crawl). matchingDay=5 needed for Saturday testing. Requires VPN to reach ScrapeDo.

## Test brand+model
- brand: Mercedes-Benz
- model: CLS 53 AMG
- verified: 2026-05-09
- notes: First alphabetically on car-gr's Greek interface. Strategy A (break-on-first-push) works. matchingDay must be changed to day-of-week offset for today (5 = Saturday 2026-05-09). ScrapeDo required — fails without VPN. SVL check always fails on first local crawl (LocalStack S3 deserialization on NoSuchKey); vehicles fall back to VEHICLE type path with skipVisitingDetail=true, bypassing parseVehicleInput. Weekly queue must be clear before test or car-gr VEHICLE messages get buried.

## History & quirks (newest first where known)
- **2026-05-09** — Flow test passed (VPN required): getBrandsAndModels ✅, 2 Mercedes-Benz CLS 53 AMG ✅, equipment N/A (listings-only), dealers N/A (parseDealer not overridden). `IsListingValidatedVehicle: false` (first local crawl — no pre-existing S3). LocalStack S3 deserialization error on NoSuchKey causes all SVL checks to fail; vehicles re-routed as VEHICLE type with skipVisitingDetail=true (expected fallback). Purged weekly queue mid-test to unblock VEHICLE messages from backlog left by earlier unmodded run. matchingDay changed from 1→5 for Saturday test.
- **2026-05-09** — Flow test blocked (initial attempt): ScrapeDo API unreachable from local (connection refused on `api.scrape.do`). getBrandsAndModels → ❌. Reverted Strategy A + matchingDay mods. Fixed by enabling VPN.
- **2026-04-28** — `lang=en` URL parameter dropped by site redirect: `?category=15001&lang=en` → `?category=15001`. Site now served in Greek, breaking all English CSS selectors. ScraperAPI headers (`sd-Accept-Language`, `sd-Cookie: lang=en`) did not override — site still returns Greek. Filip adapted selectors to Greek (PR #10), deployed. First post-fix run: only 20k vehicles prepared (expected 25k+); cause unclear — no obvious pagination error. Additional: same day ScraperAPI only 25-credit option worked; email sent to Onur at ScraperAPI. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1777349596109229)
- 1-credit success 40% → 17-19% (2026-04).
- 10-credit retry almost always works.
- Site switches to Greek — always include `&lang=en`.
- `MS_WEEKLY_LISTING_URLS_TO_FETCH` — Tue start, Mon purge, 2.5h RMQ timeout.
- Biggest listing Opel Corsa, 142 pages.
- `retryHttpRequestsCount=4` to skip 5-credit tier.
- Year format change `'18` → `2018` → SVL cascade (106k queue).
- `rawHorsePower` unit `'bhp'` → `'hp'`.
- Aug 2025 return from hiatus: details URL format changed (`/classifieds/cars/view/44632982-ford-ecosport` vs old `/45979078/?lang=en`) → had to implement legacy/working URL to avoid duplicate vehicles in S3. General rule: when returning a site from pause/hiatus, always verify details URL stability first.
- bodyType filter would make ~48k listings vs 4.5k without → decided to skip bodyType parsing for cost reduction (~200k credits/mo saved).

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

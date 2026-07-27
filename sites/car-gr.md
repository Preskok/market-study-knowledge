# car-gr (GR)

## Current status
🟢 **2026-07-14 RE-ENABLED** — `isDisabled: true` removed (MAR-2104). Root cause of the WAF block was fixed on ScrapeDo's side; no crawler code change was needed for the block itself. Verified end-to-end with `crawler-test-flow` (brands → models → listing → parse → bulk-save → ES) and specifically re-verified `getNextPageUrl()` (see 2026-07-14 below, closes the 2026-05-14 open item) — pagination works correctly. Known open issue: `coverImageUrl` never reaches ES for this site (shared bug across all `skipVisitingDetail: true` sites, tracked in [MAR-2133](https://preskok.atlassian.net/browse/MAR-2133), not car-gr-specific). Separately, the 2026-06-19 MS_TASKS_DL/weekly-queue-empty issue below predates this fix and was not re-checked this session — confirm with Matea whether it's still occurring now that the site is re-enabled.

## Test brand+model
- brand: Mercedes-Benz
- model: CLS 53 AMG
- verified: 2026-05-09
- notes: First alphabetically on car-gr's Greek interface. Strategy A (break-on-first-push) works. matchingDay must be changed to day-of-week offset for today (5 = Saturday 2026-05-09). ScrapeDo required — fails without VPN. SVL check always fails on first local crawl (LocalStack S3 deserialization on NoSuchKey); vehicles fall back to VEHICLE type path with skipVisitingDetail=true, bypassing parseVehicleInput. Weekly queue must be clear before test or car-gr VEHICLE messages get buried.
- **For `--paginate` testing:** CLS 53 AMG only has ~18 listings (1 page) — too low-volume to exercise pagination. Use Mercedes-Benz / A 180 instead (863 listings, 25+ pages) or dynamically pick the brand's highest-count model.

## History & quirks (newest first where known)
- **2026-07-14** — `getNextPageUrl()` re-verified working, closing the 2026-05-14 open item below. Tested against Mercedes-Benz / A 180 (863 listings) instead of the default low-volume test pair: ES showed 25 distinct `VehicleListUrl` values (`pg=2` through `pg=25`, no gaps/repeats), 597 vehicles saved. The pagination selector (`nav div a[class*="c-button"][class*="bg-primary"]` + `.next('a')`) correctly finds the next-page link across many pages — no code change needed for pagination. Also: ScrapeDo's default proxy pool gave `502 ROTATION_FAILED` for car.gr specifically during this session (a control request to an unrelated domain via the same key succeeded) — needed `&super=true` (residential proxies) for manual `curl` reproduction; the actual crawler's own retry logic handled this transparently.
- **2026-07-14 (credit-estimate session)** — Separately found: manual ScrapeDo `curl` calls to `?category=15000&make=X` (the exact param order used in `CarGr.service.ts`) got `502 ROTATION_FAILED` at every tier (REGULAR through SUPER_BROWSER), for 10+ minutes straight, across multiple different brand IDs. Reordering to `?make=X&category=15000` succeeded immediately at REGULAR (1cr nominal, 10cr actual per `scrape.do-request-cost`). Same finding for the `/used-cars/<brand>.html?category=...&make=...&model=...` listing endpoint. Root cause unconfirmed (ScrapeDo-side request fingerprinting/caching keyed on param order? transient rotation-pool issue?) — noting as a reproducible manual-testing gotcha, not a proven crawler bug, since the actual code (`category=` before `make=`) is confirmed working in production via the same-day flow test above.
- **2026-06-19** — 1 message in MS_TASKS_DL. Weekly queue received no messages email alert. Matea investigating. Site is low priority. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1781508175413899)
- **2026-06-08** — Even ScrapeDo 25cr mostly not working (was workaround before). Filip noted even 25 credits often don't work; suggested pinging ScrapeDo team. Low priority, grooming discussion planned. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
- **2026-06-02** — 502 on all retries for `car.gr/classifieds/cars/search/?category=15001`. Not a priority site. ScrapeDo 25cr requests work as workaround. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780304827309509)
- **2026-05-14** — `getNextPageUrl()` fix still pending. Matea opened ticket from Filip's post from the prior week. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1778485086288569)
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

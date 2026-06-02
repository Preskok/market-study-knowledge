# Failure Patterns — Market Study Crawlers

40 concrete patterns from team history. Match evidence against one of these before proposing a fix.

---

## Parsing / HTML / JSON

### 1. `cheerio.load() expects a string`
**Signal:** MS_DL flood from one site. Log says `$.load()` got undefined. Error inside `isResponseNotFound()` / `parseVehicleInput()` escapes retry loop.
**Fix:** `const html = await this.fetchRequest(url) ?? '';` OR `$.load(response)(...)` instead of `$(response).find(...)`.
**Seen:** pazar3, polovni-automobili, subito, mobile-bg, njuskalo, mobile, gebrauchtwagen

### 2. Fake 200 (Incapsula/Cloudflare body with OK status, or scrape.do cross-user leak)
**Signal:** Status 200, body is iframe/challenge — OR — body is valid JSON/HTML from a completely unrelated site (scrape.do proxy served another user's cached response). Retry doesn't trigger. Body may start with `{` (JSON), causing `$(html).find(selector)` to throw `Error: Empty sub-selector` (cheerio treats non-`<` body as CSS selector).
**Fix:** Content-based retry (length threshold, missing expected tags). Delete poisoned S3 key — key date uses server CEST time, so use NEXT day prefix after 22:00 UTC.
**Seen:** ouestfrance-auto (Incapsula), otomoto (truncated), car-gr (scrape.do short body), autoscout-ch (scrape.do returned Spanish billing API JSON for pagination page, 2026-05-14)

### 3. 200 OK with empty body (auto-zeilinger pattern)
**Signal:** `Cannot read properties of undefined (reading 'cars')`. Status 200 but body has no expected key. Gets cached in S3 → auto-retry at 8 AM serves the empty response from cache.
**Fix:** Extend `isServerError()` to detect empty-body 200 — prevents cache save.

### 4. JSON parse errors
**Examples:** promo-neuve `}` inside string (site typo); ouestfrance-auto Incapsula body; autoscout-ch format variants; otomoto truncated responses.
**Fix:** Defensive try/catch. Sanitize. Account for quote-wrapped `{`/`}`.

### 5. HTML selector broke (site redesign)
**Signal:** "Prepared listingUrl messages 0 for site" (no error) OR `Exception in iterateThroughVehicleListPages`.
**Examples:** subito (multiple), otomoto (quoted selector, `.siblings('p')`), flexicar bodytype, autoscout-ch, mobile-bg, njuskalo, auto-schiess `engineSize`→`cylinderCapacity`.
**Fix:** Ask user for live HTML. Update minimal `find()`. Check similar crawlers.

### 6. SVL mass-fail from listing HTML restructure
**Signal:** 70%+ of vehicles fail to save; S3 writes 300% higher (re-saving all). Critical — drives AWS costs.
**Example:** autoscout 2025-02-21 — brand/model moved into child elements → `name` null for 2M vehicles.
**Fix:** Minimal hotfix — drop parsing of broken field from listings; re-add later in proper refactor. Lock deactivation first.

---

## Anti-bot / Blocks

### 7. 403 wall (Akamai/Cloudflare/DataDome/Incapsula)
**Signal:** 403s run. Works in browser, not crawler. Headers: `AkamaiGHost`, `cf-ray`, `DataDome`, `Incapsula`.
**Diagnostic:** curl/Postman, VPN tests, cookies (`ak_bmsc`, `datadome`, `cf_clearance`).
**Escalation:**
1. Cookie hardcode (temp)
2. Browser requests
3. Proxy (mobile 900X or country-specific)
4. scrape.do / ScraperAPI higher tiers
5. Contact scrape.do support (allowlisted hasznalt-auto, car-gr)
6. Hardcoded fallback brands
7. Alternative endpoint (mobile API unprotected)
**Seen:** mobile, pazar3, promo-neuve, auto-connect, avto-net, car-gr, leboncoin, autoplius

### 8. Fake 404 on listings
**Signal:** 404 on listing URLs that open in browser. Default code treats as "gone" and stops paginating → huge vehicle loss.
**Example:** hasznalt-auto — listings return 404, real-missing details return 410.
**Fix:** Add to `isResponseRateLimited()` so they're retried instead of treated as not-found.

### 9. Fake 410 / fake 405 / fake 503
**Examples:** hasznalt-auto 410 on valid details; eurostocks 405 on GET endpoint; gebrauchtwagen fake 503 (MAR-1757).
**Fix:** Same as fake 404 — custom override to retry.

### 10. UNABLE_TO_VERIFY_LEAF_SIGNATURE via proxy+axios
**Signal:** Cert error appears on retries WITH proxy but not direct. Setting `rejectUnauthorized=false` switches to `ERR_CANCELED`.
**Seen:** auto-selection, auto-ici, club-auto, auto-elite.
**Fix:** Remove safeguard from `getBrandsAndModels()` so auto-rerun triggers (manual rerun usually solves).

### 11. CERT_HAS_EXPIRED (site-side cert)
**Examples:** vo3000, activ-automobiles. Site-side.
**Fix:** Wait for owner to fix.

### 12. 429 rate limit
**Fix:** Delays, lower parallelism, proxy.

### 13. Per-brand/model "all-or-nothing" loss
**Signal:** 20-30% vehicle drop with no single error. Popular brand's `getBrandsAndModels()` retries all failed → lost all listings for that brand.
**Example:** njuskalo.
**Fix:** Reset `retryNr` for subsequent pages when first-page retried.

### 14. Timeout as block-indicator
**Signal:** Specific filter combo consistently times out.
**Example:** auto-ici `vehicletype_id=4` (SUV) always times out.
**Fix:** Increase axios `timeout` to 45s; investigate per-filter block.

---

## URL / Endpoint Changes

### 15. Site URL / domain / endpoint changed
**Signal:** 404/302/308 on previously-working URLs. 0 vehicles, no error.
**Examples:** bob-automobile → meinfahrzeug.shop; auto-selection restructured (IDs lost); brie-des-nations new subdomain; autoscout GraphQL moved; otomoto URL format; oxylio encoded titles; ouestfrance-auto → zoomcar.fr; grand-nord-auto → dexauto.fr; gebrauchtwagen → autoscout24 backend.
**Fix:** Update `baseUrl`. Keep `legacyUrl` stable. Follow [Working URL fix](https://preskok.atlassian.net/wiki/spaces/M/pages/3002302476/Working+URL+fix). If IDs don't map: duplicates unavoidable.

### 16. URL encoding
**Examples:** polovni-automobili `ka+` → `%2B`; promo-neuve `Lynk & Co` → `%26`; oxylio double-encoded `%2520`; hasznalt-auto `#` in `smart/#1` collapses to all Smart; mobile-bg Cyrillic↔Latin; grand-nord-auto `&amp;` in brand; garage-chambon `(sports Tourer)` parens.
**Fix:** `encodeURIComponent()` on model/title slugs.

### 17. API endpoint renamed (same structure)
**Example:** auto-connect — just rename.
**Fix:** Update URL, no logic change.

### 18. API variable/shape change
**Examples:** otomoto GraphQL moved `filters` out of `searchTerms`; index-hr dealers API shape; auto-connect API endpoint.
**Fix:** Match new shape.

### 19. API pagination limit changed
**Example:** auto-schiess `paginationLimit=9999` → 422 `limit must not be greater than 100`. Lowered to 15.

### 20. Wrong API URL returning more data
**Examples:** autobazar Leapmotor returned ALL 20k (wrong brand); rastetter wrong URL 400-600 dupes/day; autoscout slug duplicates.
**Fix:** Match exact browser URL + ordering. Delete S3 + rerun.

### 21. Null adminId / dynamic ID in URL
**Signal:** URL contains `/null/`. 0 vehicles.
**Example:** bob-automobile `adminId` null → `/api/cardealeradmin/null/cars/...`.
**Fix:** Re-parse live page. Throw explicit error (triggers 6AM auto-rerun). Delete S3 cache.

---

## RMQ / Infrastructure

### 22. RMQ stuck message / infinite loop
**Signal:** Message stuck hours. Same URL retried every 30 min. Purge doesn't remove unacked.
**Example:** promo-neuve Citroen C3 Aircross stuck 38+ hours. `getNextPageUrl()` returned same URL; S3 served same cached response.
**Fix:** Check `getNextPageUrl()` / `isLastPage()`. Delete S3 key. Add safeguard: if next URL equals previous, break.

### 23. MS_BULK_SAVE_DL from many sites (infra blip)
**Signal:** 10+ sites in DL within seconds.
**Cause:** MySQL `ECONNREFUSED`, ES `ECONNRESET` during bulk insert.
**Fix:** `#tt-devops-support`. Redeliver DL. Run `cache-active-vehicles`. No code.

### 24. Instance restart duplicating crawl
**Signal:** Old index count nearly doubled, unique unchanged. `"Response found in S3"` ~20k times. Grafana shows instance death ~00:30.
**Different from** channel restart (within same instance).
**Fix:** None — unique count is correct. Document.

### 25. RMQ channel restart duplicates
**Signal:** `"Sending shuffled"` log appears twice for same queue/day.
**Fix:** None — unique count correct.

### 26. `MS_BULK_DL` dedup messages (not failures)
**Signal:** 1896 `"DUPLICATED ID CASE, DISCARDING MESSAGE"` logs match DL entries.
**Fix:** Not data loss — RMQ dedup. Ignore.

### 27. Proxy port outage
**Example:** `9007` (Stas) down twice (avto-net).
**Fix:** `#tt-devops-support`. AWS parameter store swap (9001/9005). Delete Redis `datadomeService` entry. Deploy.

### 28. Proxy connection instability
**Signal:** `Proxy connection ended before receiving CONNECT response` spiking.
**Cause:** Proxies rotating too fast (every 2 min).
**Fix:** Stas increased rotation interval.

### 29. Static proxy config pitfall
**Signal:** 429 from site, looks like unused proxy.
**Example:** willhaben uses static proxy `$PROXY_URL`. On office VPN it activates automatically, but direct usage needs explicit config.
**Fix:** Verify with `curl -x $PROXY_URL ifconfig.co` and `$PROXY_URL (HTTP)`.

### 30. Downscaling killing scheduled reruns
**Example:** willhaben 8 AM auto-rerun didn't trigger — ECS scaled down right at 8 AM.
**Fix:** Devops side; awareness only.

### 31. Worker process silently killed
**Signal:** No Graylog errors but crawl didn't run.
**Fix:** Check Filebeat + Grafana. Devops for OOM/deploy.

### 32. Queue backlog delays consumption
**Cause:** Large site (otomoto) pushed thousands ahead of yours.
**Fix:** Wait. Don't rerun manually (creates duplicates).

---

## S3 / Cache

### 33. S3 stale response crash-loop
**Signal:** After fix deployed, rerun produces same error. Logs reference specific `cacheKey`.
**Example:** otomoto `20250411/1f3c3e534262e590c248495528c63c84` looped repeatedly.
**Fix:** `AWS_PROFILE=preskok-prod aws s3 rm s3://$AWS_S3_BUCKET_DAILY_CACHE/YYYYMMDD/[hash]`. Deploy `isServerError()` improvement first to prevent re-save.

### 33b. Cloudflare 52x cached as valid → DL alert flood
**Signal:** 3000+ alert emails overnight. `TypeError: X is not iterable` or `TypeError: Cannot read properties of null` on listing consumer. Root S3 response has `statusCode: 52x` and empty body.
**Root cause:** Cloudflare 520–527 (origin-side errors) returned HTTP 200 wrapper from CDN. `isServerError()` only covers 500–507 → 52x gets cached as valid → every consumer reads poisoned cache → TypeError per listing message → MS_DL × N.
**Example:** auto-connect 2026-05-31 — 526 (SSL handshake failed) cached → 3000 DL alerts. Saturday crawl.
**Fix:** Override `isServerError()` in the site service to include 520–527:
```typescript
public isServerError({ response, responseBody }): boolean {
    const statusCode = response?.statusCode;
    const isCloudflareOriginError = statusCode >= 520 && statusCode <= 527;
    return isCloudflareOriginError || super.isServerError({ response, responseBody });
}
```
Also add `listingVehicles ?? []` guard in `getVehicleListPageResponse` as defense-in-depth to stop the TypeError from hitting DL queue even if a bad response slips through.
**Generalizable:** Any CF-proxied site. If S3 body has `"statusCode":52x` and empty body, the site had a Cloudflare origin error that was mis-cached.
**Tags:** `fake-200` `s3` `null-parse` `ms-dl` `cloudflare`

---

## Data / Validation

### 34. Progressive validation spikes
**Signal:** `Big number of validation logs for site(s)` with property breakdown.
**Causes:** Site-side data change; selector fix backfill (`null → value` EXPECTED post-fix); slug change; bug in parsing.
**Fix:** Check direction. Check live site. Usually no fix if site-side.

### 35. Dealer from other country price-unit confusion
**Example:** autobazar dealer davo-car-s-r-o used CZK with EUR symbol → 10x price.
**Fix:** Save final on-ad price only; sanity check if crossed-out much higher than final.

### 36. Counter on site is wrong/fake
**Example:** mobile-bg counter showed 180k but real sum per-model `adverts_counter` was 121k.
**Fix:** No fix — awareness. Don't chase missing vehicles when counter is fake.

### 37. Supplier catalogue inflates buyerstock count
**Examples:** garage-chambon jumped 88→4000; autocenter81 similar.
**Fix:** Product decision — skip supplier-origin vehicles (per Rok/Matjaž).

### 38. Dual-listing "recycled ad"
**Signal:** Looks like SVL fail — vehicle data completely changed.
**Example:** auto-1 — same storeId re-used for different vehicle (Qashqai n-connecta → tekna).
**Fix:** Site-side bug, not ours.

---

## Credits

### 39. ScraperAPI / scrape.do credit spike
**Causes:** Site upgraded anti-bot (leboncoin: only 30-credit works); scrape.do changed allocation (all sites at 10 credits — Nov 2025); bug producing excessive requests; hasznalt-auto currency-conversion 30-day re-visits.
**Fix:** Contact scrape.do support (`tt@preskok.si`). Disable site temp.

### 40. ScraperAPI premium-only failing
**Signal:** ALL premium requests fail + 50% 1-credit fail.
**Example:** hasznalt-auto 2025-03-03.
**Fix:** Domain-specific block that day. Wait.

---

## Other

### 41. Graylog/ES down → false alarm
**Signal:** Email says "no messages"/"no logs" but ES shows normal counts.
**Fix:** Verify ES. Check `#tt-devops-support`. Document.

### 42. Small site normal fluctuation
**Signal:** 20-50% drop on site <500 vehicles, no errors, recovers 1-3 days.
**Sites:** auto-elite, autohaus-listle, rastetter, autobazar, brie-des-nations, cardoen, oxylio, vo3000, glinche-automobiles, eurostocks, schmidt-automobile.

### 43. Follow-redirect tradeoff
**Example:** njuskalo — with followRedirect: 500s; without: 302s that retry. No stable config.

### 44. Puppeteer response.request.path breakage
**Cause:** Axios has `.request.path`, puppeteer uses `.request().url()`.
**Fix:** Use `response.request?.url()`.

### 45. Wrong deploy / branch
**Example:** leboncoin — stage ScrapeDo credit-lock branch accidentally deployed to prod.
**Fix:** Check recent deploys. Verify master.

### 46. Supermodel + model listings duplicate vehicles
**Signal:** Same ad appears on both a supermodel listing (e.g., "C-Class") and its specific model listing (e.g., "C 220"). Daily SVL model-name flip-flop; name/version alternates.
**Examples:** ss-lv (name cuts because of alternating titles), car-gr (supermodel listings → 15k SVL "Vehicle has changed too much"), pazar3 ("other models" listings with all-brand dupes), subito Smart #1, autoscout.
**Fix options:**
1. Skip supermodel listings → lose 20-25% vehicles
2. Parse both but accept SVL flip-flops (document as known-problem)
3. Prefer more-specific model listing when ad appears on both
Pick based on volume tradeoff — document the decision.

### 47. Details URL format changed between crawls (duplicates in S3)
**Signal:** After returning a site from pause/hiatus, details URL format differs from historical. New URLs written to S3 are different keys → duplicates.
**Example:** car-gr Aug 2025 — old `/45979078/?lang=en` → new `/classifieds/cars/view/44632982-ford-ecosport`.
**Fix:** Implement legacyUrl (stable, for S3 key) + workingUrl (current URL to fetch). Always verify details URL stability *before* re-enabling a paused site. In worst case, script to delete "in-between" duplicates from ES+S3.

### 48. Counter filter-specific drop (25-35% loss)
**Signal:** Filtering by a specific facet (bodyType, transmission) drops 25-35% of vehicles, but filter "works" in browser (just silently).
**Examples:** pazar3 (30-35% loss filtering bodyType), car-gr (48k listings w/ bodyType vs 4.5k w/o).
**Diagnosis:** Compare crawl result counts across filtered vs unfiltered run.
**Fix:** Skip the filter — accept lost property (often only cosmetic; mappings can tolerate). Decision needs Gregor.

### 49. Site counter vs actual count mismatch
**Examples:** mobile-bg (180k counter vs 121k real sum), pazar3 (Jeep Compass: 47 counter vs 38 crawled when skipping no-price), autoconnect (site shows 581 Volkswagen, crawler gets ~half).
**Fix:** Check if counter comes from a separate/inaccurate endpoint. Don't investigate "missing vehicles" when counter is known-fake. When deviations are 20-50%, often just counter inflation.

### 50. Vehicles without price
**Signal:** `"Vehicle is missing price"` logs flood.
**Decision tree:**
- Keep for market-representation sites (avto-net, pazar3, reklama5, merrjep) → set `isCrawlingVehiclesWithoutPrice: true` in CrawlingSites; save with `null` price.
- Skip for price-driven sites (pricing reports, etc.).
**Confirm with Gregor** before changing behavior — business rule, not a bug.

### 51. Leasing ads masquerading as price
**Examples:** otomoto monthly leasing rates saved as price; autoplius long-term-rental vehicles (monthly prices); blocket leasing ads without `sales_form=5` indicator.
**Fix:** Detect via margin (e.g. blocket: `DOFR > 5Y AND Price < 2k` → skip), or rely on explicit `sales_form`. Add `isDamaged`-like flag if needed (PR 2283 otomoto pattern).

### 52. Report/cron failed due to log-field bug
**Example:** 2025-07-15 validation report empty because `log.changes` was empty string for "Vehicle is missing price" (same `VALIDATION_PROGRESSIVE` context). Query matched unintended logs.
**Fix:** Add specific `message:"Vehicle has changed too much"` filter to report query. Use an enum (`LoggingMessagesForReports`) shared between log creation and query to prevent drift. Also fix count mismatches (count vehicles with changes, not count of all prop fields).

### 53. Emoji in title/description → BULK_SAVE_DL
**Signal:** Vehicle saved to Old index but missing from Data index. `jsondiffpatch` can't calculate history with emojis → S3 save fails → not saved to Data index.
**Example:** subito, finn (MAR-1960).
**Fix:** Sanitize emojis before jsondiffpatch call. Saving to Old index is independent of S3, which is why Old index still has the vehicle.

### 54. Local dev: MS_BROWSER_CRAWLERS queue has no binding
**Signal:** Locally browser-queue messages land in `MS_CATCHALL`. Site not crawled.
**Fix:** In devenv RMQ dashboard, manually add binding `exchange: ex_marketstudy, routing key: crawl.browser_crawlers.#`. Or re-run `Import definitions preskok`. Known issue: `import definitions` sometimes misses this binding.

### 55. Drift detection per-site via DataAPI
**Purpose:** Alert when mapping confidence drifts site-wide, not per-vehicle.
**Setup:** Add `?save_as_reference_metrics=true` to DataAPI stage URL (Uros Grandovec owns). Persists current-site baseline for future comparisons.

### 56. URL special chars cause infinite page recursion
**Signal:** A single listing message consumes 1000+ ScraperAPI credits and retries hit RMQ consumer timeout 5 times (~150 min). `nextPageUrl` in logs has hundreds of repeated `/page2` segments.
**Example:** hasznalt-auto `smart #1`, `honda e:ny1` — the `#` and `:` chars break URL parser used to build pagination URL, so each page appends `/page2` instead of replacing it.
**Fix:** Dedup `/page2` segments in `nextPageUrl` (or URL-encode the problem fragment). Saves ~10-20k ScraperAPI credits/month.
**Detection at code-review time:** Any site with model names containing `#`, `:`, `&`, `+`, `%` should have `encodeURIComponent` or equivalent in its URL-builder.

### 57. Fuel type flips between crawls (hybrid ads)
**Signal:** SVL fails ~2/3 of site; fuelType oscillates `hybrid` ↔ `gasoline` ↔ `electric` on same vehicle across minutes.
**Example:** bob-automobile, autohaus-landherr (same codebase family) — mild/full hybrid ads on details page cycle labels.
**Fix:** Use LISTING-page fuelType only; don't re-read on details visit. Accept listing label even if slightly less specific.

### 58. API page limit truncates crawl
**Signal:** Site shows N vehicles but crawler always reaches exactly round numbers (1000, 2000, 5000) — never beyond.
**Example:** star-terre (1000 of 2500 vehicles; 50-page API cap); leboncoin per-filter cap drove initial crumbler design; car-gr 142-page limit.
**Fix:** Refactor `getBrandsAndModels()` to split by brand so no single query hits the cap. Big brands sometimes need model-level splits or crumbler.

### 59. Auth token in Redis (not S3) — testing gotcha
**Signal:** You fixed auth regex locally but can't see the new code path execute. No "fetch auth" log appears.
**Example:** eurostocks (`useS3Cache: false` on auth because user-agent must stay in sync with xPlatformToken).
**Fix:** Delete the Redis key (Another Redis Desktop Manager). Next request refetches auth fresh. Add a TTL in Redis if safe, otherwise document the key name in site specifics.

### 60. Validation action "skip saving vehicle" blocks deactivation
**Signal:** Vehicles missing from Data index entirely, not just missing `activeTo`. Old index still has them.
**Root cause:** Numeric validation runs at deactivation too (data field validation happens BEFORE Data-index write). If value falls outside margin for fields with "skip saving vehicle" action (price, nettoPrice, discount, horsePower), vehicle is skipped — so `activeTo` never gets set.
**Fix:** For deactivation path, either soften validation (reassign null) or always persist the `activeTo` even if other fields fail. Known since Jan 2025 — must be fixed before any full remap to avoid baking errors into rebuilt index.

### 61. Deactivated→reactivated triggers validation log without real change
**Signal:** `numberDoors` (or similar) shows in validation log even though you fixed parsing yesterday.
**Root cause:** Vehicle was deactivated (with old value in S3), today's listing crawl marked it active again, no SVL triggered (listing data matches S3), but insert to Data index re-runs validation → triggers log.
**Fix:** Don't treat this as a regression. Check S3 vs. Old-index timestamps; if vehicle was previously deactivated, the log is cosmetic (subito `numberDoors` 45/23 Jan 2025 pattern).

### 62. Same queue, simultaneous block = proxy/queue issue, not per-site
**Signal:** Multiple sites on the same RMQ queue all return 403 same day; individually each site has distinct anti-bot (CloudFlare vs CloudFront vs DataDome).
**Example:** Feb 2025 — otomoto (CloudFront) + olx-ro (CloudFlare) both 403 same day; shared `MS_LIMITED_CONSUMERS_LISTING_URLS_TO_FETCH`. blocket on same queue was fine.
**Fix:** First check proxy health (`#tt-devops-support`), then consumer count, then per-site. Don't start with "site changed anti-bot" — correlation is the signal.

### 63. Whitelisted IP de-whitelisted
**Signal:** All requests from AWS IP get 403 Forbidden. Curl from local IP gets 400 (different response = possibly also API change).
**Example:** willhaben IP `3.75.69.226` revoked Mar 2025.
**Fix:** Contact Jan Mrhar (business contact) — site-side whitelist, not our fix. Note the revocation date for future audits (partners sometimes rotate allowlists quarterly).

### 64. Negative discount from catalog-vs-seller mismatch
**Signal:** `"Something went wrong with discounted price calculation"` log; discount < 0.
**Root cause:** Site's API returns BOTH `manufacturerPrice` (catalog) and `sellerPrice`. Seller can price ABOVE catalog for limited/custom configs → discount = negative.
**Examples:** star-terre (`prixConstructeur` < `prixClient`), brie-des-nations (normal), biltorvet.
**Fix (interim):** Save only `price` (seller), skip discount. Await broader catalog-price product decision. Flag-based: e.g. star-terre `virtuel: 0` = real visible discount, `virtuel: 1` = hidden (ignore).

### 65. Deactivation + insertion concurrency → DL spam
**Signal:** Many MS_BULK_DL entries during or right after deactivation window (22:00-midnight). Volume doesn't match real crawl failures.
**Root cause:** Delete/deactivate + insert happen concurrently → ES version conflicts / lock contention on same docs → DL.
**Fix:** Serialize: pause inserts during active deactivation of a given site (application-level lock). Marko documented this Nov 2024. Still on follow-up list.

### 66. Details URL generation fails → vehicle saved without URL
**Signal:** "Missing all vehicles today" email for a site, but crawl actually ran. Old index has entries but with `url: null` or same URL across multiple docs.
**Example:** gruppo-piccirillo (since 2024-11-25) — `buildId` gone, legacy API returns double-slash in `//filtri/` path, details URL generation fails; vehicles land in Old index without URL, dedup-by-URL count for alert = 0.
**Fix:** Full crawler refactor. Interim: suppress alert for the site until fixed (with ticket linked).
**Symptom check:** `SELECT count(*), count(DISTINCT url) FROM vehicles WHERE site = 'x' AND date = today` — if `count(DISTINCT url) = 0` or `= 1`, this is the pattern.

### 67. Scale-up side effect on other queues (browser crawlers)
**Signal:** Enabling one site via browser requests causes drops/delays on unrelated sites; CPU/RAM goes up on AMS.
**Example:** Oct 2024 hasznalt-auto (browser) added → autoscout finished 2h later than usual, lacentrale 3-day crawl dropped. Browser workers are heavier than axios workers.
**Fix:** Move the browser-heavy site to dedicated queue `MS_BROWSER_CRAWLERS_LISTING_URLS_TO_FETCH` (Matea added Oct 14 2024). Monitor overall CPU before enabling a new browser site. Warn team before enabling a new heavy site.

### 68. Dealer branch dedup needs more than city
**Signal:** `"Partial dealer does not match with full dealer in S3 mapping!"` log flood; dealer records multiply or collide.
**Root cause:** `dealerId` built from site + brand + city. Multi-branch dealers in one city get same `dealerId` → mapping collision.
**Example:** biltorvet (multiple branches same city), willhaben (Linz 4020 vs 4040).
**Fix:** Include ZIP code (or full address) in `branchName` for those sites. ZIP is simpler, address more robust. Avoid purely name-based differentiation (dealer names often identical across branches).

### 69. Model naming with space vs no-space
**Signal:** CIS/AMS matching produces 0 results or wrong results; same model name with different spacing appears in different pipelines.
**Example:** DS 7 (`Ds 7`) vs `Ds7` on buyer-stock turnover — AMS didn't yet use data-mapped vehicles for this endpoint, so raw names leaked.
**Fix:** Consumer side: pass BOTH variants as filter (`model[]=Ds7&model[]=Ds 7`). Long-term: use data-mapped name consistently everywhere.

### 70. Duplicated field parsing (HTML duplication bug on site)
**Signal:** A single field parsed as doubled value: `"KasseKasse"`, `"DealerName DealerName"`, etc.
**Root cause:** Site's HTML renders the same field twice (frontend bug on their side, not ours).
**Examples:** finn body type `KasseKasse`; avto-net dealer name doubled (some source delivers it twice).
**Fix:** `getTextWithoutChildren()` collapses the DOM text; for single-value fields, parse only first occurrence. Add targeted assertion to detect the doubling pattern (string = concat of itself).

### 71. Backend API migrated domain
**Signal:** Sudden 404s on API endpoint requests, crawler still gets HTML fine.
**Example:** olx-ba Oct 2024: `olx.ba/api/categories/18/brands` → `api.olx.ba/categories/18/brands`.
**Fix:** Update API baseUrl in site specifics. Sometimes documented in site's API response headers or robots.txt; sometimes has to be traced via browser network tab.

### 73. ES CPU 100% causes DL queue spike (bulk timeout cascade)
**Signal:** DL queue 3× normal size. Logs show `"Request timed out"` on msearch operations. Mostly between 22:00–02:00 and 08:00–09:00.
**Root cause:** If the same RMQ bulk message times out twice, it goes to DL. New-search index msearch (800-doc batches) taking 22-25s on prod (vs 200ms local) when ES CPU is at 100%. Rollover index growth, DCM access, or other projects hitting the same cluster.
**Fix:** Check ES CPU in Grafana/Kibana. If 100%: (1) lower msearch prefetch, (2) scale up ES cluster (ask Stas), (3) investigate other consumers (DCM, CustomElasticAdapter). After ES stabilises, redeliver DL messages. Consider indexing schedule (22:00 peak = deactivation jobs + crawl overlap).
**Reference:** July 2024 incident. Data on new-search index: 1500 msearch timeouts in 8 days. Stage msearch: 800 docs = 1.5s, prod = 22-25s.

### 74. numberDoors / numberSeats slash format (e.g. `5/7`)
**Signal:** ES has `numberDoors: 57` or `numberSeats: 57` (two digits concatenated). Or massive numbers like `25000`.
**Root cause:** Site displays `5/7` meaning "5 or 7". Simple parseInt reads it as `57`. Sites like subito, mobile.de affected.
**Rule (Gregor 2024):** Take **higher** number for BOTH numberDoors and numberSeats when format is `A/B`. Numbers > 20 for doors or > 25 for seats → data validator sets to null (don't handle in crawler, validator catches it). Concatenated number (e.g. `57` displayed as single number without `/`) → also null via validator, no crawler fix needed.
**Helper:** New methods `parseNumberDoors()` / `parseNumberSeats()` handle the slash; legacy methods deprecated. Subito was main offender.

### 75. "Buy" / "changing" indicator on classifieds sites (ss-lv pattern)
**Signal:** Vehicles saved with no price, or appearing in wrong brand category (e.g. Nissan in BMW listing).
**Root cause:** Some classifieds let users post "want to buy" ads (`rawPrice = "buy"`) or exchange listings (`"changing"` indicator). These appear mixed into normal listings.
**Rule:** Skip `rawPrice === "buy"`. Skip "changing" (for-exchange) listings. Save vehicles without price if they're genuine sale listings (Gregor decision).

### 76. SVL disabled for one day to back-fill mass null field
**Signal:** Mass PVL ("Validation logs" spike to 34%+) for a field that was newly added to parser or was null for all vehicles.
**Root cause:** blocket driveTrain was null for 86k vehicles. Details weren't revisited (SVL passed with null). New field being parsed triggers a mass "null → value" SVL failure.
**Fix:** Temporarily disable SVL for the affected site for 1 day. All vehicles visit details, null fields get populated. Re-enable SVL. Confirm via Graylog next day. Coordinate with Marko (only infra can merge SVL-toggle deploy).

### 77. Site switches HTML structure mid-day (lacentrale pattern)
**Signal:** Critical selector fails, 0 vehicles or all details missing. No code change on our side.
**Root cause:** Site deploys new frontend while we're mid-crawl. Old cached S3 responses still work, but new page visits use new HTML → selector fails.
**Examples:** lacentrale June 28 2024 (all traffic), lacentrale July 30 2024 (selector change). Hotfix required within hours.
**Fix:** Check browser DevTools for current selector. Deploy hotfix to develop (not master). If mid-day and prod affected, trigger emergency deploy.

### 78. Axios SSL cert verification failure (auto-selection pattern)
**Signal:** `"Prepared 0"` for site. Logs show SSL/cert error (CERT_UNTRUSTED, UNABLE_TO_VERIFY_LEAF_SIGNATURE, etc.) on homepage/listing fetch.
**Root cause:** Site has misconfigured or self-signed SSL cert. Axios rejects it by default.
**Fix:** Add per-request `httpsAgent: new https.Agent({ rejectUnauthorized: false })`. Global `fetchRequestOptions.httpsAgent` does NOT propagate to all fetch calls — must be set explicitly per request. If site resolves SSL issue → remove the override.

### 79. AHM href URL double-concatenation
**Signal:** Detail URLs look like `https://ahm.gmbhhttps://ahm.gmbh/Autohaus-...`. 0 vehicles fetched from AHM.
**Root cause:** Site alternates between full absolute href and relative href. When site serves absolute href, crawler prepends baseUrl → double URL.
**Fix:** `if (!href.startsWith('http')) { href = baseUrl + href; }` pattern — only prepend if href is relative. See AHM service for reference.

### 80. General crawl task executed twice (instance killed mid-task)
**Signal:** Multiple sites (subito, auto-selection, bob-automobile) all spike DL or vehicle counts simultaneously. Graylog shows two `request_id` variants for the same general task.
**Root cause:** Main instance killed at bad moment while processing MS_TASKS queue. Task is NACKed, requeued, another instance picks it up → all crawlers in general queue run again.
**Fix:** This is inherent to RMQ at-least-once delivery. If detected live: check if queue is still draining, don't rerun manually. Monitor DL for duplicate-id errors (expected for duplicated messages). No code fix needed — just awareness.

### 81. MySQL full → proxy and SVL stall
**Signal:** All proxy-dependent crawlers fail silently. SVL pages stuck waiting. Email: "AMS production compromised due to a full MySQL database."
**Root cause:** MySQL `active_vehicles` table not updated (disk full). Proxy rotation also depends on MySQL → no working proxies. shouldValidateListing pages wait for DB confirmation and stall.
**Fix:** (1) Contact Stas to expand MySQL disk. (2) Lock vehicle archiving for 1 day. (3) After MySQL restored, run `cache-active-vehicles` to sync ES → MySQL. (4) Redeliver any DL messages from the failure window.
**Reference:** June 2024. Confluence page: `/spaces/M/pages/3079438339/MySQL+down+Full+storage`

### 72. Suppress false forbidden detection on S3 reads
**Signal:** Request succeeded on first crawl (not forbidden), but rerun reads from S3 and marks response as forbidden.
**Root cause:** `isResponseRateLimited()` runs on the cached responseBody, not on original HTTP status; body-text match can change meaning after reading from cache (e.g. encoding artifact).
**Fix:** Ensure the check runs on actual response content with same parser as first visit. Prefer status-code-based detection where possible; if body-text based, sanity-check the response body is identical to what we wrote to S3.

### 82. Multi-currency SVL false fail (ooyyo / aggregator pattern)
**Signal:** Mass SVL failures for a multi-country site. All vehicles from a given country fail on the same day. No actual price change on site.
**Root cause:** Exchange rates update every ~2 days. If SVL compares converted EUR prices (default), any exchange rate shift looks like a price change → entire country's vehicles fail SVL.
**Fix:** Compare in original currency for SVL (save `originalCurrencyPrice` + `originalCurrency`). Only convert to EUR for display/storage, not for SVL comparison. Gregor decision: "compare original currency so exchange rate changes don't trigger SVL." Applies to any site that lists vehicles in non-EUR currencies (ooyyo, multi-country aggregators).

### 83. False "N MORE vehicles" alert from old-index alias gap
**Signal:** Morning alert says "ALL sites have N MORE vehicles than yesterday." No actual vehicle surge occurred. Happens right after index rollover.
**Root cause:** When only today's new index has the alias (alias transition window), yesterday's count query returns 0 (querying old index that no longer has alias) → delta = today's count − 0 = huge apparent increase. Every site shows "N MORE".
**Fix:** If the alert fires for ALL sites simultaneously at rollover time, it's a false alarm. Verify: check ES index aliases with `GET /_cat/aliases`. If the alias just moved, ignore the alert. No code fix needed — just operator awareness.

### 84. RMQ "Blocked/Unblocked connection" log (not a crawler issue)
**Signal:** Graylog shows `"Blocked connection"` / `"Unblocked connection"` messages from RMQ. May coincide with crawl slowdowns but not always.
**Root cause:** RMQ memory or disk watermark exceeded → RabbitMQ blocks publisher connections. This is RMQ-internal, not a crawler code issue.
**Fix:** Check RMQ memory/disk in RMQ management UI or Grafana. If memory: ask Stas to investigate RMQ resource limits. If disk: check if logs or data dir is filling up. Crawling resumes automatically when watermark clears. Inform Stas if it persists.

### 85. Worker process hangs on extremely long string (regex catastrophic backtracking)
**Signal:** RMQ queues show 0 consumers. Worker process appears "running" in Grafana (ECS task alive) but health check endpoint `/api/v1/health-check/check` stops responding → AWS ECS marks instance unhealthy → autoscaling triggers → new instance picks up same bad RMQ message → same hang → 100+ failed redeploys overnight → 0 consumers for hours → thousands of vehicles uncrawled.
**Root cause:** A single RMQ message contains a vehicle with an extremely long string in title, equipment list, or description. A regex applied to this string catastrophically backtracks (exponential time) → JS event loop blocked → no I/O → health check never responds. The bad message is re-delivered to each new instance, creating an infinite restart loop.
**Fix immediate:**
1. Move all messages from the affected queue to a temporary queue (Stas does this via shovel).
2. Restart the worker — it starts fresh with no messages, consumers come back.
3. Find the offending message: check Graylog for the last `"LISTING_URL started"` or `"DETAIL_URL started"` log before the hang — that's the bad vehicle.
4. Delete or patch the bad vehicle's S3 cached response.
5. Shovel messages back from tmp queue; monitor carefully.
**Fix permanent:** Crop all text fields to a max length (e.g. 5000 chars) BEFORE regex operations. Related ticket: MAR-1379 ("process must die, not hang, when something goes wrong").
**Seen:** eurostocks, Oct 6 2023 — one Jaguar listing with extremely long title/equipment caused full outage (~4M vehicles not crawled that night).

### 86. VPN/proxy provider outage → 2/3 daily data loss
**Signal:** Multiple sites simultaneously drop to 0 vehicles. No site-specific error pattern — ALL proxied sites fail at once. Graylog: connection refused / auth failure on proxy requests.
**Root cause:** The VPN/proxy provider (HMA, NordVPN, or mobile proxy) has infrastructure issues. All proxied requests fail. Non-proxied sites (if any) continue normally.
**Fix:**
1. Stas checks proxy provider status dashboard (HMA, NordVPN, or mobile proxy admin). If provider reports incident: wait; if no incident: restart proxy service.
2. If provider is down for hours: Stas evaluates switching to backup provider or port.
3. Announce in channel: "Using proxies X" when switching back.
4. After proxy switch back, check njuskalo especially — ShieldSquare is sensitive to proxy IP changes and may block for several hours after IP rotation.
**History:** HMA outage Jan 24-25 2023 (auth failure all endpoints, 2/3 data lost). NordVPN all-down Jun 26 2023 (48-reply thread). Mobile proxy port 9007 down multiple times.

### 87. ms-bulksave misconfigured to too many instances → ES 100% CPU
**Signal:** ES CPU hits 100% for 1-2 hours. Graylog: "Request timed out" on msearch operations. MS_BULK_DL floods with ES timeout errors. ms-bulksave shows unexpectedly high instance count in Grafana (e.g. 10 instead of 2).
**Root cause:** Auto-scaling misconfiguration or a ticket description error caused ms-bulksave to scale to 10 instances instead of the normal 2. 10 bulk consumers overwhelm ES with concurrent writes, especially around `msearch` (which-index-has-this-document check).
**Normal configuration:** ms-bulksave scales up to **2 instances** when bulk queues exceed 300k messages; down to 1 at 100k.
**Fix immediate:** Stas adjusts ECS service desired count back to 2. ES recovers automatically within minutes.
**Data impact:** Vehicles saved to S3 successfully (S3 consumer unaffected). New search ES index misses ~1M vehicles. They auto-recover next day via S3→ES backfill during index rebuild. No need to redeliver DL messages if gap is acceptable.

### 88. `getNextPageUrl()` returns same URL → infinite loop (unacked, immune to purge)
**Signal:** A single listing task runs for hours. Queue shows 1 message "unacked" all day. Graylog: same listing URL restarts every 30 min. S3 logs show 125k+ cache reads for the same domain. Crawl doesn't finish; eventually runs past midnight.
**Root cause:** `getNextPageUrl()` implementation returns the current page URL unchanged (usually a bug in detecting the "next page" URL — e.g. picking a relative link that resolves back to the same page). The listing fetches page → parses vehicles → calls `getNextPageUrl()` → gets same URL → fetches again from S3 cache (same key) → loop. The RMQ message is "unacked" (being actively processed), so queue purge does NOT remove it. The 30-min `x-consumer-timeout` fires → message redelivered → immediately re-enters same loop.
**Why it stops:** S3 7-day per-day cache expires at midnight. After expiry, the first live request gets a fresh response with a properly parsed next-page URL, breaking the loop. OR: consumer restart with the queue empty causes natural resolution.
**How to tell it's a loop (not a slow crawl):** Check Graylog for "Response found in S3" on the same URL repeating. Count of S3 reads will be in the thousands. Real slow crawls don't S3-hit the same URL 100k times.
**Fix immediate:**
1. Identify the stuck listing URL from Graylog.
2. Delete the S3 cached response: `aws s3 rm s3://$AWS_S3_BUCKET_DAILY_CACHE/[YYYYMMDD]/[md5-hash]`.
3. Purge the queue (removes unacked only if consumer restarts — usually must restart consumer too).
4. OR wait for S3 cache natural expiry at midnight (risky if crawl window is tight).
**Fix permanent:** Detect same-URL repeat in `getNextPageUrl()`: if returned URL equals current URL, throw or return null. Add a circuit breaker counting how many times the same URL has been fetched in one listing run.
**Seen:** promo-neuve, March 28 2025 — `getNextPageUrl()` stuck on page 1 for 38 RMQ cycles (~19 hours), 125k+ S3 reads.

### 89. Removed site in code but ES/reporting still references it → adSiteConfig crash
**Signal:** A reporting job, alert script, or dashboard that iterates all sites starts failing with "cannot read property of undefined" or "adSiteConfig not found for site X". Site X was recently removed from `CrawlingSites.ts` or the site config, but its vehicles still exist in ES.
**Root cause:** ES Data index still has vehicles with `site: "bynco"` (or whichever removed site). Reporting code that reads ES results and looks up site config by key fails because the config key no longer exists. The vehicles in ES are not cleaned up when a site is disabled in code.
**Fix:**
1. Add a null/undefined guard in reporting code: `if (!adSiteConfig) continue;` (or equivalent).
2. OR deactivate all ES vehicles for the removed site before removing from code (preferred but time-consuming).
3. Add removed site to a `DISABLED_SITES` constant that reporting code tolerates.
**Prevention:** When removing a site, check if any reporting or alert script iterates ES results by site key without a guard. Add a comment: `// bynco removed Jul 2025 — keep guard until ES vehicles expire`.
**Seen:** bynco removed Jul 2025 — site posted disclaimer "no longer selling via platform", 0 vehicles → site removed from code → adSiteConfig lookup crash in report.

### 90. ScraperAPI sudden credit jump across ALL sites
**Signal:** ScraperAPI credit dashboard shows dramatic spike on a specific date. All sites that use ScraperAPI see 10 credits/request instead of their expected tier. No change was made to crawler config. Credit consumption multiplies overnight.
**Root cause:** ScraperAPI changed their billing model or applied a new policy. The Nov 5 2025 incident: all requests suddenly billed at 10 credits regardless of tier previously used. No warning email. Support acknowledged the change.
**Fix:** Contact ScraperAPI support immediately with the billing date and site examples. Ask for clarification on the new billing structure and whether historical rates can be restored for existing accounts. In the short term, consider disabling low-priority ScraperAPI sites (ScraperAPI used for: leboncoin, hasznalt-auto) to avoid credit exhaustion.
**Note:** Monthly credit check is on the 24th — but a sudden billing change like this will exhaust budget before the next check. Check credit balance in first 2-3 days after any unusual crawl-failure pattern across ScraperAPI sites.
**Seen:** Nov 5 2025 — all ScraperAPI sites suddenly 10cr/request. Team contacted support.

### 91. jsondiffpatch "URI malformed" → S3 history calculation error
**Signal:** `MS_BULK_SAVE_RAW_VEHICLES` dead-letter queue receives messages with error "URI malformed" from jsondiffpatch. Vehicles are still saved to S3, but the change-history delta calculation fails. No visible impact to vehicle counts.
**Root cause:** jsondiffpatch internally uses `decodeURIComponent()` when generating string diffs. If the vehicle data contains a malformed URI sequence (e.g. a stray `%` in a description or URL field), this throws. The error surfaces in the bulk-save raw-vehicles consumer when trying to compute the diff between old and new vehicle state.
**Fix:** Sanitize vehicle string fields before passing to jsondiffpatch. Either strip/encode `%` sequences in description/title/url fields, or wrap the diff call in try/catch and log the error rather than DL-ing the message.
**Seen:** Recurrently in `MS_BULK_SAVE_RAW_VEHICLES` DL. Documented Dec 2024 by Marko.
**Seen:** July 11 2023 — Stas changed scaling threshold from 300k→200k messages and accidentally set target to 10 (Marko's mistake in ticket description).

### 92. DataDome cookie persistence broken on 403 (Subito MAR-2039)
**Signal:** `proxy has no cookies in Redis` log fires hundreds-of-thousands of times per day even though DataDome recovery is being attempted. Successful recoveries logged (`DataDome recovery succeeded`) but next request on the same proxy still cold-starts. Vehicle count steadily drops as proxy reputation degrades.
**Root cause:** `afterRequest` in `Subito.service.ts` was passing the original `ex` to `dataDomeService.updateProxyAfterRequest` — when `ex` was non-null (the request failed before recovery), it triggered the error branch in `updateProxyAfterRequest` which never persisted cookies. Even when the recovery flow successfully obtained a fresh DataDome cookie via Set-Cookie, that cookie was never saved to Redis, so the next request on that proxy hit a cold start again.
**Fix:** After `trySolveDataDome`, check if the cookieJar has a `datadome` cookie even when the result is still failed. If yes, override `exForRedis=null` and `responseForRedis={statusCode:200}` before calling `updateProxyAfterRequest` — forces the save branch.
```typescript
if (isResultFailed && options.cookieJar) {
    const freshCookies = await CookieHelper.getDevtoolsProtocolCookiesFromCookieJar(options.cookieJar);
    if (this.dataDomeService.hasDataDomeCookie(freshCookies)) {
        exForRedis = null;
        responseForRedis = { statusCode: 200 } as RequestResponseData<T>;
    }
}
```
**Seen:** Subito 2026-04-30 deploy. Fix in `bugfix/MAR-2039-subito-datadome-cookie`.
**Generalizable:** Any DataDome-protected site that uses `dataDomeService.updateProxyAfterRequest` should verify cookies acquired during recovery are actually persisted on the failure path.

### 93. Subito chunk URL bypassing DataDome proxy flow
**Signal:** `getMappedBrandsAndModels` fails intermittently with 403 on `_next/static/chunks/*.js` fetches. When Graylog is checked, those chunk fetches show `useProxy: false` instead of `useProxy: true`.
**Root cause:** Two bugs in the chunk fetch line:
1. URL constructed as `${this.baseUrl}/${scriptUrlPath}` but `scriptUrlPath` already starts with `/` → produces `https://www.subito.it//_next/...` (double slash)
2. Call signature was `await this.fetchRequest(url)` with no second argument → uses the default options which have `useProxy: false` → plain axios with no DataDome cookie
**Fix:**
```typescript
const scriptContent = await this.fetchRequest(
  `${this.baseUrl}${scriptUrlPath}`,
  { ...this.fetchRequestOptions, useS3Cache: false },
);
```
**Seen:** Subito hotfix — fixed in MAR-2039 bugfix branch.
**Generalizable:** Any DataDome-protected site that fetches static assets (chunks, JSON config) through the same `fetchRequest` must explicitly opt into `useProxy: true` via `fetchRequestOptions`. Plain `fetchRequest(url)` defaults to no-proxy.

### 94. Backfill spike burns proxy reputation for days (Subito May 01 pattern)
**Signal:** A specific day shows 4-7× normal request volume in Graylog. Success rate drops on that day AND stays depressed for days afterward even when traffic returns to normal. `forbidden` count creeps up day after day. `no_proxy_cook` events persist far above baseline.
**Root cause:** Anti-bot fingerprinting at proxy-IP level. A high-volume burst from the same IPs trains DataDome (or Cloudflare/Akamai) to flag those IPs aggressively. The fingerprint persists for days — much longer than the spike itself.
**Fix:** No quick fix once it happens.
- **Reactive:** Wait for the proxy reputation to decay (typically 3-7 days). Reduce volume in the meantime.
- **Preventive:** Run backfills on a separate proxy pool from the daily crawl. Or schedule backfills at very low rates over many days rather than a single burst.
**Seen:** Subito May 01 2026 — backfill caused 254k requests vs normal 60-70k. Success rate dropped 60%→30% and stayed there for May 02-03.
**Diagnostic:** Run multi-day trend analysis (`multi-day-trend-analysis.md`). Look for: (1) volume spike on day N, (2) success rate inversion on day N, (3) `forbidden` count higher on N+1, N+2 even though volume is back to normal.

### 95. Puppeteer setJavaScriptEnabled(true) breaks DataDome solving
**Signal:** Browser-path requests started failing — `getMappedBrandsAndModels` exits without parsing brands. Failure happens silently on cold-start (no DataDome cookie yet). Crawler stops after the 5 outer-loop iterations of `getBrandsAndModels` all fail.
**Root cause:** When Puppeteer has JS enabled AND a request interceptor is active (which is the default for the proxy/cookie flow), DataDome's challenge XHRs are blocked by the interceptor (they don't match the expected URL patterns), so the JS challenge never completes. Without a successful challenge, no cookie is issued — the cold-start handshake fails forever.
**Fix:** Keep `await page.setJavaScriptEnabled(false)` in `browser.service.ts`. Don't add a `enableJavaScript` option that flips this on. The static-HTML browser path is what works for cookie acquisition.
**Seen:** MAR-2039 "Change B" tested in staging Apr 29 2026 — staging effectively dead for a day. Reverted; bugfix branch keeps only Change A (cookie persistence).

### 96. DataDome cookie invalidated server-side: warning logged but no recovery (Subito)
**Signal:** Graylog shows `datadome cookie invalidated server-side despite being present in Redis` repeatedly, immediately followed by raw 403 retries (no `start special logic for data dome` between them). Producer eventually crashes with `Problem preparing listingUrl messages` after 8 retries exhaust. Local repro: warm session works once → delete S3 daily cache → second run dies the same way.
**Root cause:** In `trySolveDataDome`, the branch where Redis says `hasDataDomeCookie = true` but the request still got 403 (cookie invalidated by DataDome server-side) only LOGGED a warning — it never called `createValidDataDomeCookie`. The cold-start branch (no cookies in Redis) and the in-jar-but-not-in-Redis branch both did the recovery; only the "invalidated" branch sat silent. So once a Redis-stored session got rejected, every retry just hit 403 forever.
**Fix:** In the `if (redisProxy[options.specificProxy]?.hasDataDomeCookie)` branch, after the warning, call `createValidDataDomeCookie` exactly the same way the other branch does:
```typescript
if (redisProxy[options.specificProxy]?.hasDataDomeCookie) {
    this.logger.warn({ message: 'datadome cookie invalidated server-side despite being present in Redis', ... });
    const validDataDomeResponse = await this.createValidDataDomeCookie<T>({ url, options });
    if (validDataDomeResponse) {
        result = validDataDomeResponse;
    }
}
```
**Seen:** Subito 2026-05-04. Local test confirmed: before fix, 3× warning + crash; after fix, warning + `start special logic for data dome` → `good special logic for data dome` (recovery flow runs). Recovery still fails when proxy is IP-blocked at network level (recovery URL also 403, original URL retry 403) — that's an infrastructure problem, not a code one.
**Generalizable:** Any DataDome-protected site that branches on `redisProxy[proxy].hasDataDomeCookie` in `trySolveDataDome` should attempt recovery in BOTH branches. The 403 always includes a fresh DataDome cookie via Set-Cookie, so the recovery URL has something to work with regardless of what Redis previously stored.

### 98. Broken model page returns full brand catalog (eurostocks pattern)
**Signal:** Site total vehicle count (sum of TotalRows across model pages) significantly exceeds ES unique count. Crawler runs use far more scrape.do credits than vehicle count would suggest. ES query for cross-listing duplicates returns hits — same `url` saved under different `listingUrl` values. Same vehicle appears on multiple model pages of the same brand.
**Root cause:** The site's backend, when given an unknown/invalid model slug, falls back to returning ALL vehicles of that brand instead of returning 0 results or 404. So `volkswagen/id3` (or any made-up slug) returns the entire VW catalog. The crawler then crawls hundreds of pages of duplicates per broken model.
**Verification:** Try multiple URL variants (hyphen, %20-encoded, no-separator) for the suspect slug. If ALL variants return the same inflated TotalRows, it's their backend bug — no URL works. If only the slugified version is broken but the raw href works, it's a slugify issue on our side. Check `StringHelper.slugify` (currently only `.replace(/ /g, '-')` — preserves dots, underscores, apostrophes, plus signs).
**Cost:** Listing fetches duplicated, but worse: every vehicle on broken pages also goes through full detail fetch + parse + ES upsert. RMQ dedup does NOT catch this (different listingUrl = different message hash, see foundational.md → RMQ dedup scope). ES data integrity is preserved (same storeId = upsert overwrites).
**Why TitleSEO filtering at parse time doesn't work:** TitleSEO is generated from the vehicle's own title with inconsistent normalization (Mercedes-Benz → mercedesbenz, Nissan X-Trail → xtrail, Audi e-tron → etron, Porsche 356 Coupe → porsche-other, Volvo 1800S → volvo-amazon). Any startsWith/includes check produces too many false positives/negatives.
**Mitigation options:**
1. TotalRows cap in `getBrandsAndModels`: skip model nav links where page-1 TotalRows is many multiples of brand's per-model average or above an absolute threshold.
2. Hardcoded skip list in the crawler. Brittle but simple.
3. Accept the credit/time cost if it's small relative to the site.
**Detection methods:**
- Old index aggregation: `terms` agg on `url` with `min_doc_count: 2`, then sub-agg `listingUrl` (see es-queries.md → "Detecting broken model pages").
- TotalRows scan: fetch each model page, parse TotalRows from RSC chunk `FrontEndProductVehicleDetails`, flag outliers.
**Seen:** eurostocks 2026-05-07 — 16 broken pages across volvo, renault, ford, kia, peugeot, nissan, opel, ~31,500 inflated vehicle fetches per run. Full list in sites/eurostocks.md.
**Generalizable:** Any site whose backend uses a "show everything if filter unrecognized" fallback. Check by trying a deliberately invalid model slug — if it returns the full brand catalog instead of 0 / 404, this pattern applies.


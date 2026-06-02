# Market Study — Topic Knowledge Base

Curated answers for `ams [topic]` queries. Each entry: dense bullets + Source line.

**Maintenance:**
- Add a new entry whenever a topic comes up that isn't here.
- Use lowercase-hyphenated `## topic-name` headings.
- Keep entries 3-7 bullets, dense, no preamble.
- Always end with a `**Source:**` line — Confluence URL preferred, fall back to `references/foundational.md § section`.

---

## active-vehicles

**Active vs inactive** — vehicles stay "active" as long as the crawler keeps seeing them. Deactivation pipeline runs nightly at 22:00, ~250k/day average, peak ~2M (leboncoin days).

**Data index lifecycle** — `activeFrom` / `activeTo` track when a vehicle was first seen and when it went offline. No `activeTo` = still active.

**Zombie vehicles** — active in the Data index but the crawler can't actually reach them (URL changed, site gone, detection failed). Marko has a detection script.

**Safe threshold** — above ~900k deactivations/night the pipeline slows significantly. Stage default: don't trigger mass deactivation when running tests.

**Source:** [Active vehicles (Confluence)](https://preskok.atlassian.net/wiki/spaces/M/pages/2840821764/Active+vehicles) — full Confluence page not yet synced into knowledge base; ask if you need more depth.

---

## es-indices

**Old search index** — URL-unique. No `workingUrl` field. Primary lookup by URL. Still in active use.

**New search index** — was being built; **frozen** in Mar 2025 deploy. Stops writing; reads continue. Removal discussed Dec 2024 but kept for reads.

**Data index** — history index. Stores `workingUrl`, `activeFrom`/`activeTo`, full vehicle lifecycle, progressive validation history. Source of truth for "everything that ever happened to this vehicle".

**S3 raw cache** — bucket `$AWS_S3_BUCKET_DAILY_CACHE`, keys `YYYYMMDD/[md5]`. **7-day retention.** Used by crawler for same-day reruns without re-fetching from external sites.

**legacyUrl vs workingUrl** — `legacyUrl` = stable key for `storeId`/S3/dedup; `workingUrl` = current accessible URL. ES `url` = workingUrl if set, else legacyUrl.

**Field naming convention** — Old search index (`marketstudy_search_rollover`) uses **mixed case**: top-level fields are PascalCase (`CreatedAt`, `Site`, `URL`, `Brand`, `Model`, `Price`), but nested object subfields keep their original casing. Date field for "when crawled" = `CreatedAt` (no `activeFrom` in old search index). Confirmed from live prod sample 2026-05-15.

**`Description` lives in the old search index** (PascalCase `Description` alongside `Site`/`URL`) — NOT in a separate vehicle-data sibling. Coverage is partial and dealer-dependent (typical site: 60–85% of active docs populated; eurostocks 79.5% confirmed 2026-05-26). The other 15–40% are empty because the source dealer didn't fill it on the ad. Always measure with an aggregation across the active set — a 5-doc sample by `CreatedAt desc` often lands on the unpopulated minority and reads as a false bug.

**Persistent vs reset timestamps** — `activeFrom` (Data index, lowercase) is the **ONLY** field that genuinely persists across the entire vehicle lifetime. Both old-index `CreatedAt` and data-index `createdAt` reset on doc rewrite / index rollover. Observed live: same eurostocks doc has `activeFrom: 2022-03-14` but `createdAt: 2026-05-25`. Use `activeFrom` for any "first ever seen" / cross-deploy / cross-era comparison.

**Rollover duplicate inflation** — when a rollover happens mid-week, the same `storeId` can exist in two backing indices (pre-rollover and post-rollover). A `_search` or `_count` query across the alias returns BOTH copies — inflating totals. Symptom: raw doc count is e.g. 1.4×–2× higher than vehicle count on source site. Diagnosis: run a cardinality aggregation on `URL` field — the cardinality result is the true vehicle count; the difference is rollover duplicates. This is expected behaviour, not a crawler bug. Observed: autohaus-landherr 629 total / 442 unique URL in 7-day window vs 444 on site (2026-05-27). The 1.42× ratio matches a mix of 1× and 2× crawl days (midnight fail + 6 AM retry).

**Source:** session 2026-05-27.

**Kibana CreatedAt histogram is misleading for "vehicle age"** — a `site:"<SITE>"` discover view bucketed by `CreatedAt` shows when docs were last written, NOT how old the vehicles are. During an in-progress crawl you'll see two bars (e.g. ~20k pinned at the previous run's date, ~10k at today) — both groups can be any mix of brand-new and continuously-tracked-for-years vehicles. After the crawl finishes everything collapses to today. To measure actual age, switch to the data index and bucket by `activeFrom` instead. Note: `activeFrom` ALSO resets on reactivation (vehicle deactivated then re-detected → fresh `activeFrom`), so even this isn't perfect — but it's the closest thing to "first seen".

**Validation gate is split between indices** — the Graylog log `"Skip saving data vehicle to ES due to failed validation"` (context `VALIDATION`) **only blocks writes to the data index**. The old search index write path runs separately and bypasses the same gate, so docs that failed validation can still appear in `marketstudy_search_rollover`. This is the current architectural behaviour. Confirmed 2026-05-26: 8 eurostocks docs with negative `Price`/`NettoPrice` (Ferrari/Bentley/Mercedes/etc.) present in old index, absent in data index, all logged 9× as VALIDATION skips. When you see "validation skipped but data is still in ES", check which index you're reading — it's almost certainly the old search index.

**country field** — in old search index: `Country.country` (capital C outer, lowercase c inner — mixed!). In Data index: `country.country` (all lowercase, confirmed working). No `.keyword` suffix needed on either. Country values from `CountryInfo.ts` — notable: Czech Republic = `Czech`, North Macedonia = `Macedonia`, Bosnia = `Bosnia and Herzegovina`. Moldova is NOT in `CountryInfo.ts` (no crawler exists for it).

**Active vehicles Kibana query (Data index):** — Data index uses all-lowercase fields (different from old search index).
```json
GET market-study-vehicle-data_rollover/_search
{
  "size": 0,
  "query": {
    "bool": {
      "must": [{ "terms": { "country.country": ["Albania", "Slovakia", "Croatia", "Czech", "Hungary", "Romania", "Serbia", "Bosnia and Herzegovina", "Montenegro", "Macedonia", "Austria", "Bulgaria"] } }],
      "must_not": [{ "exists": { "field": "activeTo" } }]
    }
  },
  "aggs": { "by_country": { "terms": { "field": "country.country", "size": 20 } } }
}
```
`activeTo` not existing = currently active. Index name from `.env` `ELASTIC_SEARCH_VEHICLE_DATA`. Note: `marketstudy_data_rollover` seen in old docs — may be an alias; use `market-study-vehicle-data_rollover` (confirmed working).

**New vehicles per day per country (last 7 days, old search index):**
```json
GET marketstudy_search_rollover/_search
{
  "size": 0,
  "query": { "bool": { "must": [
    { "terms": { "Country.country": ["Albania","Slovakia","Croatia","Czech","Hungary","Romania","Serbia","Bosnia and Herzegovina","Montenegro","Macedonia","Austria","Bulgaria"] } },
    { "range": { "CreatedAt": { "gte": "now-7d/d", "lte": "now+1d/d", "time_zone": "Europe/Ljubljana" } } }
  ] } },
  "aggs": { "by_day": { "date_histogram": { "field": "CreatedAt", "calendar_interval": "day", "time_zone": "Europe/Ljubljana", "format": "yyyy-MM-dd" },
    "aggs": { "by_country": { "terms": { "field": "Country.country", "size": 20 } } }
  } }
}
```

**Avg vehicles per day per country (`avg_bucket` pattern):**
```json
GET marketstudy_search_rollover/_search
{
  "size": 0,
  "query": { "bool": { "must": [
    { "terms": { "Country.country": [...] } },
    { "range": { "CreatedAt": { "gte": "now-6d/d", "lte": "now/d", "time_zone": "Europe/Ljubljana" } } }
  ] } },
  "aggs": { "by_country": { "terms": { "field": "Country.country", "size": 20 },
    "aggs": {
      "by_day": { "date_histogram": { "field": "CreatedAt", "calendar_interval": "day" } },
      "avg_per_day": { "avg_bucket": { "buckets_path": "by_day._count" } }
    }
  } }
}
```
Result: `aggregations.by_country.buckets[].avg_per_day.value`. Use `lte: "now/d"` (not `now+1d/d`) to exclude today's partial data. ⚠️ Sites with `runOnNthDays > 1` (e.g. `hasznaltauto` every 3 days, `mobile-bg` every 3 days) get inflated averages because zero-days are included in the bucket count — real per-run output is much higher than the avg suggests.

**Slack format for ES results** — markdown tables with emoji flags never align (emojis are double-width). Use plain list instead:
```
*Active vehicles by country*
🇦🇹 Austria — 153,298
🇷🇴 Romania — 135,775
*Total: 1,055,327*
```
Paste directly (no code block). `*text*` = bold in Slack.

**Source:** `session 2026-05-15`, `src/shared/const/CountryInfo.ts`, `src/shared/const/CrawlingSites.ts`.

---

## deactivation-pipeline

**Schedule** — starts nightly at **22:00**.

**Volume** — ~250k/day average; peak ~2M (leboncoin days); safe threshold ~900k (above this, slows significantly).

**Behavior** — multisearch before indexing; flag `bulk_save_search_vehicles` request_ids; on timeout retry once → `MS_BULK_DL`.

**`createdAt = lastVisit` during deactivation** — when a vehicle is deactivated, the code sets `vehicle.createdAt = vehicle.activeTo = data.lastVisit` (round-second from MySQL DATETIME). This is intentional: `createdAt` is a "state-as-of" timestamp — the deactivated state became valid at the last-crawl time, not at 22:00 deactivation run time. Before updating, the code pushes a history delta `{createdAt: [old_createdAt, lastVisit]}`. Special case: if `vehicle.createdAt >= newActiveTo`, uses existing `createdAt` (1-day-active vehicle — no meaningful history change). **Kibana attribution consequence:** all deactivation writes appear under `lastVisit` date, not the deactivation run date. A failed Saturday crawl (57k found instead of 103k) → Sunday night deactivation → ~47k Data index writes appear under Friday in Kibana (last time those vehicles were seen). `src/vehicle/store-vehicle.service.ts:154–176`.

**Manual lock** — can lock a specific site to prevent deactivation tonight. Used during hotfixes when crawl is broken but we don't want mass-deactivation.

**Per-site auto-lock (Redis)** — `DEACTIVATION_PREVENTED_SITES` key holds a JSON map of `site → { timestamp, reason }`. Written with `TimeEnum.ONE_YEAR_IN_SECONDS` TTL (31536000 s) so it never expires naturally. Populated by `checkAndPreventDeactivationBySite` cron when missing-vehicle ratio exceeds `DeactivationPreventionThresholds`. Already-locked sites are excluded from the MySQL ratio query (8-day window). Unlock is manual via `unlockSiteDeactivation` endpoint. Email notification: one consolidated email per cron run — newly locked sites at top (⚠️ header), already-locked sites below.

**Mid-day deploy protocol** — lock deactivation → deploy → rerun crawler (S3 cached responses, no credits) → verify → redeliver DL → unlock.

**Source:** `references/foundational.md § Deactivation pipeline`, `§ Mid-day deploy protocol`.

---

## rmq-queues

**Per-site queues** — `MS_[SITE]_LISTING_URLS_TO_FETCH` for big sites: autoscout, mobile, leboncoin.

**General** — `MS_GENERAL_LISTING_URLS_TO_FETCH` for small/medium sites.

**Browser crawlers** — `MS_BROWSER_CRAWLERS_LISTING_URLS_TO_FETCH` (puppeteer-based: subito, olx-ro, etc).

**Limited consumers** — `MS_LIMITED_CONSUMERS_LISTING_URLS_TO_FETCH` for **otomoto** (CloudFront-heavy, isolated to not block other sites).

**Weekly** — `MS_WEEKLY_LISTING_URLS_TO_FETCH` for **car-gr only**. Tue start → drains week → Mon 23:25 purge. Not-empty Tue-Sun is normal.

**Hungary** — `MS_HUNGARY_LISTING_URLS_TO_FETCH` shared by mobile-bg (matchingDay 0) + hasznalt-auto (matchingDay 1). Max 6 consumers. Purged 23:25 nightly.

**Dead letters** — `MS_DL` (no TTL, manual purge), `MS_BULK_DL` (24h TTL, mostly dedup), `MS_BULK_SAVE_DL` (ES/MySQL connection issues), `MS_TASKS_DL` (long-running task timeout).

**Default timeout** — 30 min. Raised to 2.5h for `MS_WEEKLY_...` (car-gr).

**Source:** `references/foundational.md § Queue architecture`, [RMQ queues Confluence](https://preskok.atlassian.net/wiki/spaces/M/pages/2611314741/RMQ+queues).

---

## scrapedo

**Implementation** — implemented 2025-11-24. Account: `tt@preskok.si`. Sites: hasznalt-auto, promoneuve, autoscout-ch, leboncoin, car-gr (verify in code).

**Credit reset** — monthly on the **24th**.

**401 = no credits** — body "You have no credits or your subscription has been suspended". NOT a target-site auth error. Do NOT retry. Throws `ScrapeDoCreditsExhaustedError` centrally in service layer.

**400 = bad request** — invalid params/headers. Do NOT retry.

**Cost monitoring** — `requestCost > maxRequestCost` → Graylog WARN `"Request cost is bigger than max cost"` → email alert per site (with grace period). Indicates proxy escalation or fingerprint detection.

**Credits lock (Redis)** — too many expensive requests for a site → Redis lock until next crawl TTL. Auto-recovers — no manual action needed unless persistent.

**Personal accounts banned** — Matea's personal account permanently banned after <50 credits while testing. Always use team account `tt@preskok.si`.

**Source:** [ScrapeDo documentation (Confluence)](https://preskok.atlassian.net/wiki/spaces/M/pages/3977576464/ScrapeDo+documentation), `references/foundational.md § ScraperAPI vs scrape.do`.

---

## scraperapi

**Credit costs per site** — avto-net: **10 credits/req**, leboncoin: **1 credit/req**, lacentrale: **35 credits/req** (ultra-premium only), auto-connect makes+models: **1 credit/req** (regular tier sufficient, CF does not challenge scrape.do datacenter IPs on these endpoints).

**Escalation** — standard request (1st-2nd attempt) → premium proxy (3rd) → ultra-premium proxy (4th). Each retry tier consumes more credits.

**creditsLock** — pauses 20 min when credits exhausted.

**Nov 5 2025 incident** — billing model changed silently; all sites jumped to 10 credits/request regardless of tier. Budget burned in days. **Always contact support if all ScraperAPI sites fail on the same date** — don't assume crawler issue (Pattern #90).

**Monthly check** — 24th. >70% mid-period → consider disabling low-priority sites.

**Source:** [ScraperAPI Confluence](https://preskok.atlassian.net/wiki/spaces/M/pages/3370680321/ScraperAPI), `references/foundational.md § ScraperAPI vs scrape.do`.

---

## svl

**What it is** — `shouldValidateListingVehicle` boolean flag. Skips visiting the detail page when listing data matches what's in S3. Reduces network traffic dramatically.

**Pass = skip details** — listing URL + key fields match S3 → no detail request.

**Fail = visit details** — any mismatch in price, model, URL, etc. → falls back to detail fetch.

**Where it works** — only on crawlers extending `HtmlAdVehicleCrawlerAbstract`. API crawlers must be refactored to HTML-style if site has >5k vehicles.

**Must use** — sites with >5k vehicles, or any foreign-currency site (currency conversion only happens on details visit or every 30 days).

**Queue debug flow** — `MS_BULK_SAVE_LISTING_VEHICLE_CHECK` → `MS_BULK_SAVE_VEHICLES` = pass; → back to `MS_GENERAL_LISTING_URLS_TO_FETCH` = fail.

**Stage caveat** — stage uses prod S3 daily cache → SVL always fails on first stage run. Re-run to see real behavior.

**Known benign failures** — blocket (~1.7k/day, discounted-price mismatch), auto-connect (super-model intentional), any site's first crawl after enabling SVL (100% expected).

**Graylog context** — `LISTING_VEHICLE_CHECK`.

**Source:** [SVL: A how-to guide](https://preskok.atlassian.net/wiki/spaces/M/pages/3356852239/ShouldValidateListingVehicle+SVL+A+how-to+guide), `references/foundational.md § SVL`.

---

## proxy

**Base URL** — `$PROXY_URL`.

**80XX = external** — worldwide providers. 8000 = random of 8001-8005; each 8001-8005 uses 2 proxies from 8010-8019.

**802X = changeable** — proxy11-15 = ports 8021-8025. Manually change IP/country/reconnect via API endpoint. Not accessible via 8000.

**90XX = internal** — ISP modems (landline/mobile). PROXY_SET_1: 9007, 9004. PROXY_SET_2: 9001, 9005. Current: 9001=rpi-stas1, 9003=rpi2-stas2 (INACTIVE), 9004=rpi-preskok1, 9005=rpi4-kristjan, 9007=rut240-stas-lte-hot (SIM 069839053).

**Status check** — `$PROXY_URL (HTTP)` (80XX), `$PROXY_URL (HTTP, 90XX)` (90XX). Admin: `$PROXY_URL/admin/`.

**HAProxy stats dashboard** — same host as `$PROXY_URL`, port **:8080**. Loads the HAProxy stats HTML. Append `/;csv` for machine-parseable CSV: `curl -s http://<proxy-host>:8080/\;csv`. Backend groups are named by provider: `vpn_*` = PRESKOK pool (proxy1–proxy15, proxyfr1, proxyfr2 — all served via 80XX frontends), `hma_*` = HideMyAss pool. Each physical proxy box appears in multiple backend groups (round-robin `vpn_backend_all_8000`, paired `vpn_backend_80XX`, single-listener `vpn_backend_single_80XX`). A server entry named with literal suffix `offline` (e.g. `proxy1offline` on `hma_backend_single_offline_8020`) is **intentionally decommissioned** — expected to show DOWN/L4CON, not a real outage.

**Swap procedure** — see fix-playbook.md. If 9007 down → AWS parameter store → delete Redis `datadomeService` → deploy.

**Source:** [Proxy Confluence](https://preskok.atlassian.net/wiki/spaces/M/pages/2609971332/Proxy), `references/foundational.md § Proxy architecture`, session 2026-05-27.

---

## s3-cache

**Bucket** — `$AWS_S3_BUCKET_DAILY_CACHE`. Region: configured per env.

**Key format** — `YYYYMMDD/[md5-hash-of-url]`.

**Retention** — **7 days** in S3. **Cache is only used if the key is from TODAY** — the crawler reads `YYYYMMDD/md5` where YYYYMMDD = today's date. Yesterday's key is ignored even if it exists in S3. Effectively a 1-day cache for crawl reruns, 7-day archive for investigation/replay.

**Cache rules** — 200 OK is cached; 4xx and 5xx are NOT cached. **Important exception:** 200-with-empty-body IS cached → if a site returns empty 200 (silent failure), the cache must be manually deleted before rerun.

**Delete cached response** — `aws s3 rm s3://$AWS_S3_BUCKET_DAILY_CACHE/[YYYYMMDD]/[md5-hash]`. Look up the hash via Graylog or error logs.

**Same-day rerun** — reads from S3, no credits spent, re-parses with current code. Standard mid-day fix flow.

**Source:** `references/foundational.md § Index architecture`, `references/fix-playbook.md § Delete S3 cached response`.

---

## deploy-flow

**Branches** — feature/MAR-XXX-name, hotfix/MAR-XXX-name. Bitbucket targets: `hotfix/*` → master (NOT develop), bypasses develop review.

**Proper flow** — develop → stage → master → prod. Min 1 PR approve.

**Mid-day hotfix** — lock deactivation for site → deploy to master → rerun crawler on prod (S3 cached, no credits) → verify ES + Graylog → redeliver DL messages → unlock deactivation.

**Stage instances** — daily reset, scaled down overnight. Increase manually for stage tests via Jenkins (`StageInstanceControl`). Consumers = instances × 2.

**Coordination** — Matea usually handles prod deploys.

**Common mistake** — deploying wrong branch to prod. If symptoms look like "half-crawl" or "feature acts like stage" → double-check master is actually deployed.

**Source:** `references/foundational.md § Deploy flow & branches`.

---

## site-protection

**Cloudflare** — car-gr, hasznalt-auto, autoscout-ch (+ possibly CloudFront), mobile-bg, avto-net, pazar3, auto-connect, vetura-neshitje.

**CloudFront (AWS)** — otomoto, blocket. High 403 rate is **expected and normal** (not an incident).

**Datadome** — leboncoin, polovni-automobili (base protection).

**Akamai** — leboncoin (added on top of Datadome Jan 2025 → ultra-premium required).

**Incapsula** — ouestfrance-auto (fake 200 responses).

**first-id** — lacentrale (cross-site tracking, fingerprint feeder).

**Source:** [Site protection list (Confluence)](https://preskok.atlassian.net/wiki/spaces/M/pages/3898114050/Site+protection+list), `references/foundational.md § Site protection list`.

---

## working-url-fix

**Goal** — fix the `url` in ES vehicles when a site's URL format changes, so vehicles remain accessible via ES, without changing `storeId` (which would create duplicates in S3).

**legacyUrl** — used for `storeId` (S3 key + Data index `id`). Stays stable. Saved to old search index as `url`.

**workingUrl** — current accessible URL. Saved to S3 as `workingUrl`. Saved to New search + Data index as `url`.

**ES url** — workingUrl if set, else legacyUrl.

**Implementation (simple sites / SVL=false)** — override `fetchRequest()` to use workingUrl; assign workingUrl on vehicle in details parsing; assign workingUrl + url to VehicleListItem in listing parsing.

**Implementation (big sites with SVL=true)** — start with details-only assignment to gradually populate workingUrl. Once enough vehicles covered, add listing-level assignment. Otherwise mass SVL failures from "change detected".

**Backup rebuild caveat** — vehicles pulled from old search index during rebuild won't have workingUrl until re-crawled.

**Source:** [Working URL fix (Confluence)](https://preskok.atlassian.net/wiki/spaces/M/pages/3002302476/Working+URL+fix), `references/foundational.md § workingUrl / legacyUrl`.

---

## nth-day-crawl

**What it is** — sites can run every N days, not daily. More granular than `runWeekly`.

**`runOnNthDays`** — interval in days (3 = every 3rd day, 7 = weekly).

**`matchingDay`** — offset to stagger sites on the same interval. Example: lacentrale and leboncoin both run every 3 days but different `matchingDay` so they never start same day.

**Scheduling check** — `(days since 2024-01-01) % runOnNthDays == matchingDay`.

**Reference date** — `2024-01-01`.

**Debug rule** — if site fired 0 alerts and uses `runOnNthDays`, calculate the modulo first before investigating. May simply not be the site's day.

**Source:** [NTH Day Crawl (Confluence)](https://preskok.atlassian.net/wiki/spaces/M/pages/3370876940/NTH+Day+Crawl), `references/foundational.md § NTH Day Crawl`.

---

## skip-visiting-detail

**`skipVisitingDetail`** — boolean property on `VehicleListItem`. Different from SVL.

**Behavior** — skips the detail page entirely; vehicle is still processed through the full pipeline using listing-page data only.

**vs SVL** — SVL conditionally skips details (when listing matches S3); skipVisitingDetail unconditionally skips details for vehicles flagged with this property.

**When to use** — listing page has sufficient data, OR detail page is too costly/complex to access.

**Bonus** — also enables saving dealer data from listing pages without visiting detail pages.

**Source:** [Skip Visiting Listing Details (Confluence)](https://preskok.atlassian.net/wiki/spaces/M/pages/3456303118), `references/foundational.md § skipVisitingDetail`.

---

## drivetrain

**Field meaning** — ES `driveTrain` = FWD/RWD/AWD value crawled from a site.

**Current state (2026-04-07)** — ~60% of vehicles have `null`; ~8% have wrong mapped values (conflict with `engine` field populated by DataAPI).

**Planned fix** — repopulate from DataAPI Engine field values after S3 remap. **Date NOT yet scheduled** as of Apr 2026.

**Don't treat null as bug** — it's a data coverage limitation, not a parsing failure. Don't open tickets for null driveTrain unless coverage drops below baseline.

**Source:** [2026-04-07 DriveTrain field in ES (Confluence)](https://preskok.atlassian.net/wiki/spaces/M/pages/4195057737/2026-04-07+DriveTrain+field+in+ES).

---

## ad-site-crawler

**Pattern** — extends `HtmlAdVehicleCrawlerAbstract` (HTML/scraping) or `ApiAdVehicleCrawlerAbstract` (API).

**Required setup files**:
- `src/crawler/sites/[Site]/[Site].service.ts` — main crawler
- `src/shared/const/SiteKeys.ts` — `AdSiteKeysEnum` entry
- `src/shared/const/CrawlingSites.ts` — queue + flags (`runWeekly`, `runOnNthDays`, `shouldValidateListingVehicle`)
- `src/reporting/const/SiteThresholds.ts` — alert threshold (0.2 for <2k ads, 0.1 for >2k)
- `src/shared/const/CountryInfo.ts` — country VAT
- `src/crawler/crawler-aliases.module.ts` — service provider

**Required methods**:
- `getBrandsAndModels()` — return all brand-model combinations as listingUrls
- `getVehicleListPageResponse(options)` — parse a listing page, return `vehicleListItems` + `nextPageUrl`
- `parseVehicleInput(params)` — parse a single ad → `AdVehicle`

**Validation** — every Jira ticket for new crawler has a `MarketStudy - validate site crawler` checklist. Validate after stage deploy (don't tick boxes), then check on prod next day.

**Source:** [Ad Site Crawlers (Confluence)](https://preskok.atlassian.net/wiki/spaces/M/pages/2594471964/Ad+Site+Crawlers).

---

## people

**Matea Lenček** (UQXNRJK17) — lead. Has RMQ, S3 delete, prod param-store access. Often deploys prod.

**Filip Ožbolt** (U04GZH40QMD) — engineer, on-call rotation.

**Danijel Daskijević** (U042X3G1ZQT) — engineer, on-call rotation (ex-QA).

**Gregor Džampo** (U052JEQQGNR) — product / business decisions (which sites matter, disable/prioritize).

**Marko Lavrinec** (U03A150FJ65) — infra-adjacent. Built S3-vs-ES validation, zombie detection.

**Stas** (devops) — hosts mobile proxies (9001-9007), Graylog/infra. Report to `#tt-devops-support`.

**Source:** `references/foundational.md § People / roles`.

---

## price-discount

**New vehicles** — `discount` often = factory/catalog price minus customer price (common on French dealers).

**Used vehicles** — no default discount. Save discount only if seller explicitly markdown'd (start price visible, lowered price).

**Catalog vs seller price** — seller price = `price`. Catalog can be higher OR lower. If lower, discount would be negative → don't save discount, save only price (cardoen, star-terre).

**Netto / no-VAT** — `rawNettoPrice` → `nettoPrice`. Trap: German commercial vehicles often show VAT-excluded as primary. Check both, pick brutto as `price`.

**Leasing / financing** — monthly installments are NOT prices. Skip if site labels leasing. Otherwise heuristic: DOFR > 5y + price < 2k → skip on blocket/finn.

**Mileage missing** — if `mileage` null/missing, save ONLY seller's `price` (no discount, no catalog) — prevents junk data.

**Source:** [Price and discount handling (Confluence)](https://preskok.atlassian.net/wiki/spaces/M/pages/3614179347/Price+and+discount+handling), `references/foundational.md § Price/discount canonical rules`.

---

## s3-buckets

**Daily cache (raw responses)** — `$AWS_S3_BUCKET_DAILY_CACHE` (prod/stage env var), `local-ms-raw` (LocalStack). Key format: `YYYYMMDD/[md5]`. 7-day retention. Hash is `md5(url + "_" + data)`; for GET-only requests data is `undefined` so the suffix `_undefined` is appended before hashing.

**Store vehicle (parsed vehicle JSON)** — `$AWS_S3_BUCKET_STORE_VEHICLE` (prod), `$AWS_S3_BUCKET_STORE_VEHICLE (stage)` (stage), `local-ms-store` (LocalStack). Env: `AWS_S3_BUCKET_STORE_VEHICLE`. Key format: `a/b/c/abc...` (first 3 chars of `storeId` as folder hierarchy + full storeId). `storeId` = md5 of `legacyUrl` (also stored as `id` in Data index).

**Other store buckets** — `AWS_S3_BUCKET_STORE_VEHICLE_RENT` (`msvehiclestorerent-...`), `AWS_S3_BUCKET_STORE_DEALER` (`msstoredealer-...`), `AWS_S3_BUCKET_GENERAL_STORAGE` (`msstoregeneral-...`).

**Personal/dev buckets** — `marketstudy-filipozbolt-271070082075` (Filip's personal bucket for tooling), `devenv-preskok-271070082075` (Stas's shared dev bucket — data not safe, can be wiped any time). Use these instead of LocalStack when you need real-AWS behavior.

**Quick lookup commands:**
```bash
# prod daily cache (uncomment prod s3 block in .env first, or inline the bucket name)
AWS_PROFILE=preskok-prod aws s3 cp s3://$AWS_S3_BUCKET_DAILY_CACHE/[YYYYMMDD]/[md5] ./
# stage daily cache
aws s3 cp s3://$AWS_S3_BUCKET_DAILY_CACHE (stage)/[YYYYMMDD]/[md5] ./
# local daily cache
aws --endpoint-url=http://localhost:4566 s3 cp s3://local-ms-raw/[YYYYMMDD]/[md5] ./
# prod store vehicle (first 3 chars of storeId as path)
aws s3 cp s3://$AWS_S3_BUCKET_STORE_VEHICLE/a/b/c/abc...full ./
# list local store
aws --endpoint-url=http://localhost:4566 s3 ls s3://local-ms-store/ --recursive
```

**Token expiry** — `ExpiredToken` error means AWS SSO session expired. Re-login via Identity Center. LocalStack has no auth, never expires.

**S3 key date uses server LOCAL time (CEST = UTC+2)** — `DateHelper.toDailyString()` runs on the production server which is in CEST. After **22:00 UTC** (= 00:00 CEST next day), the YYYYMMDD in the S3 key rolls to the NEXT calendar day. When investigating a crash at e.g. 22:46 UTC on 2026-05-14, the S3 key will be `20260515/…`, not `20260514/…`. Always add 2 h when converting alert timestamps to S3 date prefixes.

**DL contamination check (cross-user/random-site responses)** — when suspecting ScrapeDo/ScraperAPI returned another user's page, fetch the actual S3 raw and inspect the first 500 bytes:
```bash
# 1. Compute S3 key: md5(url + "_undefined") for GET requests
python3 -c "import hashlib; print(hashlib.md5(('$URL_undefined').encode()).hexdigest())"
# 2. Fetch — use NEXT day's date if crash happened after 22:00 UTC
AWS_PROFILE=preskok-prod aws s3 cp s3://$AWS_S3_BUCKET_DAILY_CACHE/YYYYMMDD/<hash> - | head -c 500
```
Contamination signals: body starts with `{` (JSON from a completely different API), body contains wrong domain/language, or `Content-Type: text/html` but body is clearly not HTML. Legitimate = `<!DOCTYPE html>` + correct domain/lang.

**Source:** `session 2026-05-15`, `src/crawler/CrawlerAbstract.ts:201`.

---

## local-testing-flags

**Disable cache write (clean responses)** — `AWS_S3_BUCKET_DAILY_CACHE_PERMISSION_WRITE=false` in `.env`. Crawler reads from cache but won't write back. Useful when iterating on parsing logic — fresh responses every run, no stale-by-yesterday's-write contamination. **Re-enable after testing** or you'll silently break next day's reruns.

**Skip cache for one request** — pass `useS3Cache: false` in `fetchRequest` options. Use when:
- The request fetches a token / cookie that other requests depend on (avoid loop where the bootstrap request reads its own stale response from cache).
- Testing redis-cached values (datadomeService, eurostocks token) — request must hit the network to refresh redis.
- Example: `await this.fetchRequest(this.baseUrl, { useS3Cache: false })`.

**Load raw response into LocalStack for testing** — copy a problematic response from prod S3 and replay locally without burning credits:
```bash
# 1. Save prod response locally
aws s3 cp s3://$AWS_S3_BUCKET_DAILY_CACHE/[YYYYMMDD]/[md5] ./response

# 2. Upload to LocalStack under TODAY's date so the crawler reads it
aws --endpoint-url=http://localhost:4566 s3 cp ./response s3://local-ms-raw/$(date +%Y%m%d)/[md5]

# 3. If you get "x-amz-trailer header not supported", disable checksum:
AWS_REQUEST_CHECKSUM_CALCULATION=when_required \
  aws --endpoint-url=http://localhost:4566 s3 cp ./response s3://local-ms-raw/$(date +%Y%m%d)/[md5]
```
Now run only the listing/detail-URL crawl path — the crawler reads from LocalStack, no external request, parsing changes are exercised against the exact bad response.

**Daily cache delete (force refetch)** — `curl -X POST 'http://localhost:3000/api/v1/market-study/delete-daily-cache' -H 'Authorization: abcd'`. Wipes ALL sites' daily cache, not per-site. Used when stale local cache is masking your code change.

**Source:** `CLAUDE.md § Local crawler testing recipe`, `references/fix-playbook.md`, `.env`.

---

## bulk-save-queues

**Two distinct bulk-save queues, two distinct ES indexes:**

**`MS_BULK_SAVE_VEHICLES`** — saves to **OLD search index** (URL-unique). Property names use **lowercase** (`url`, `site`).

**`MS_BULK_SAVE_SEARCH_VEHICLES`** — saves to **NEW search index** (frozen Mar 2025). Property names use **PascalCase** (`URL`, `Site`). Still receives messages but new search index is read-only.

**`MS_BULK_SAVE_LISTING_VEHICLE_CHECK`** — SVL gating queue. If listing data matches S3 → routes to `MS_BULK_SAVE_VEHICLES` (skip details). If mismatch → routes back to `MS_GENERAL_LISTING_URLS_TO_FETCH` (visit details).

**Why this matters when redelivering from `MS_BULK_SAVE_DL`** — the DL queue mixes messages from both bulk-save queues. Match by queue name OR by property casing (lowercase = OLD, PascalCase = NEW) before redelivering, otherwise the message goes to the wrong index.

**24h TTL on `MS_BULK_DL`** — most entries are dedup messages, not real failures. Dropping after 24h is intentional. Real failures show up in `MS_BULK_SAVE_DL` (ES/MySQL connection issues) and persist longer.

**Deactivation cascade** — during 22:00 deactivation, multisearch-before-indexing fails under ES load → bulk request retried once → on second fail goes to DL. Telltale: `request_id` contains `bulk_save_search_vehicles`. Pattern #73 / #87 cover the cascade.

**Source:** `references/foundational.md § Queue architecture`, `references/failure-patterns.md § 23, 73, 87`.

---

## cache-vs-svl

**These are two different mechanisms — common point of confusion.**

**Daily cache (S3 raw response)** — applied at the **HTTP-fetch layer**. Before `fetchRequest()` makes an external call, it checks S3 for `YYYYMMDD/md5(url)`. Hit → returns the cached body, NO external request. Miss → fetches, caches if successful (200 only; 4xx/5xx not cached). Affects every request — listings, detail pages, API calls. Log signal: `"Response found in S3"`.

**SVL (`shouldValidateListingVehicle`)** — applied at the **vehicle-processing layer**, AFTER the listing fetch. For each vehicle on the listing page: if listing data matches the existing S3-stored vehicle entry → skip the detail visit entirely. If mismatch → visit details. Log signal: context `LISTING_VEHICLE_CHECK`.

**Order of operations on a listing page:**
1. `fetchRequest(listingUrl)` — daily cache may serve the listing HTML.
2. Parse listing → `VehicleListItem[]`.
3. For each item: SVL check → if pass, save listing data → done. If fail, queue detail URL.
4. `fetchRequest(detailUrl)` — daily cache may serve the detail HTML (independent from SVL decision).

**Two key implications:**
- **SVL skipping does NOT bypass the daily cache for the listing fetch** — the listing page still came from S3 (or network) before SVL ever ran.
- **A "Response found in S3" log on a detail URL means the crawler DID try to visit details** (SVL failed), it just got the response from cache instead of making a network call.

**Why same-day rerun seemingly "skips details"** — SVL is comparing today's listing page against the S3-stored vehicle (which was saved during the FIRST run). The listing data already matches what we just saved → SVL passes → no detail visit. Pattern explains why the second run takes a fraction of the time of the first.

**Stage caveat** — stage uses prod S3 daily cache → SVL almost always FAILS on first stage run because the prod-saved S3 response is from a different prod-time crawl, mismatches local listing parse. Re-run stage to see real SVL behavior.

**Source:** `references/foundational.md § Index architecture`, ams `## svl`, ams `## s3-cache`.

---

## coding-rules

**Don't mock errors with truthy defaults** (Matea's rule) — if `getBrandsAndModels()` returns `[]` or partial data on error, the crawler logs success with 0 vehicles and the alert system thinks the site is empty. Always throw, let retry handle it. Pattern: remove safeguards on lines that swallow errors — let the cron retry (5 attempts).

**`useS3Cache: false` for redis-bootstrapping requests** — if a request fetches a token/cookie consumed by all subsequent requests, NEVER let it read from S3 cache. The cached response would feed itself in a loop. Example: gruppo-piccirillo bootstrap request.

**Defensive fetch** — `const html = await this.fetchRequest(url) ?? '';` so `$.load()` never gets undefined. Pattern #1 (`cheerio.load() expects a string`) is preventable with a single `?? ''`.

**Don't assign mutable state to `this`** — multiple instances each get their own `this.X` and diverge. If the value can change at runtime (mappings, indexes), put it in Redis. If it's read-only at startup, instance state is fine.

**Spread `requestOptions` in every `fetchRequest()`** — `await this.fetchRequest(url, { ...options, headers: {...} })`. Without the spread, caller-passed options are dropped silently.

**`getFetchRequestOptionsForDetailsUrlValidation()` overrides** — needed when details URL validation must use different fetch behavior than the main crawl (e.g. autovit-ro sets `followRedirect: false` for validation only). Crawlers with redirect-based URL changes need this method overridden, otherwise validation falsely fails.

**Skip-and-log unrecoverable items** — for fields that can be missing legitimately (model, version), log via `PARSER_DEBUGGING` context and `continue`, never throw. Throwing kills the whole batch.

**Don't return raw fields without comparison knowledge** — Old search index stores LISTING-VALIDATED vehicles only; many fields are null even though the site has them. To investigate "why is field X null for site Y", query the **Data index** (`market-study-vehicle-data_rollover`), not the Old index.

**Override + super() pattern for inverting parent logic**:
```typescript
public isResponseForbidden({ response, responseBody }): boolean {
    const isForbidden = super.isResponseForbidden({ response, responseBody });
    return !isForbidden && /* additional condition */;
}
```
Useful when the parent's logic is mostly right but inverted for one edge case.

**Source:** team Slack threads, `references/failure-patterns.md`, on-call rotation lessons.

---

## graylog-retention

**Logs older than ~7-10 days are gone.** Variable depending on log volume across all Preskok projects (shared Graylog). Don't assume yesterday-of-last-week is queryable.

**Rough timestamps to pin a date:** S3 daily cache is also 7 days, so for incidents older than that, Slack threads and ES Data index (with `activeFrom` / `activeTo` / `createdAt`) are your only sources.

**Aug 8 2025 outage** — production Graylog logs permanently lost for that day (Graylog ES went down during high prod ES load). Cross-check with Filebeat (`filebeat_*`) for silent worker kills Graylog missed.

**Lag during high load** — Graylog can be 5-10 min behind real-time. Active incidents: cross-check CloudWatch / ECS task logs.

**Standardization plan** — re-using existing field names instead of creating new ones is intentional (reduces ES bloat, allows future retention bump). Don't add a new field unless the existing ones genuinely don't fit.

**Source:** `references/foundational.md § Graylog reliability & retention`, `references/graylog-queries.md`.

---

## application-modes

**Set `APPLICATION_MODE` env var** to load only a subset of NestJS modules:

| Mode | Port | Purpose |
|------|------|---------|
| _(unset)_ | 3000 | Full local dev (everything) |
| `WORKER` | 3000 | Crawler + RMQ consumers + data processing |
| `SEARCH_API` | 4000 | Read-only search API |
| `BULK_SAVER` | 3001 | Bulk persistence worker |

**Module loader** — see `src/app.module.ts` for conditional loading.

**Multiple workers locally** — `APPLICATION_MODE=WORKER npm run start:dev` × N. Port 3000 conflicts on the 2nd+ instance are harmless (HTTP fails to bind, RMQ consumers still attach with prefetch=1).

**Watch-mode gotcha** — if a worker crashes mid-startup with `EADDRINUSE`, `nest start --watch` does NOT auto-restart on crash, only on file change. Symptoms: watch process alive, no child, port held by zombie. Fix: `lsof -i :3000`, `kill -9 <PID>`, save a real change to retrigger.

**Stage/dev simulation** — to point search-api UI at local dev: in `.env`, change `"url": "http://localhost:4000"` → `"url": "http://localhost:3000"` (full-mode local has search-api on 3000, not 4000).

**Source:** `CLAUDE.md § Application Modes`, `src/app.module.ts`.

---

## live-stage-prod-from-local

**Pull prod data from local devenv** — possible via DEVENV2 setup with AWS Identity Center.

**Flow:**
1. Set up DEVENV2 per [Preskok Devenv2 Environment setup with AWS Identity Center](https://preskok.atlassian.net/wiki/spaces/SR/pages/3902930955).
2. In `.env`, switch ES host from local Kibana → prod Kibana.
3. Search-api on local now hits prod ES — useful for reproducing report bugs on real data without copying.

**`.env` switch convention** — comment out the dev/local block, uncomment prod block. Easy to forget to switch back; if next day's local run looks weird, check `.env` first.

**Reporting from local** — `.env` on prod ES means you can fire validation/report endpoints locally that will hit prod ES. Good for iterating on report queries without a deploy. **DON'T** call any write endpoints in this mode.

**Risk** — prod tokens are static at the moment (devops ticket open). Don't leave prod token in committed `.env`. Pull from LastPass each session.

**Source:** [Devenv2 setup (Confluence)](https://preskok.atlassian.net/wiki/spaces/SR/pages/3902930955), `.env.dist`.

---

## crawler-hierarchy

**Three-layer abstract hierarchy:**

```
CrawlerAbstract                       — base: HTTP retry, cache, classifiers
└── VehicleAdCrawlerAbstract          — vehicle ads: brands/models, parseVehicle, ad fields
    ├── HtmlAdVehicleCrawlerAbstract  — HTML: pagination, listing→detail, hooks
    └── ApiAdVehicleCrawlerAbstract   — API: direct parse, no pagination
```

**File:line refs:**
- `src/crawler/CrawlerAbstract.ts:36` — base class (`fetchRequest` retry loop at line 368, classifiers at 117-138)
- `src/crawler/sites/VehicleAdCrawlerAbstract.ts:35` — vehicle layer
- `src/crawler/sites/HtmlAdVehicleCrawlerAbstract.ts:32` — HTML layer
- `src/crawler/sites/ApiAdVehicleCrawlerAbstract.ts:20` — API layer

**`@CrawlerAlias(SiteKeysEnum.X)` decorator** (`src/crawler/crawler.decorator.ts:17`) — wires per-site config from `CrawlingSites.ts` into the instance: `site`, `baseUrl`, `domain`, `routingKey`, `detailRoutingKey`, `shouldValidateListingVehicle`, `shouldRevisitYesterdaysVehicles`, `isDisabled`, `skipDetailsUrlValidation`.

**Always-required overrides:**
- `getBrandsAndModels(): Promise<ParseVehicleParams[]>` — listing URLs to publish
- `parseVehicleInput(params): AdVehicle` — single ad → vehicle object
- `parseVehicle(params): Promise<ParseVehicleOutput>` — orchestrates the above

**HTML-only overrides:**
- `getVehicleListPageResponse(options): Promise<VehicleListPageResponse>` — parse listing
- `getNextPageUrl(params): string | undefined` — pagination
- `beforeParseVehicle(params, opts): Promise<boolean>` — pre-detail hook (return false to skip)
- `afterParseVehicle(output): Promise<ParseVehicleOutput>` — post-detail hook

**Anti-bot overrides** (run inside the retry loop — thrown errors ESCAPE!):
- `isResponseNotFound({ response, responseBody }): boolean`
- `isResponseRateLimited({ response, responseBody }): boolean`
- `isResponseForbidden({ response, responseBody }): boolean`
- `isServerError({ response, responseBody }): boolean`

**URL-change overrides:**
- `fetchRequest()` — full request override (rare; CarGr does this for scrape.do)
- `getFetchRequestOptionsForDetailsUrlValidation()` — different fetch behavior for details validation only (autovit-ro: `followRedirect: false`)
- `buildVehicleWorkingUrl()` / `buildLegacyUrl()` — URL change handling

**Site-config knobs** in `src/shared/const/CrawlingSites.ts`:
- `url` — base URL (required)
- `routingKey` — override default queue routing (e.g. `MS_AUTOSCOUT_LISTING_URLS_TO_FETCH`)
- `shouldValidateListingVehicle` — enable SVL gate
- `shouldRevisitYesterdaysVehicles` — re-crawl yesterday's URLs
- `isDisabled` — silent skip
- `skipDetailsUrlValidation` — skip detail URL validation cron
- `runOnNthDays` + `matchingDay` — N-day cycle
- `isCrawlingVehiclesWithoutPrice` — accept price-less listings

**Source:** `src/crawler/CrawlerAbstract.ts`, `src/crawler/sites/*.ts`, `src/shared/const/CrawlingSites.ts`.

---

## pipeline

**End-to-end vehicle flow (parse → S3 → ES):**

1. **Crawler publishes listing URL** to `MS_*_LISTING_URLS_TO_FETCH` via `crawler.service.ts:285` (`producerRmq` → `MS_EX_CRAWLING` exchange, `routingKey` from site config).
2. **Listing consumer** (`crawler.consumer.ts`, channel `MS_RECEIVE_CRAWL_JOBS`, prefetch=1) parses the listing page → emits `VehicleListItem[]`.
3. **SVL gate** (`bulk-save-listing-vehicle.service.ts:45,115`) — for each `VehicleListItem`:
   - Pass (listing matches S3-stored vehicle) → routes to `MS_BULK_SAVE_VEHICLES` (skip details).
   - Fail → re-publishes to `MS_GENERAL_LISTING_URLS_TO_FETCH` for detail visit.
4. **Detail consumer** parses the detail page → publishes vehicle to `MS_BULK_SAVE_VEHICLES`.
5. **Bulk-save consumer** (`bulk-save-worker.consumer.ts:40`, prefetch 600/800/1000 by queue size) → `bulk-save-worker.service.ts:63` (`saveVehiclesToStorage`):
   - Line 67 — group messages by URL.
   - Line 70-81 — upsert to MySQL `active_vehicles`.
   - Line 84 — `store-vehicle.service.ts:106` (`saveVehiclesToS3`) — dedup by URL, recalculate history, write to S3 store bucket.
   - Line 94-109 — route to DataAPI mapping (if `shouldBeMapped`) or directly to data-index save.
6. **Mapping completion** — `store-vehicle.service.ts:791-838` updates S3 vehicle with `mappedValues` + `mlConfidence`.
7. **ES indexing** — `vehicle-aggregate.service.ts:44` (`createSearchVehicleFromPrefix`) generates documents → bulk indexes to OLD search index + Data index.
8. **Progressive validation** — `store-vehicle.service.ts:640-713` (`checkChangedValuesInLastHistory`) compares against history thresholds → logs `LoggingContexts.VALIDATION_PROGRESSIVE` (vehicle still saved). Hard validation in `data-vehicle-validation.ts:28` may SKIP_SAVING or REASSIGN_NULL.

**Dedup within run** — `store-vehicle.service.ts:770-776` groups vehicles by URL into a `Map`, single write per URL.

**Source:** `src/bulk-save-worker/`, `src/vehicle/`, `src/validation/`.

---

## queue-routing

**Source files:** `src/shared/const/RmqQueues.ts`, `RmqBindings.ts`, `RmqChannels.ts`.

**Two RMQ vhosts** (`src/queue/rmq/const/RmqConnectionConsts.ts`):
- **MS** (`RMQ_VIRTUAL_HOST_MS`) — all crawling + bulk-save
- **DATA** (`RMQ_VIRTUAL_HOST_DATA`) — only `AMS_REQUEST` + `AMS_RESPONSE` (DataAPI mapping)

**Listing URL queues** (one per region/protocol/special-case):
| Queue | Binding | Notes |
|-------|---------|-------|
| `MS_GENERAL_LISTING_URLS_TO_FETCH` | `crawl.general.#` | Default for small/medium sites |
| `MS_AUTOSCOUT_LISTING_URLS_TO_FETCH` | `crawl.de.autoscout` | Big site, isolated |
| `MS_MOBILE_LISTING_URLS_TO_FETCH` | `crawl.de.mobile` | Big site, isolated |
| `MS_LACENTRALE_LISTING_URLS_TO_FETCH` | `crawl.lacentrale` | Anti-bot heavy |
| `MS_LEBONCOIN_LISTING_URLS_TO_FETCH` | `crawl.leboncoin` | DataDome+Akamai, 2.5h timeout |
| `MS_BROWSER_CRAWLERS_LISTING_URLS_TO_FETCH` | `crawl.browser_crawlers.#` | Puppeteer sites (subito, olx-ro) |
| `MS_LIMITED_CONSUMERS_LISTING_URLS_TO_FETCH` | `crawl.limited.#` | otomoto (CloudFront-heavy isolation) |
| `MS_HUNGARY_LISTING_URLS_TO_FETCH` | `crawl.hungary.#` | mobile-bg + hasznalt-auto, max 6 consumers |
| `MS_CROATIA_LISTING_URLS_TO_FETCH` | `crawl.croatia.#` | HR sites |
| `MS_SLOVENIA_LISTING_URLS_TO_FETCH` | `crawl.slovenia.#` | SI sites (avto-net) |
| `MS_POLAND_LISTING_URLS_TO_FETCH` | `crawl.poland.#` | PL sites |
| `MS_ROMANIA_LISTING_URLS_TO_FETCH` | `crawl.romania.#` | RO sites |
| `MS_WEEKLY_LISTING_URLS_TO_FETCH` | `crawl.weekly.#` | car-gr only, 2.5h timeout |
| `MS_BUYERS_STOCK_LISTING_URLS_TO_FETCH` | `crawl.buyersstock.#` | gruppo-piccirillo etc. |

**Bulk-save queues** (consumer prefetch tier per channel):
| Queue | Channel | Prefetch | Index |
|-------|---------|----------|-------|
| `MS_BULK_SAVE_VEHICLES` | `MS_RECEIVE_BULK_SAVE_JOBS_BIG` | 1000 | OLD search (lowercase props) |
| `MS_BULK_SAVE_SEARCH_VEHICLES` | `BIG` | 1000 | NEW search (PascalCase props) |
| `MS_BULK_SAVE_RAW_VEHICLES` | `MEDIUM` | 800 | Pre-mapping raw vehicles |
| `MS_BULK_SAVE_LISTING_VEHICLE_CHECK` | `SMALL` | 600 | SVL gate |
| `MS_BULK_SAVE_DEACTIVATE_ACTIVE_VEHICLES` | `SMALL` | 600 | Deactivation pipeline |
| `MS_BULK_SAVE_DATA_VEHICLES` | `SMALL` | 600 | Data index writes |
| `MS_BULK_SAVE_DELETE_DATA_VEHICLES` | `SMALL` | 600 | Data index deletes |
| `MS_BULK_SAVE_RAW_DEALERS` | `BIG` | 1000 | Raw dealers ES |
| `MS_BULK_SAVE_DEALERS` | `BIG` | 1000 | Processed dealers MySQL |

**ACK/NACK semantics:**
- **Single-consumer** (`RmqSingleConsumer.ts:53`): NACK with `requeue: !message.fields.redelivered`. First fail → requeue. Second fail → DL.
- **Bulk-consumer** (`RmqBulkConsumer.ts:127-135`): per-message ACK/NACK after batch. Timeout 10s (`RmqBulkConsumer.ts:145`).
- **Crawler retry** (`crawler.service.ts:77-119`): tracks `message.data.retryNr`. Re-publishes to same queue on transient HTTP fail. After `maxRetries` exceeded: logs `"Too many retries for message, discarding it"` and silently drops (no explicit DL push from app code — broker config handles it).

**Routing per site** — each `CrawlingSites[site]` entry has optional `routingKey: RmqBindings`. If unset, defaults via `SiteHelper.getRoutingKey(site)`. Decorator `@ConsumeRMQ` on consumer methods binds to a specific queue name with prefetch + maxConsumers (`MS_MAX_1` to `MS_MAX_6`).

**Source:** `src/shared/const/Rmq*.ts`, `src/queue/rmq/`.

---

## app-modes-detail

**`APPLICATION_MODE` env var** selects which NestJS modules + RMQ channels load.

**Module filter** (`src/queue/rmq/rmq.module.ts:42`):
```ts
if (process.env.APPLICATION_MODE && process.env.APPLICATION_MODE !== applicationMode) {
    continue;  // Skip consumers not matching the current mode
}
```

**Port mapping** (`src/main.ts:44`):
- `SEARCH_API` → 4000
- `BULK_SAVER` → 3001
- `WORKER` or unset → 3000

**RMQ channel setup** (`src/queue/rmq/rmq.module.ts:63-74`):
- WORKER/unset opens: `MS_SEND_CRAWL_JOBS`, `MS_SEND_BULK_SAVE_JOBS`, `MS_SEND_UNIQUE_VEHICLE_URLS`
- BULK_SAVER/unset opens: `DATA_SEND_JOBS`
- SEARCH_API: no send channels (read-only)

**No internal cron.** Every "scheduled" job is an HTTP POST endpoint triggered by an external scheduler (Kubernetes CronJob / external runner). To find what runs when, look at the external scheduler config — not this codebase.

**Endpoints commonly cron-triggered** (none have `@Cron` in this code):
- `POST /market-study/crawl-brands-and-models` — trigger crawler (lock-protected)
- `POST /active-vehicle/cache-active-vehicles` — sync ES → MySQL active_vehicles
- `POST /active-vehicle/get-and-update-expired-vehicles` — deactivation pipeline
- `POST /data-vehicle-es-index/delete-deactivated-vehicles` — clean Data index
- `POST /reporting/send-*` — 8 alert-email endpoints
- `POST /market-study/revisit-yesterdays-vehicles` — opt-in re-crawl
- `POST /data-restore/import-from-old-es-to-s3` — migration

**Source:** `src/app.module.ts`, `src/main.ts`, `src/queue/rmq/rmq.module.ts`.

---

## reporting-endpoints

**8 alert-email endpoints** in `src/reporting/reporting.controller.ts`:

| Endpoint | Purpose |
|----------|---------|
| `send-number-of-crawled-vehicles-comparison` | Today vs yesterday count diff per site → email if > threshold |
| `send-listings-sent-to-all-queues-check` | Validate all listings reached bulk-save |
| `send-crawling-not-finished-check` | Detect crawling hangs |
| `send-queues-not-empty-check` | Backlog detection (12:00 noon check) |
| `send-validation-changes-check` | Validation logic-change report |
| `send-details-url-validation-failed-check` | Detail URL validation failure alert |
| `send-failed-data-vehicles-validation-report` | Vehicles failing field validation |
| `send-url-change-detection-check` | URL structure change per site |

**Thresholds:**
- `src/reporting/const/SiteThresholds.ts` — % diff tolerance per site. `0.1` (10%) for high-volume (autoscout, mobile, leboncoin); `0.2` (20%) for low-volume.
- `src/reporting/DataVehicleValidationThresholds.ts` — global default 20% failed records; field-level: price/mileage 10%, batteryRange 2.5%, batteryCapacity 5%.

**`isDisabled` sites are still in alert lists** — false-alarm risk. Cross-check `CrawlingSites.ts` if a site flagged "0 vehicles" was actually disabled.

**Source:** `src/reporting/`, `references/foundational.md § Alert / reporting infrastructure`.

---

## search-api-endpoints

**Read-only endpoints in `src/search/search.controller.ts`** (SEARCH_API mode, port 4000):
- `vehicles-history-by-vin-numbers` — vehicle history aggregated by VIN
- `get-stock-data` — vehicle aggregations by filters/date/granularity
- `get-available-brands` — brands available per filter
- `get-avg-sell-days` — avg time-on-market per brand/model
- `get-cheapest-data-vehicles-by-country-and-site` — cheapest from data index (rent-a-car)
- `get-cheapest-data-vehicles-range-by-country-and-site` — price range agg

**Dealer endpoints — separate module** at `src/dealer/dealer.controller.ts`:
- `get-all-dealers` — all raw dealer data for a site
- `get-all-vehicles-from-dealer` — vehicles from one dealer
- `get-all-vehicles-from-dealers` — vehicles from many dealers
- `cache-top-dealers` — cache frequently-selling dealers (lock-protected)
- `get-dealers`, `get-dealer-vehicles`, `get-best-selling-brands-and-models` — DCM dealer card endpoints

**Storage layout:**
- Dealer metadata: MySQL (`DealerBranchRepository`, `BrandRepository`)
- Raw dealer records: ES (`ElasticSearchEntitiesEnum.RAW_DEALER`)
- Bulk save publishes to `MS_BULK_SAVE_RAW_DEALERS`

**Source:** `src/search/`, `src/dealer/`.

---

## data-fix-restore

**`src/data-fix/data-fix.controller.ts`** — repair endpoints (lock-protected):
- `fix-active-to` — corrects vehicles missing `activeTo` on first crawl (MAR-816)
- `fix-s3-url-sid` — strips session IDs from S3 URLs, dedups (MAR-851)
- `fix-s3-history` — rebuilds S3 history for given URLs

**`src/data-restore/data-restore.controller.ts`**:
- `import-from-old-es-to-s3` — migrate vehicle data from legacy ES → S3, async tasks queued

**Both modules require WORKER or unset mode** (BULK_SAVER doesn't load them).

**Source:** `src/data-fix/`, `src/data-restore/`.

---

## error-handling

**Three tiers — never mix.**

**Tier 1: Retry (request-level transient errors)** — happens inside `CrawlerAbstract.fetchRequest()` retry loop (`src/crawler/CrawlerAbstract.ts:368-450`). Up to `retryHttpRequestsCount` retries with exponential backoff. Override `isResponseRateLimited` / `isResponseForbidden` / `isServerError` to participate. **Errors thrown from these classifiers ESCAPE the retry loop** — almost never what you want.

**Tier 2: Skip-and-continue (vehicle-level non-retryable)** — 404, 410, missing-field. `return` from the parser, log via `LoggingContexts.PARSER_DEBUGGING`, never throw. Listing keeps processing other vehicles.

**Tier 3: Throw to RMQ DL (process-level — system genuinely broken)** — `HttpRequestFailedError` after retries exhausted; or any unhandled error in the consumer. RMQ NACKs with `requeue: false` on second attempt → dead letter.

**Matea's rule — don't mask errors with truthy defaults.** `getBrandsAndModels()` returning `[]` on error makes the alert system think the site is empty. Throw, let the cron retry (5x).

**Defensive fetch:** `const html = await this.fetchRequest(url) ?? '';` so `cheerio.load()` never receives `undefined`. Pattern #1 in failure-patterns.md is preventable with one `?? ''`.

**Source:** `src/crawler/CrawlerAbstract.ts`, `references/failure-patterns.md`.

---

## logging

**Structured-object first, context second** — every log call:
```ts
this.logger.log({ message: '...', url, site: this.site, /* fields */ }, LoggingContexts.X);
this.logger.warn({ message: '...', url, error: err }, LoggingContexts.X);
this.logger.error({ message: '...', error: err }, LoggingContexts.X);
```

**LoggingContexts enum** (`src/shared/const/LoggingContexts.ts`) — ~54 contexts:
- `FETCH_EXTERNAL` — outgoing HTTP
- `FETCH_S3` — S3 reads/writes
- `CRAWLER_SERVICE` — crawl orchestration
- `ELASTIC_SEARCH_SERVICE` — ES ops
- `RMQ_INFO` / `RMQ_BULK_CONSUMER` — queue info / errors
- `MAILER` — alert emails
- `VALIDATION` / `VALIDATION_PROGRESSIVE` — vehicle validation
- `PARSER_DEBUGGING` — site-parser dev signal
- `LISTING_VEHICLE_CHECK` — SVL gate
- `DATA_MAPPING` — DataAPI bridge
- `VEHICLE_AGGREGATION` — ES indexing

**Picking a context** — reuse existing. New contexts cost ES schema budget (Graylog ES is shared across Preskok projects). See `ams graylog-retention`.

**Field-name reuse** — same principle as contexts. Don't add a new field name (`vehicleId` vs `vehicle_id` vs `id`) when one already exists. Keeps cardinality low and queries stable.

**No `console.log`** — ESLint warns. Always `this.logger`.

**Source:** `src/logger/logger.service.ts`, `src/shared/const/LoggingContexts.ts`.

---

## code-style

**Prettier + ESLint enforced (`npm run lint` auto-fixes most):**

**Prettier** (`.prettierrc`):
- `printWidth: 240`, `tabWidth: 4`, `useTabs: false`
- `singleQuote: true`, `trailingComma: 'all'`, `arrowParens: 'always'`

**ESLint** (`.eslintrc.js`) — non-default rules an LLM commonly violates:
- `@typescript-eslint/explicit-function-return-type: warn` — every function declares return type
- `@typescript-eslint/no-explicit-any: warn` — no `any`
- `simple-import-sort/imports: warn` + `simple-import-sort/exports: warn` — sort imports/exports
- `eqeqeq: warn` — `===` only
- `quotes: ['warn', 'single', { allowTemplateLiterals: true }]`
- `space-before-function-paren: ['error', { asyncArrow: 'always', anonymous: 'never', named: 'never' }]`
- `no-multiple-empty-lines: ['error', { max: 1, maxEOF: 0 }]`
- `no-console: warn`, `no-param-reassign: warn`, `prefer-template: warn`
- `'@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_', ignoreRestSiblings: true }]`
- **`import/prefer-default-export: off`** — default exports actively forbidden; named exports always

**Path aliases (use them, never relative)** — declared in `tsconfig.json`:
```
@root @shared @queue @request @logger @crawler @mapping @database
@config @vehicle @exchange-rate @search @data-fix @dealer @mailer
@reporting @api-clients @test
```

**Custom decorators:**
- `@CrawlerAlias(SiteKey)` — wires crawler config (`src/crawler/crawler.decorator.ts:17`)
- `@ConsumeRMQ` — RMQ queue binding on consumer methods

**Patterns NOT used here:**
- `any`, `// @ts-ignore`, default exports, async logic in constructors, `@Cron`/`@Interval`, `console.log`

**Source:** `.eslintrc.js`, `.prettierrc`, `tsconfig.json`.

---

## test-patterns

**Unit tests** — `**/*.spec.ts` co-located with source.

**Standard setup** uses `TestUtils.mockProviders([...])` from `test/test.utils.ts`:
```ts
const module: TestingModule = await Test.createTestingModule({
    providers: [
        CrawlerService,
        ...TestUtils.mockProviders([RmqService, RmqManager, MailerService, RedisService, S3Service, DealerService, ElasticSearchService, CommonEmailsService]),
        { provide: 'AutoScoutSQS', useValue: jest.fn() },
    ],
    imports: [ConfigModule, LoggerModule],
}).compile();
service = module.get<CrawlerService>(CrawlerService);
```

**Don't roll your own mocks** — `TestUtils.mockProviders` handles `ConfigService` specially (returns empty string from `.get()`). Add new providers to the array, not custom mocks.

**Other helpers:**
- `TestUtils.getDefaultAppSetup()` — full app init for integration tests
- `TestUtils.getTestEnvironmentData()` — merges `.env` + `.env.test`

**E2E tests** — `test/*.e2e-spec.ts`. `npm run test:e2e` clears S3 buckets + purges queues first.

**Jest timeout 60s** — async/crawler tests need it.

**Source:** `test/test.utils.ts`.

---

## data-index-spike-pattern

**Root cause** — any change to the URL field used for `storeId` computation causes the bulk saver to treat the entire site inventory as new vehicles → mass re-index to data index. `storeId = md5(legacyUrl)`. Even changing `null → actual URL` triggers this.

**URL key flip** — the most common cause: a `workingUrl` fix changes which URL form is stored in the listing item's `url` field (e.g. `with ?type=car` → `without ?type=car`). Every existing vehicle gets a new storeId → all re-indexed. Size of spike = full site inventory.

**Null URL silent bug** — if a bug wipes `url` (e.g. `parseVehicleParams.additional = { ... }` replacing the entire object), vehicles are still saved daily with `url: null` and `storeId = md5(null)` — consistent, so no daily spike. The spike happens when the FIX restores real URLs (new storeId for every vehicle).

**Commit time ≠ crawl time** — crawls run ~07:00. A fix committed at 15:00 means: the morning spike is from the broken code being deployed, the fix's side-effect spike appears in the next day's crawl.

**Cumulative multi-site effect** — the MAR-2039 workingUrl migration (2026 Q1-Q2) fixed URL keys for ~15 sites in rapid succession. Each deploy caused a per-site re-index wave. Combined effect: sustained elevated data index write rate for weeks (visible as a climb in April–May 2026 on any 1-year chart).

**Encoding change spike** — fixing response encoding (e.g. `windows-1251` for Bulgarian/Cyrillic) changes what `StringHelper.slugify(brandName)` produces → different brand path in listing URL → different vehicle detail URL → different storeId → re-index for affected brands (mobile-bg March 2026 pattern).

**Deactivation-driven spike (createdAt attribution)** — a partial/failed crawl (site down, proxy issues, incomplete run) followed by the nightly deactivation pipeline produces a Data index spike dated to the *last successful crawl*, not to the deactivation night. Key signals: (1) spike date is 1-2 days before the anomaly date; (2) affected vehicles have round-second `createdAt` (`.000Z` suffix — MySQL DATETIME precision from `lastVisit`), not millisecond (live crawl). Do NOT attribute a one-time spike like this to a broken pagination selector — persistent code bugs produce persistent daily anomalies, not isolated one-time spikes. If the following days look normal without any code fix, the cause is a transient site issue (503, Cloudflare, incomplete run), not broken code.

**Source:** session 2026-05-18 (auto-connect April 1 spike investigation + vozi + mobile-bg analysis).

---

## progressive-validation

The `VALIDATION_PROGRESSIVE` Graylog context with message `"Vehicle has changed too much"` fires when fields differ vs the previously stored value. Logic in [`src/vehicle/store-vehicle.service.ts:639-712`](src/vehicle/store-vehicle.service.ts), field list in [`src/shared/const/ChangedValuesFieldsAndThresholds.ts`](src/shared/const/ChangedValuesFieldsAndThresholds.ts).

**Numeric, threshold-based** (progressive %):
- `price` — 50% under €2,000; 20% €2k–€10k; 10% above €10k
- `mileage` — 50% under 1,000km; 20% 1k–10k; 10% above 10k

**String, always logged on change:** `brand`, `model`, `version`, `engine`, `site`.

**Other, always logged on change:** `engineCapacity`, `bodyType`, `driveTrain`, `fuelType`, `horsePower`, `transmission`, `numberDoors`, `numberSeats`.

**`url`/`workingUrl`/`legacyUrl` are NOT in any list.** A URL change can never trigger this log — and `legacyUrl` change wouldn't anyway (it'd produce a new storeId → fresh doc, no delta).

**Reading the log** — the structured `changes` field is the diagnostic; `full_message` is just the constant `"Vehicle has changed too much"`. Pull `changes` to see which field(s) drove it. Note: Graylog stores `changes` as a flat (non-tokenised) field, so substring search like `changes:DRIVETRAIN` returns 0 — pull the messages and grep client-side.

**One-off migration spike pattern** — when a crawler is rewritten/redeployed and starts populating a previously-null field (e.g. `driveTrain: null → FWD`), every existing active doc fires once on its next visit. Expect a 1–2 day spike at ~size of the active set, then decay to baseline. Eurostocks 2026-05-26 example: 9,815 logs in 24h, ~85% pure `DRIVETRAIN: (OLD: null, NEW: FWD)`.

**Source:** session 2026-05-26.

---

## graylog-prod-access

**URLs (commented in `.env`, uncomment or read with grep):**
- Local (active): `http://graylog.devenv:8090` — NOT reachable for prod/stage log validation
- Stage: `https://graylog3beta.b2b-carmarket.com`
- Prod: `https://graylog3.b2b-carmarket.com`

Tokens for stage and prod live in the matching commented `GRAYLOG_AUTH_TOKEN` lines below each URL in `.env`.

**Auth quirk** — Graylog tokens contain characters that confuse `curl -u "$TOKEN:token"` (curl reads them as a password prompt). Use an explicit Basic Auth header instead:
```bash
AUTH=$(printf "%s:token" "$TOKEN" | base64)
curl -H "Authorization: Basic $AUTH" -H "X-Requested-By: curl" -H 'Content-Type: application/json' \
  -X POST "$GURL/api/views/search/sync?timeout=20000" -d '<query>'
```

**Don't assume Graylog is unreachable** without checking the commented prod URL in `.env` — same pattern as `ELASTIC_SEARCH_URL` (active = local, commented = stage/prod). If a session says "Graylog not reachable from this environment", first verify it actually read both the active and the commented lines.

**Source:** session 2026-05-26.

---

## url-change-alert

**What it is** — automated email `"Urgent: URL change detection signal for N site(s)"` triggered when the **ratio of newly-active vehicles** (data index, `activeFrom` within the last crawl window) exceeds a threshold against total crawled. Format example: `EUROSTOCKS  Vehicles crawled: 30272 | Newly active vehicles: 16563 | ratio: 54.7%  CRITICAL`.

**What it catches** — a site URL-pattern change combined with broken/missing `workingUrl` wiring. Symptom: `legacyUrl` changes for the same physical vehicle → new `storeId` → old doc gets deactivated AND a new doc gets activated in the SAME crawl window. Ratio spikes because half the inventory appears "fresh".

**What it CAN'T distinguish on its own** — a benign re-enablement spike. When a previously-disabled site comes back online, all vehicles deactivated during the disabled period get reactivated together. `activeFrom` is updated to today on reactivation (this is real, observed: storeIds preserved, but `activeFrom` reset). Ratio looks identical to a workingUrl break: 50%+ newly-active.

**Diagnostic to tell them apart — paired-deactivation count in the SAME window:**

| Signal | workingUrl break | Re-enablement spike |
|---|---|---|
| Newly-active ratio | High (50%+) | High (50%+) |
| Inactive-deactivated-in-same-window with same VehicleId as a newly-active | **HIGH — one paired inactive per new active** | **0 or near-0** (old deactivations happened weeks/months ago during disabled period) |
| Multiple docs per VehicleId | **YES** — old storeId inactive + new storeId active | **NO** — one doc per VehicleId, same storeId before and after |

Query for the diagnostic (replace `<SITE>`):
```bash
# Newly-active in last 48h
curl -s "$ES/market-study-vehicle-data_rollover/_count" -H 'Content-Type: application/json' \
  -d '{"query":{"bool":{"must":[{"term":{"site":"<SITE>"}},{"range":{"activeFrom":{"gte":"now-2d/d"}}}],"must_not":[{"exists":{"field":"activeTo"}}]}}}'
# Inactive-deactivated in last 48h (the paired-deactivation count)
curl -s "$ES/market-study-vehicle-data_rollover/_count" -H 'Content-Type: application/json' \
  -d '{"query":{"bool":{"must":[{"term":{"site":"<SITE>"}},{"range":{"activeTo":{"gte":"now-2d/d"}}}]}}}'
```
If the second count ≈ the first → workingUrl break. If the second is near-0 → re-enable spike. Eurostocks 2026-05-26: 16,563 newly-active + 0 paired-deactivated → re-enable spike, not a bug.

**What it misses entirely** — slow URL drift. A workingUrl misconfig that re-storeIds 1–2% of docs per day stays under threshold but silently degrades the index over months. Run W1-W5 from the crawler-data-validation skill periodically as a complement.

**Possible alert improvement** (not implemented as of 2026-05-26) — add the paired-deactivation count to the report. Promote to CRITICAL only when paired count is non-zero; otherwise downgrade to INFO ("benign re-enable spike"). Saves on-call attention.

**Source:** session 2026-05-26 (eurostocks re-enable on develop produced 54.7% ratio; verified benign via 0 paired deactivations).

---

## browser-timeout-logs

**Chromium `net::ERR_*` strings are NOT in Graylog** — Puppeteer-based crawlers wrap any Chromium navigation failure (`ERR_TUNNEL_CONNECTION_FAILED`, `ERR_CONNECTION_RESET`, `ERR_PROXY_CONNECTION_FAILED`, etc.) into a single generic log: `message:"Browser timeout reached"` with `context:FETCH_EXTERNAL`. The raw `net::ERR_*` string lives only in Puppeteer stderr / local dev logs. Searching Graylog for `"TUNNEL"` / `"net::ERR"` returns 0 even during a real outage.

**Correct Graylog query** — `facility:marketstudy AND site:<site> AND "Browser timeout reached"` for the failure count. The log carries `request_id` but **no `specificProxy` field**.

**Correlate to proxy** — join via `request_id` to the preceding `"Starting browser request"` log (same request_id), which DOES carry `specificProxy: http://proxy.b2b.aws:90XX`. Group failures by that field to tell "one proxy down" from "site-wide DataDome pressure":
- Single-proxy outage → 100% of timeouts on one `specificProxy` value.
- Symmetric failure rate (~equal %) across both proxies in the pool → site-side blocking (DataDome / Cloudflare), not a proxy issue.

**Example (avto-net 2026-05-27, PRESKOK_SET_1)** — 60 unique timeout request_ids over 1378 + 1257 browser requests; failure rate 15.1% on `:9007` vs 16.7% on `:9004` → symmetric → site pressure, not proxy outage.

**Source:** session 2026-05-27.

---

## listing-vehicle-check-diagnostic

When investigating `"Listing vehicle check failed in prop"` logs (`context:LISTING_VEHICLE_CHECK`), the **`existingValue` field's presence and shape is the primary diagnostic** for "is this a real listing-vs-detail mismatch or migration noise?":

| `existingValue` shape | Meaning | Diagnostic |
|---|---|---|
| **Missing entirely** | Stored `fullVehicle[prop]` is `null`/`undefined`. `?.toString()` returned undefined, Graylog drops the key. | **Migration noise.** The previously-stored vehicle was written by older code that didn't extract this field at all. Self-heals after the details re-visit populates it. |
| **Empty string `""`** | Stored value was explicitly empty. | Source-side: dealer never filled this field. Parser correctly stored empty; listing now returns a value → genuine drift, worth checking. |
| **Non-empty differing value** | Both versions have a real value, they just don't match. | Real bug or genuine source-side edit. Compare the two values to decide. |

**Per-prop breakdown query** — when LISTING_VEHICLE_CHECK volume spikes, drill into the dominant `prop:` to identify the field. Example query: `message:"Listing vehicle check failed in prop" AND prop:workingUrl` (or `prop:price`, `prop:mileage`, `prop:name`, etc.). The `prop` field is structured and searchable.

**Concrete eurostocks example (2026-05-26 — rewrite migration)** — `prop:workingUrl` SVL fails: 9,026 day-1 → 1,828 day-2, 100% with `existingValue` missing across both days. Root cause: pre-rewrite code never extracted workingUrl; rewrite added it to both listing AND details paths in one commit (against the documented phased rollout in `fix-playbook.md § Implement workingUrl/legacyUrl`). Self-healed within 3 days.

**When to act vs ignore:**
- If `existingValue` missing dominates (≥80%) → migration noise. Expect 1–3 day decay. No action.
- If `existingValue` is mostly non-empty differing → real parser instability. Investigate the field.
- If volume stays elevated past 5 days → not migration; something is genuinely unstable. Check the listing-page extractor for that field.

**Source:** session 2026-05-26 (eurostocks rewrite produced 10,854 workingUrl SVL fails over 48h with 100% `existingValue` missing).

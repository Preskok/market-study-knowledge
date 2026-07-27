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

**legacyUrl vs workingUrl** — `legacyUrl` = stable key for `storeId`/S3/dedup; `workingUrl` = current accessible URL. ES `url` = workingUrl if set, else legacyUrl - **but this swap only actually happens for the Data index** (`ConfigKeys.ELASTIC_SEARCH_VEHICLE_DATA` = `market-study-vehicle-data_rollover`, built via `SearchVehicleService.createDataAdVehicle`/`createSearchVehicle`, `url: vehicle.workingUrl ?? vehicle.url`). The Old search index (`ConfigKeys.ELASTIC_SEARCH_INDEX` = `marketstudy_search_rollover`) is written by a *different* mapper (`vehicleToEsVehicle()` via `CrawlerMessagesRoutingService.saveVehiclesToOldIndex`) that always uses the legacy `url`, by design - it has no `workingUrl` concept at all (consistent with "New search index frozen" above: nothing writes the working-preferring value there anymore). **So: checking `marketstudy_search_rollover`'s `url` field to verify a workingUrl/legacyUrl fix always shows legacy and will look like a false failure - verify against the Data index (`market-study-vehicle-data_rollover`) or S3 (`vehicle.workingUrl` field) instead.** Confirmed live via polovni-automobili MAR-2126 test (2026-07-30): S3 record and Data index both correctly had the working (pretty, real-slug) url; `marketstudy_search_rollover` showed the legacy `/oglas` form on the same vehicle, as expected.

**Field naming convention** — Old search index (`marketstudy_search_rollover`) uses **mixed case**: top-level fields are PascalCase (`CreatedAt`, `Site`, `URL`, `Brand`, `Model`, `Price`), but nested object subfields keep their original casing. Date field for "when crawled" = `CreatedAt` (no `activeFrom` in old search index). Confirmed from live prod sample 2026-05-15.

**`Description` lives in the old search index** (PascalCase `Description` alongside `Site`/`URL`) — NOT in a separate vehicle-data sibling. Coverage is partial and dealer-dependent (typical site: 60–85% of active docs populated; eurostocks 79.5% confirmed 2026-05-26). The other 15–40% are empty because the source dealer didn't fill it on the ad. Always measure with an aggregation across the active set — a 5-doc sample by `CreatedAt desc` often lands on the unpopulated minority and reads as a false bug.

**Persistent vs reset timestamps** — `activeFrom` (Data index, lowercase) is the **ONLY** field that genuinely persists across the entire vehicle lifetime. Both old-index `CreatedAt` and data-index `createdAt` reset on doc rewrite / index rollover. Observed live: same eurostocks doc has `activeFrom: 2022-03-14` but `createdAt: 2026-05-25`. Use `activeFrom` for any "first ever seen" / cross-deploy / cross-era comparison.

**Rollover duplicate inflation** — when a rollover happens mid-week, the same `storeId` can exist in two backing indices (pre-rollover and post-rollover). A `_search` or `_count` query across the alias returns BOTH copies — inflating totals. Symptom: raw doc count is e.g. 1.4×–2× higher than vehicle count on source site. Diagnosis: run a cardinality aggregation on `URL` field — the cardinality result is the true vehicle count; the difference is rollover duplicates. This is expected behaviour, not a crawler bug. Observed: autohaus-landherr 629 total / 442 unique URL in 7-day window vs 444 on site (2026-05-27). The 1.42× ratio matches a mix of 1× and 2× crawl days (midnight fail + 6 AM retry).

**`rawBrand`/`rawModel`/`rawVersion` in Data index** — these fields ARE reliably present. Populated in `createDataAdVehicle()` from `vehicle.brand`/`vehicle.model`/`vehicle.version` (not from `vehicle.rawBrand` — older S3 store records pre-date the raw fields and stored raw values in `brand`). The S3 store record's `.rawBrand` can be `undefined` for old records; the Data index's `rawBrand` is the more reliable source for new records. Only fall back to S3 raw fields when you need the most precise value for slug rebuilding.

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

**Local devenv old index (`marketstudy_search_rollover`) — `URL`/`FuelType`/etc. are mapped as plain `keyword`, not `text` with a `.keyword` subfield.** Querying `URL.keyword` or `storeId.keyword` (the pattern that works on `text` fields) silently returns 0 hits instead of erroring — checked via `_mapping/field/<field>`. `storeId` does not exist as a field in the old index mapping AT ALL (confirmed empty mapping across every backing index) — it's data-index-only, computed downstream in the mapping pipeline, never written to the old index. For the old index, query `URL`/`FuelType` directly (no `.keyword` suffix); for the data index, `storeId`/`url` are also plain `keyword` (no suffix needed there either). Always check `_mapping/field/<field>` before concluding "not found" when a query returns 0 hits.

**Fetching a doc by exact `_id` when the index is a multi-index alias** (rollover aliases always are) — `GET <alias>/_doc/<id>` errors with `"alias has more than one index associated with it, can't execute a single index op"`. Use `POST <alias>/_search {"query":{"ids":{"values":["<id>"]}}}` instead, which works across all backing indices transparently.

**Prod Elastic Cloud endpoint silently fails with embedded URL credentials.** `curl "https://user:pass@<prod-es-endpoint>/..."` returns an empty body (no error, no JSON — `JSONDecodeError: Expecting value` on parse) even though the same request with `curl -u "user:pass" "https://<prod-es-endpoint>/..."` (no embedded creds in the URL, `-u` flag instead) succeeds with HTTP 200. Stage's ES accepts embedded URL credentials fine — this is specific to the prod Elastic Cloud endpoint. Always use `-u` for prod ES curl calls, and if you ever get an unexplained empty response from prod ES, check auth style before assuming the query itself is wrong. (Endpoint hostnames are session-private, not documented here.)

**Source:** `session 2026-05-15`, `src/shared/const/CountryInfo.ts`, `src/shared/const/CrawlingSites.ts`; ES field-mapping gotchas from session 2026-07-08; prod Elastic Cloud auth gotcha from session 2026-07-13 (polovni-automobili storeId verification).

---

## deactivation-pipeline

**Schedule** — starts nightly at **22:00**.

**Volume** — ~250k/day average; peak ~2M (leboncoin days); safe threshold ~900k (above this, slows significantly).

**Behavior** — multisearch before indexing; flag `bulk_save_search_vehicles` request_ids; on timeout retry once → `MS_BULK_DL`.

**`createdAt = lastVisit` during deactivation** — when a vehicle is deactivated, the code sets `vehicle.createdAt = vehicle.activeTo = data.lastVisit` (round-second from MySQL DATETIME). This is intentional: `createdAt` is a "state-as-of" timestamp — the deactivated state became valid at the last-crawl time, not at 22:00 deactivation run time. Before updating, the code pushes a history delta `{createdAt: [old_createdAt, lastVisit]}`. Special case: if `vehicle.createdAt >= newActiveTo`, uses existing `createdAt` (1-day-active vehicle — no meaningful history change). **Kibana attribution consequence:** all deactivation writes appear under `lastVisit` date, not the deactivation run date. A failed Saturday crawl (57k found instead of 103k) → Sunday night deactivation → ~47k Data index writes appear under Friday in Kibana (last time those vehicles were seen). `src/vehicle/store-vehicle.service.ts:154–176`.

**Manual lock** — can lock a specific site to prevent deactivation tonight. Used during hotfixes when crawl is broken but we don't want mass-deactivation.

**Per-site auto-lock (Redis, MAR-2102)** — `DEACTIVATION_PREVENTED_SITES` key holds a JSON map of `site → { timestamp, reason }`, written with `TimeEnum.ONE_YEAR_IN_SECONDS` TTL so it never expires naturally. Populated by `check-and-prevent-deactivation` cron at **21:30** (before 22:00 deactivation) via `checkAndPreventDeactivationBySite`. Unlock is manual via `unlock-site-deactivation` endpoint; manual lock via `lock-site-deactivation` (also sends an alert email). Already-locked sites are excluded from the ratio query, so a lock can never be silently lost by a config change.

**Ratio query (2-bucket)** — `getVehicleVisitCountsBySite` groups `vehicle_visit` per site into `todayCount` = `SUM(DATE(lastVisit)=CURDATE())` and `prevCount` = `SUM(DATE(lastVisit)<CURDATE())`. ratio = `prevCount / (prevCount + todayCount)` — high ratio = many previously-seen vehicles not re-crawled today (would be deactivated tonight). nth-day crawlers only evaluated on their scheduled day (`SiteHelper.shouldSiteRunToday`).

**Thresholds** — resolved by `getSiteThreshold(site)` in priority order: (1) `DeactivationPreventionThresholds.perSite[site]` explicit override; (2) `largeSite`/`smallSite` × `daily`/`nthDay` group from `DeactivationPreventionThresholds` const, where site size = `SiteThresholds[site]` (0.1=large→0.2/0.3, 0.2=small→0.5/0.6) and crawl frequency from live `CrawlingSites.runOnNthDays`. All `AvailableAdSiteKey` sites covered by `SiteThresholds` so no global default fallback needed.

**Manual lock behaviour** — `lock-site-deactivation` is a no-op if site already in Redis (preserves original lock timestamp). Alert email only fires on new locks. `unlock-site-deactivation` removes the entry.

**Email** — only for **newly** locked sites: `⚠️ Alert: N NEW site(s) locked deactivation`. Sent from `reporting.service.sendDeactivationPreventionAlert` (ActiveVehicleModule imports ReportingModule, not MailerModule). Existing-locks reminder email is a future ticket.

**Crawl-pattern-change edge cases** — developer responsibility when changing `runOnNthDays`/`matchingDay`. nth-day→daily on change day: can produce a *false* lock (acceptable — unlock manually) but never a *missed* lock since `shouldSiteRunToday=true`. daily→nth-day handled correctly: prevention check fires on the crawl day; on non-crawl days site is skipped (correct).

**`runOnNthDays` goes stale in `vehicle_visit`** — `insertOrUpdate` orUpdate columns are `['hash','lastVisit','site']` — NOT `runOnNthDays`. Existing rows keep their old value after a crawl-pattern change until re-inserted, so the deactivation interval `IFNULL(runOnNthDays,1)` uses the stale value. Pre-existing; separate ticket.

**Mid-day deploy protocol** — lock deactivation → deploy → rerun crawler (S3 cached responses, no credits) → verify → redeliver DL → unlock.

**`getSiteThreshold()` reuses `SiteThresholds` for an unrelated purpose** — `SiteThresholds[site]` (0.1/0.2) was built to classify sites for the volume-drop-alert email, but `getSiteThreshold()` (`active-vehicle.service.ts:306-314`) also reuses that same large/small classification to pick the deactivation-lock threshold (`largeSite.daily=0.2` vs `smallSite.daily=0.5`). Bumping a site's `SiteThresholds` entry (e.g. after its inventory grows past 2k, to fix a missed drop-alert) silently tightens/loosens its deactivation-lock threshold as a side effect — verify both consequences before changing this const for a site. `DeactivationPreventionThresholds.perSite` exists as an escape hatch (e.g. `AUTOPLIUS` MAR-2110) when the shared large/small bucket doesn't fit a specific site.

**`getVehiclesBeforeDate` / manual `beforeDate` purge semantics** — the query is `DATE_ADD(lastVisit, INTERVAL IFNULL(runOnNthDays,1) DAY) < :beforeDate` (`active-vehicles.repository.ts:58-73`), NOT `lastVisit < beforeDate`. `beforeDate` must clear `lastVisit + crawl-interval`, including time-of-day — for a daily site, a stuck row from `lastVisit=2026-06-11 <any time>` needs `beforeDate >= 2026-06-13` to guarantee a match regardless of hour (using the exact next calendar day, e.g. `2026-06-12`, undershoots by however many hours past midnight the `lastVisit` was). `POST /active-vehicle/get-and-update-expired-vehicles` also has **no per-site filter** — `beforeDate` applies globally across every non-locked site, and any site currently in `DEACTIVATION_PREVENTED_SITES` is silently excluded (must unlock first, or the call does nothing for it). Always run `SELECT site, COUNT(*) FROM vehicle_visit WHERE lastVisit < :beforeDate GROUP BY site` as a pre-flight check to confirm blast radius before firing this in prod.

**Reactivation-backdated `lastVisit` as a distinct lock-loop cause** — separate from the documented `sn-diffusion` stale-URL-migration case: `POST /data-fix/reactivate-vehicles` backdates the reactivated vehicle's `vehicle_visit.lastVisit` to its original `activeTo` (not "today"), by design, so the row "self-heals" only once the crawler actually re-sees that specific vehicle. If the crawler never re-discovers a subset of the reactivated vehicles (e.g. they were genuinely sold and gone, or a coverage gap), those rows stay frozen forever and keep tripping the deactivation-lock on every unlock attempt. Confirmed instance: `brie-des-nations`, 2026-07-13, ~1,219 rows frozen at `lastVisit=2026-06-11` — all sampled ones were confirmed actually sold (browser-checked live site), fixed by a scoped `beforeDate` purge once identified. Diagnostic order that worked: (1) per-site `vehicle_visit` day-by-day `lastVisit` distribution to find the frozen cohort, (2) cross-check ES `Site`/`CreatedAt` `date_histogram` for the same dates to rule out "crawler isn't running" (vehicle_visit and ES are independent write paths and can diverge), (3) the storeId-drift verification method to rule out URL/storeId drift, (4) browser-check a few sample URLs directly on the live site to confirm sold vs still-live before deciding whether to purge or dig into crawler coverage.

**Source:** `references/foundational.md § Deactivation pipeline`; session 2026-06-02 (MAR-2102 PR #21 review); session 2026-07-13 (brie-des-nations lock-loop diagnosis).

---

## rmq-queues

**Per-site queues** — `MS_[SITE]_LISTING_URLS_TO_FETCH` for big sites: autoscout, mobile, leboncoin.

**General** — `MS_GENERAL_LISTING_URLS_TO_FETCH` for small/medium sites.

**Browser crawlers** — `MS_BROWSER_CRAWLERS_LISTING_URLS_TO_FETCH` (puppeteer-based: subito, olx-ro, etc).

**Limited consumers** — `MS_LIMITED_CONSUMERS_LISTING_URLS_TO_FETCH` for **otomoto** (CloudFront-heavy, isolated to not block other sites).

**Weekly** — `MS_WEEKLY_LISTING_URLS_TO_FETCH` for **car-gr only**. Tue start → drains week → Mon 23:25 purge. Not-empty Tue-Sun is normal.

**Hungary** — `MS_HUNGARY_LISTING_URLS_TO_FETCH` shared by mobile-bg (matchingDay 0) + hasznalt-auto (matchingDay 1) + autoscout-ch (matchingDay 1) + promo-neuve (matchingDay 1). Max 6 consumers. Purged 23:25 nightly.

**Hungary queue starvation** — if one site's listing URLs take a long time per message (e.g. ScrapeDo 502 + retries = ~5 min/URL), it can monopolise all 6 consumers for hours and starve co-located sites. Formula: `N_messages × time_per_message / 6 consumers = stall duration`. Example: autoscout-ch 2,160 slow-failing URLs × 5 min / 6 = ~30 hours stall → promo-neuve ↓86% same day (2026-06-29). **Fix: purge the queue and rerun all affected sites.**

**Dead letters** — `MS_DL` (no TTL, manual purge), `MS_BULK_DL` (24h TTL, mostly dedup), `MS_BULK_SAVE_DL` (ES/MySQL connection issues), `MS_TASKS_DL` (long-running task timeout).

**Default timeout** — 30 min. Raised to 2.5h for `MS_WEEKLY_...` (car-gr).

**Source:** `references/foundational.md § Queue architecture`, [RMQ queues Confluence](https://preskok.atlassian.net/wiki/spaces/M/pages/2611314741/RMQ+queues).

---

## crawler-producer-retry

**There is no automatic retry when a site's `getBrandsAndModels()` fails** — whether it throws an exception or returns an empty array, `sendMessagesToRmq()` (`crawler.service.ts:266-317`) treats both identically: logs an error and calls `cacheLogFailingCrawlerOnStart()` (`crawler.service.ts:719-733`), which just pushes the site key into a Redis list `FAILING_CRAWLERS_START` (12h TTL). No re-publish, no re-invocation happens from that call alone.

**The only re-run mechanism is `rerunFailedCrawlers()`** (`crawler.service.ts:702-712`), which reads + clears `FAILING_CRAWLERS_START` and re-triggers `startCrawlingAdSites()`. It is reachable **only** via the manual `POST /rerun-failed-crawlers` endpoint (`crawler.controller.ts:187-191`) — no `@Cron` or other scheduled caller exists in-repo.

**Don't trust an in-code comment claiming "force automatic re-run"** without verifying — several crawlers throw explicitly with that exact comment text, but the throw provides no retry benefit beyond a bare empty return; both are logged identically and both wait for the same manual trigger.

**Source:** session 2026-07-31 (MAR-2039 AutoScout — traced after questioning whether two throw-guards in `getBrandsAndModels()` were still needed).

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

**Comparator mechanics (`VehicleHelper.isPartialVehicleSubsetOfVehicle`, `src/shared/helpers/vehicle.helper.ts`)** — iterates every own-enumerable key of the listing partial and does **strict `!==` equality** against the stored full vehicle (deep `JSON.stringify` comparison for object-typed props like `country`); any single mismatch fails the whole check. **Every key starting with `raw` is skipped entirely** (`prop.startsWith('raw')`) since raw text commonly differs cosmetically between listing and detail markup - only mapped/derived fields (`name`, `price`, `mileage`, `bodyType`, etc.) are actually compared. No fuzzy/substring/normalized matching anywhere - a listing partial's `name` that's a superset of the detail's `name` (e.g. carries an extra seller-added marketing suffix the detail page strips) fails just as hard as a completely wrong value. Free-text fields (`name`/title) are the least safe thing to assert in a listing partial for this reason - a site that decorates listing titles with badges/notes not present on the detail page will generate SVL noise proportional to how often that decoration appears, and there's no way to fix it at the comparator level (shared across all crawlers) - only at the crawler's own listing-partial construction.

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

**Terminology** — Working URL: the details URL that is currently accessible in-browser, is what gets requested, and is saved to ES as `url`. Legacy URL: a details URL that worked in the past and is still used to calculate `storeId` (to avoid creating duplicates).

**Goal** — fix the `url` in ES vehicles (New search + Data index) so the details page stays reachable, without ever changing the URL used to calculate `storeId` (that would create duplicates in S3). **Scope caveat:** only applies to active vehicles going forward from implementation time — already-inactive ads aren't reachable either way, don't try to backfill them.

**How it works** — crawler assigns `workingUrl` on the vehicle only if it exists on the crawled source; if it doesn't exist, nothing is assigned (never defaults to `null` — that would touch every vehicle on sites that don't need this fix). Before saving to ES, `SearchVehicle`/`DataVehicle` construction assigns `workingUrl` to `url` if present, else falls back to `url` (the legacy form) unchanged — so sites without the fix are unaffected.

**What's saved where:**
- legacyUrl → still saved to Old search index as `url` (for storeId stability); used to generate `storeId` (S3 key + Data index `id`)
- workingUrl → saved to S3 as `workingUrl`; saved to ES New search + Data index as `url`

**When to use it** — the details URL changed in a way where both the legacy form and the working form can still be generated in code (i.e. the old identity-bearing part is still derivable from the new URL). See the Autoscout precedent.

**How to use it:**
- **Simple sites / SVL=false (or small sites)** — override `fetchRequest()` to request the working URL instead of the legacy URL; in details parsing assign the working URL as `workingUrl` (leave legacy assignment as `url` unchanged); in listing parsing assign both `workingUrl` and `url` to the partial vehicle/`VehicleListItem` right away.
- **SVL=true + bigger sites** — steps 1-2 (fetchRequest override, details-parsing assignment) are the same, but do **not** add the listing-parsing assignment immediately. First ship details-only assignment to gradually populate `workingUrl` across the existing population (new vehicles + ones that fail the SVL check each day/week). Only once enough of the inventory is covered (site-size and change-rate dependent), add the listing-parsing assignment — doing it too early triggers a mass SVL "change detected" failure for every vehicle that doesn't yet have `workingUrl` set, since listing-parsing assignment on an SVL=true crawler makes every one of those vehicles route into details parsing at once (far more requests than a normal daily crawl).

**Rebuild-from-backup caveats:**
- Vehicles restored from the Old index (covering the gap between backup date and rebuild date) won't have `workingUrl` at all until re-crawled — they'll show the legacy URL as `url` in New search/Data index in the meantime.
- Worse: because Old-index-sourced vehicles have no `workingUrl`, a restore can **overwrite an already-set `workingUrl` in S3** with nothing, not just leave new vehicles unset. Vehicles first crawled after the S3 backup was taken aren't in the S3 backup at all either.

**Reassigning workingUrl to a new value** — if the working URL itself changes again after already being wired up (e.g. the site changes URL format a second time): for an SVL=true + bigger-inventory crawler, **remove the (old) `workingUrl` assignment from listing parsing first**, so the new value re-populates gradually via details parsing again — exactly the same phased approach as the initial rollout above, not a straight flip in listing parsing (same mass-SVL-failure risk as skipping the phased rollout the first time).

**Source:** [Working URL fix (Confluence)](https://preskok.atlassian.net/wiki/spaces/M/pages/3002302476/Working+URL+fix) (full page content provided by user, session 2026-07-10), `references/foundational.md § workingUrl / legacyUrl`.

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

**Matea Lenček** — lead, often deploys prod.

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
AWS_PROFILE=<prod-profile> aws s3 cp s3://$AWS_S3_BUCKET_DAILY_CACHE/[YYYYMMDD]/[md5] ./
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
AWS_PROFILE=<prod-profile> aws s3 cp s3://$AWS_S3_BUCKET_DAILY_CACHE/YYYYMMDD/<hash> - | head -c 500
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

## get-cheapest-vehicles-search-quirks

**V1 vs V2 endpoint differences** — both live in `data-vehicle-search.service.ts` but diverge meaningfully: V1's `fuelType` is a single `FuelTypeEnum` (strict `term` match); V2's is `Array<FuelTypeEnum>` (`terms`/OR match, auto-wraps a bare string via `@Transform`). V2 hardcodes a bottom price floor (`v2MinPrice = 1500`) to exclude undetected leasing/damaged vehicles — V1 has no such floor. V2 always appends `onlyDealers: true` to the generated `vehicleListUrl` (dealer-only link) regardless of request body — this affects only the **display URL**, never the ES result set (no dealer/private-seller filter exists in `buildEsFilters()` at all).

**ES query leniency for `driveTrain`/`horsePower`/`engineCapacity`** — `buildEsFilters()` wraps these three fields in `should: [exact-match, field-missing]` (not a strict `term`/`range`), so a vehicle with an unknown/untagged value for any of them still counts as a match. This means the ES-reported count for e.g. `driveTrain: "AWD"` is often **higher** than what the destination site's own (strict) filter shows when you click through the generated `vehicleListUrl` — not a bug, working as designed to avoid false negatives from incomplete crawl data. `engineCapacity` is additionally excluded entirely from ES filtering in V2's `getCheapestDataVehiclesRangesByCountryAndSiteV2` (commented out per ticket MAR-1741) — it still affects the generated listing URL (via `structuredClone(body)`) but never filters the ES result set.

**`mlConfidence` thresholds can silently zero out real matches** — `fullConfidence`/`brandConfidence`/`modelConfidence` in the request body become strict ES range filters (`mlConfidence.<field> >= value`). A legitimately-matching vehicle can have very low `modelConfidence` (e.g. ~0.48 for Otomoto Audi A4 — a real, systemic value across many docs, not a fluke) and get excluded even though brand/fuel/etc. all match. When a query returns fewer results than expected, check the actual `mlConfidence` values on known-matching docs before assuming a filter/formatter bug.

**Sort is always price-ascending, no alternative exists** — neither `DataVehiclesSearchRangeParamsDto` nor `DataVehiclesSearchV2ParamsDto` exposes a sort field, and every site's `AdSitesUrlFormattingConfig.sortParams` only defines a `price.asc` key. `FormatterService.formatListingUrl()` defaults `sortBy='price', order='asc'` and the one call site never overrides it. Requesting any other sort would throw `"Error: Selected sorting option is not implemented"` — but nothing in the current codebase can trigger that path.

**`brand`/`model` term filters are case-sensitive** — ES stores them as e.g. `"A4"` (capitalized); a request with `model: "a4"` (lowercase) matches zero documents, not a partial/case-insensitive match. Always verify exact stored casing (`_search` with a `match` query, or check a known sample doc) before assuming a brand/model filter is broken.

**Every response is Redis-cached by exact request-body hash — retesting can lie** — `ElasticSearchService.cachedSearch()` (`elastic-search.service.ts:152`) caches the full ES response in Redis, keyed by `CommonHelper.getObjectHash(esRequest)` (content hash of the built query), TTL = `REDIS_EXPIRATION` (21600s/6h locally). This covers V1 and V2 of `get-cheapest-data-vehicles-*`. If you test a request body while a real bug produces 0 results, then fix the bug and retest the *identical* body, you get the stale cached 0 back — indistinguishable from the bug still existing. Confirm cache vs. real bug by nudging any harmless field (e.g. `mileage.max += 1`) to force a fresh cache key; if the result changes, it was cache. Local Redis (`REDIS_HOST=redis.devenv`, `REDIS_DATABASE_NUMBER=15`) is safe to flush entirely when small (`node -e 'require("redis").createClient({host:"redis.devenv",port:6379,db:15}).on("connect",function(){this.flushdb(()=>this.quit())})'`).

**Source:** session 2026-07-02 (MAR-2121 Otomoto formatter work + live V1/V2 comparison debugging); caching gotcha added 2026-07-03.

---

## data-fix-restore

**`src/data-fix/data-fix.controller.ts`** — repair endpoints (lock-protected):
- `fix-active-to` — corrects vehicles missing `activeTo` on first crawl (MAR-816)
- `fix-s3-history` — rebuilds S3 history for given URLs
- `update-vehicle-urls` — migrates old/legacy-format URLs to clean URLs in S3 + Data ES, merges histories if a clean-URL record already exists, and (as of MAR-1975, session 2026-07-21/22) keeps MySQL `vehicle_visit` in sync so migrated active vehicles don't become "zombies" that never expire. Service: `src/data-fix/remove-sid-from-s3-fix/update-vehicle-urls.service.ts`, class `UpdateVehicleUrlsService` — **confirmed to exist and be the live class as of session 2026-07-21/22; grep for it directly rather than trusting any older note in this file that says otherwise, this doc has been wrong about this before.**
- `cleanUrl()` per-site coverage as of 2026-07-22: Car4You, HasznaltAuto, AutoIes, Starterre, ClubAuto, GarageChambon, **Otomoto** (rebuilds `brand-model-ID....html` short slug from `rawBrand`/`rawModel`, or `rawVersion` for `/dostawcze/` commercial listings which legitimately keep more hyphens in the slug — don't mistake a long `/dostawcze/` slug for "still dirty", check the URL prefix first). Adding a new site means writing a new `cleanUrl()` case and wiring it into the `cleanUrl(url, site)` switch in `update-vehicle-urls.service.ts`.
- `delete-wrong-url-vehicles` — deletes vehicles with wrong URLs from S3 + Data ES (MAR-1976, car-gr + auto-zeilinger). Supports `dryRun: true` preview mode.

**`src/data-restore/data-restore.controller.ts`**:
- `import-from-old-es-to-s3` — migrate vehicle data from legacy ES → S3, async tasks queued
- `import-vehicles` / `import-vehicle-visits` — see `export-import-local-testing` section above.

**Both modules require WORKER or unset mode** (BULK_SAVER doesn't load them).

**`update-vehicle-urls` key behaviors (current as of MAR-1975, session 2026-07-22):**
- ES query (`ElasticSearchService.getVehiclesForUrlFixing`) has **three mutually exclusive modes**, selected by `fixActiveOnly`/`includeActiveVehicles` body flags:
  - default (neither flag) — `activeTo` range filter only. Structurally can **only** return already-deactivated vehicles.
  - `fixActiveOnly: true` — ignores `dateFrom`/`dateTo` entirely, matches only currently-active vehicles (`must_not exists(activeTo)`) regardless of date. On a long-lived shared ES cluster this pulls in **all** currently-active docs for the site, not just a recent subset — expect large ambient noise if the cluster has years of accumulated data.
  - `includeActiveVehicles: true` — OR of both above (`activeTo` range for the date window, OR currently-active regardless of date). Same ambient-noise caveat as `fixActiveOnly` for the active-vehicles side.
- **`vehicleVisitTableRowsInsertedCount`/`DeletedCount` will always be 0 in default mode** — since that mode can only return already-deactivated vehicles, and the vehicle_visit sync only fires when the *merged* outcome is active. This is expected, not a bug; don't read 0 here as evidence the sync logic is broken unless you deliberately used `includeActiveVehicles`.
- `recalculateVehiclesHistoryAndWriteToS3` deletes `activeTo` from inputs and recomputes from `createdAt` diffs — always returns vehicles in an "active" state unless `shouldKeepActiveVehicle: false`. In the URL-fix context clean URL records can be deactivated → read `originalActiveTo` from the newest record first, pass `shouldKeepActiveVehicle: !originalActiveTo`, then restore `originalActiveTo` after recalculate if it was set.
- `recalculate` returns `[]` when data is identical even if URLs differ (e.g. only `url` field changed). Force-write fallback: call `writeVehicleToS3` directly and push result into the array so the old URL record still gets deleted.
- `skippedUnsafeToRebuildCount` — `cleanUrl()` returns `null` when it cannot safely rebuild (e.g. Otomoto slug mismatch between rawModel and URL). Safe to ignore; these vehicles keep their old URL.
- Old-S3-record deletion (`removeVehicleByUrl`) silently swallows errors internally and resolves falsy on failure instead of throwing — must explicitly check its return value before proceeding to ES delete / vehicle_visit sync, or you'll orphan the ES doc / never sync visits while thinking the old record is gone. If this delete fails (e.g. AccessDenied from an IAM permission gap), the whole merge should abort *before* touching ES or vehicle_visit — confirmed this exact failure mode on a real stage deployment (session 2026-07-22): stage worker's own AWS creds lacked `s3:DeleteObject`, so every merge created the new record but correctly aborted before cleaning up the old one, rather than leaving a worse half-deleted state.
- **A whole-window recreation event is identifiable via a `createdAt` spike + `activeTo` clustering** (a mass-deactivation batch bumps both fields together for records with wildly different `activeFrom` values) — sample a handful of docs from the spike window and check if their URLs are actually dirty-format before assuming that's where a URL migration happened; some `createdAt` spikes are just routine deactivation batches with already-clean URLs.

**Source:** session 2026-06-08 (MAR-1975 — otomoto URL fix); extended 2026-06-16 (9-case test suite, history-interleave paths); extended 2026-07-21/22 (vehicle_visit sync, dateField-aware export, real-scale stage/local testing, ES `_id` bug, stage IAM permission gap).

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

**Dependency-free services skip the TestingModule ceremony** — a service with no constructor dependencies (e.g. `FormatterService`) is instantiated directly with `new FormatterService()` in specs, no `Test.createTestingModule`/`TestUtils.mockProviders` needed. Check the constructor before reaching for the standard NestJS TestingModule setup.

**`moduleNameMapper` gap** — `package.json`'s Jest config historically only mapped `^src/(.*)$`, missing all the `@root`/`@shared`/`@crawler`/etc. path aliases from `tsconfig.json`. Any spec importing via an alias silently fails with "Cannot find module" until all aliases are added to `moduleNameMapper` to mirror `tsconfig.json`'s `paths`. Check this first if a brand-new spec file can't resolve any aliased import.

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

**URLs:**
- Local (active in `.env`): `http://graylog.devenv:8090` — NOT reachable for prod/stage log validation
- Stage: (hostname session-private, not documented here)
- Prod: (hostname session-private, not documented here)

Stage/prod credential resolution is intentionally not spelled out here — resolve from session context, or ask the user.

**Auth quirk** — Graylog tokens contain characters that confuse `curl -u "$TOKEN:token"` (curl reads them as a password prompt). Use an explicit Basic Auth header instead:
```bash
AUTH=$(printf "%s:token" "$TOKEN" | base64)
curl -H "Authorization: Basic $AUTH" -H "X-Requested-By: curl" -H 'Content-Type: application/json' \
  -X POST "$GURL/api/views/search/sync?timeout=20000" -d '<query>'
```

**Don't assume Graylog is unreachable** without first resolving the prod/stage endpoint properly (session context, not just the active local `.env` line). If a session says "Graylog not reachable from this environment", verify it actually tried the right endpoint before concluding that.

**Don't mistake the stage Graylog instance returning 0 results for "broken/deprecated instance"** — a query scoped to a site that only runs in prod will legitimately return `used_indices: []` / 0 results on stage — that's correct behavior, not evidence the endpoint is non-functional. If prod itself returns `403 Not Authorized`, the prod `GRAYLOG_AUTH_TOKEN` is what's actually broken (expired/invalid) — flag for renewal, don't conclude "Graylog is down" from this combination (session 2026-07-15, e-motors: prod 403 + stage 0-results was misread as "both broken" before realizing stage was just correctly empty).

**Simpler alternative endpoint** — `GET /api/search/universal/relative?query=<url-encoded-lucene>&range=<seconds>&limit=<n>&fields=message` (Basic Auth same as above, still needs the explicit-header workaround, not `-u`) works without building a full search-view payload. **`fields=` is required** — omitting it returns `400 "must not be empty (path = RelativeSearchResource.searchRelativeChunked.arg7, invalidValue = null)"`, which looks like an auth/query error but is just a missing required param. With `fields=` set, the response is **CSV, not JSON** (`"timestamp","message"` header row) — don't `json.load()` it, parse as CSV or just grep the raw text.

**Prod token confirmed dead, not a curl quirk** — retried on 2026-07-16 with both plain `curl -u "$TOKEN:token"` AND the documented Basic Auth header workaround above; both return `403 Not Authorized` on the prod endpoint. This rules out the auth-method quirk as the cause — the token itself needs actual renewal/rotation before prod Graylog is usable again. Don't re-attempt alternate curl auth styles; it's not a syntax problem.

**Source:** session 2026-05-26; corrections added sessions 2026-07-15 and 2026-07-16.

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

**100% ratio = complete URL structure change (expected after crawler rewrite)** — when a site changes its entire tech stack (e.g. Rastetter: Audaris API `/angebote/{brand}/{model}/{id}` → WooCommerce `/produkt/{slug}` in July 2026), the `storeId = md5(legacyUrl)` for every vehicle changes. 100% newly-active ratio is expected and correct — the URL change detection fired as intended. To confirm: (1) check paired-deactivation count ≈ total crawled (old storeIds all going inactive); (2) verify the crawler was recently rewritten with a different URL format; (3) check whether the old URL format can be reconstructed from the new one (if not, no workingUrl fix is possible and the churn is unavoidable). Document in the site's `.md` file.

**What it misses entirely** — slow URL drift. A workingUrl misconfig that re-storeIds 1–2% of docs per day stays under threshold but silently degrades the index over months. Run W1-W5 from the crawler-data-validation skill periodically as a complement.

**Possible alert improvement** (not implemented as of 2026-05-26) — add the paired-deactivation count to the report. Promote to CRITICAL only when paired count is non-zero; otherwise downgrade to INFO ("benign re-enable spike"). Saves on-call attention.

**Source:** session 2026-05-26 (eurostocks re-enable on develop produced 54.7% ratio; verified benign via 0 paired deactivations).

**Identity mechanism behind all of the above** — `storeId = md5(vehicle.url)` where `vehicle.url` is `legacyUrl` (NOT `workingUrl`); confirmed the sole call: `newestVehicle.id = S3Service.generateKey({ key: newestVehicle.url, isPrefixed: false })` (`store-vehicle.service.ts:359`). **There is no VIN or any other secondary/fallback matching anywhere in the persistence pipeline** — `vin` is copied onto the search doc as a passive payload field only (`search-vehicle.service.ts:150`), never used for lookup. Every identity read/write is by URL (hashed) or by the already-computed storeId. So any text change inside `legacyUrl` — not just the domain, but branch/dealer names, slugs, anything — mechanically creates a new vehicle with zero linkage to the old one, no matter how "obviously the same car" a human would judge it.

**S3 bucket key roles** (relevant when assessing blast radius of a legacyUrl change):
| Bucket | Keyed by | Affected by legacyUrl change? |
|---|---|---|
| `AWS_S3_BUCKET_DAILY_CACHE` (daily raw-response cache) | the actual **fetched** URL (workingUrl/API url) via `CrawlerAbstract.ts:201` `cacheKey = \`${url}_${JSON.stringify(options.data)}\`` | No — fetching/caching is unaffected |
| `AWS_S3_BUCKET_STORE_VEHICLE` (parsed vehicle JSON, the identity anchor) | `calculatePrefix(md5(legacyUrl))` | Yes — old objects orphaned, new key written fresh |

**Deactivation is a scheduled MySQL sweep, not immediate or per-crawl** — every successful crawl upserts a `vehicle_visit` row (`lastVisit`, `storeId`) in `bulk-save-worker.service.ts:70-81`. A separately-triggered sweep (`active-vehicle.service.ts:41`, `getAndUpdateExpiredVehicles(beforeDate)`) finds rows with `lastVisit < beforeDate`, publishes `VEHICLE_DEACTIVATION`, deletes the MySQL row. This means a URL-rename event self-heals within roughly 1-2 sweep cycles with **zero manual intervention** — before concluding "we need a service to force-deactivate the old storeIds," check whether it has already resolved itself (query `activeTo` counts per day; if the old-URL docs already show `activeTo` set, it's done).

**`fix-active-to` is NOT a targeted force-deactivate tool** — despite the name, `POST /data-fix/fix-active-to` (`active-to-fix.service.ts:32`) takes only `{ limit }`, no storeId list. It's a one-shot backfill for a historical bug (MAR-816, vehicles that never got an `activeTo` at all) — it finds docs *missing* `activeTo` and republishes them for normal reprocessing. It does not accept a specific storeId list and cannot force-deactivate on demand. There is no existing endpoint that takes an arbitrary storeId list and sets `activeTo` directly — the only way `activeTo` gets set is via the `VEHICLE_DEACTIVATION` message path above.

**New storeId = ML re-mapping from scratch, real cost** — mapping (`mappedValues`/`mlConfidence`) is cached on the S3 doc keyed by storeId, with no text-based (`rawBrand`/`rawModel`/`name`) cache. `shouldBeMapped` is `true` whenever `!history.length` (`store-vehicle.service.ts:605`) — true for every freshly-keyed vehicle. So a legacyUrl-driven storeId churn re-triggers a real Data-API mapping call per vehicle, even though the car and its raw fields are unchanged.

**Diagnostic technique for "is this a rename or a genuine new/relisted vehicle" at scale** — batch ES `_msearch` against the Data index: for every newly-active vehicle, query by `vin` (exact term — **`vin` is mapped `type: keyword` already, there is no `.keyword` subfield; querying `vin.keyword` silently returns 0 matches instead of erroring, easy to misread as "no history"**) filtered to `activeFrom < event_date`, sorted `desc`, size 1, to get the immediate predecessor. Then regex-extract the numeric listing ID and any UUID from both URLs: identical ID+UUID with only text differing = pure rename (fixable by a stable-ID legacyUrl or a branch/slug lookup table); different ID/UUID = genuine re-listing by the source site (not fixable by any URL-based identity scheme — needs VIN-based reconciliation instead, with the caveat that VIN data quality itself should be spot-checked first, some sites/crawler-generations use placeholder/masked VINs reused across unrelated vehicles). Running this across the full affected population (not a sample) via `_msearch` in batches of ~300 is fast enough to get exact percentages rather than estimates.

**"Rename storm" sub-pattern** — distinct from both the pure-migration case (100% ratio, full tech-stack rewrite) and the re-enable spike: a site keeps the same tech stack but does a **company-wide rebrand/relabel rollout** (e.g. renaming dealer/branch names embedded in listing URLs), hitting a large fraction of the catalog on one day with the SAME kind of churn as a URL migration, but restricted to specific text fragments. A single blanket text substitution will not have full coverage — expect roughly half the fixable population to need a slug/branch lookup table instead of a regex, and expect at least one branch/segment to be an unreliable historical catch-all tag (relocations vs. mislabels are indistinguishable in the data) that should be excluded from any automated remap.

---

## browser-timeout-logs

**Chromium `net::ERR_*` strings are NOT in Graylog** — Puppeteer-based crawlers wrap any Chromium navigation failure (`ERR_TUNNEL_CONNECTION_FAILED`, `ERR_CONNECTION_RESET`, `ERR_PROXY_CONNECTION_FAILED`, etc.) into a single generic log: `message:"Browser timeout reached"` with `context:FETCH_EXTERNAL`. The raw `net::ERR_*` string lives only in Puppeteer stderr / local dev logs. Searching Graylog for `"TUNNEL"` / `"net::ERR"` returns 0 even during a real outage.

**Correct Graylog query** — `facility:marketstudy AND site:<site> AND "Browser timeout reached"` for the failure count. The log carries `request_id` but **no `specificProxy` field**.

**Correlate to proxy** — join via `request_id` to the preceding `"Starting browser request"` log (same request_id), which DOES carry a `specificProxy` field identifying the proxy host used. Group failures by that field to tell "one proxy down" from "site-wide DataDome pressure":
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

---

## export-import-local-testing

**Purpose** - seed local/stage ES Data index + S3 store (+ optionally MySQL `vehicle_visit`) with real prod/stage data for realistic data-fix testing, at any scale, without touching prod. Also supports deleting that seeded data back out. Feature lives permanently on `feature/no-ticket-s3-import-and-export` (no longer needs cherry-picking - check it out directly).

**Endpoints (current - vehicle_visit is merged into the vehicles endpoints, no more separate vehicle-visits routes):**
- `POST /export/vehicles` - `{site, dateFrom, dateTo, dateField?, limit?, onlyActive?, includeActiveVehicles?, useActiveFromRange?, includeVehicleVisits?, jobId?}`. Streams ES Data index + S3 store (+ MySQL vehicle_visit unless `includeVehicleVisits: false`) into `tmp/exports/<site>/<jobId>/{es,s3,visits}-NNNNN.ndjson` chunk files (~10k lines each) + a resumable `manifest.json`. Re-run with the same `jobId` to resume. Also returns `staleCrawlWarning` when the site's crawler has been dead 3+ days (see below).
- `dateField` - `'activeFrom'` (default) or `'activeTo'`. Only applies when `includeActiveVehicles` is not set. **Critical**: must match whichever field the *consumer* feature filters on, or the exported population won't overlap with what the feature actually processes.
- `onlyActive: true` - **narrows**: ANDs a no-`activeTo` filter onto the date range (only vehicles both in-range AND still active).
- `includeActiveVehicles: true` - **widens**: ORs a date-range check with "currently active regardless of date." Ported from `update-vehicle-urls`'s identical flag this session. Mutually exclusive with `onlyActive` (`RequiresAndExcludes` validator on the DTO). Ignores `dateField` - see `useActiveFromRange`.
- `useActiveFromRange: boolean` - only meaningful with `includeActiveVehicles: true` (`requires: ['includeActiveVehicles']`, `excludes: ['onlyActive']`). Controls which field the union's date-range side checks: omitted/`false` (default) ranges on `activeTo` - `(activeTo in [dateFrom, dateTo)) OR (no activeTo)`, matching `update-vehicle-urls`'s hardcoded behavior ("deactivated in this window OR still active"); `true` ranges on `activeFrom` instead - `(activeFrom in [dateFrom, dateTo)) OR (no activeTo)` ("went active in this window OR still active" - a genuinely different population, not just a technical substitute).
- `includeVehicleVisits` - defaults to `true` (vehicle_visit always accompanies vehicle inserts by default now, since testing active-vehicle scenarios needs it and it was too easy to forget as a separate step - see the git history around the MAR-1975/2126 branch merge). Pass `false` to skip MySQL entirely.
- `POST /data-restore/import-vehicles` - `{jobDir, includeVehicleVisits?}`. Resumes via `import-manifest.json`, tracking `importedChunkFiles` (now covers `es-`, `s3-`, and `visits-` prefixed chunks together).
- `POST /data-restore/delete-vehicles-by-date-range` - `{site, dateFrom, dateTo, dateField?, onlyActive?}` (site + date range required). `POST /data-restore/delete-vehicles-by-store-ids` - `{storeIds}` (required, non-empty array). Both delete from ES + S3 + MySQL vehicle_visit together, resolving storeIds/urls from the data index first. **NEVER RUN AGAINST PROD** - both throw `ForbiddenException` when `NODE_ENV=production`; treat that as a last-resort backstop, not permission to be careless.

**Job naming convention** - suffix jobIds with a UTC timestamp, `<descriptive-name>-YYYYMMDD-HHmmss` (e.g. `polovni-onlyactive-prod-20260728-041524`), generated with `date -u +%Y%m%d-%H%M%S` at request time. Keeps re-runs of the same scenario distinguishable and sortable by filesystem listing.

**Env-switching cookbook** - `.env` has three commented blocks (LOCAL/STAGE/PROD) for `ELASTIC_SEARCH_URL` and for the whole AWS S3 block; only one active at a time. Always flip **both together** (ES URL and the full S3 block) - flipping only one silently reads from one env and writes to another. `TYPEORM_*` (MySQL) is a **separate** three-block switch, only needed when `includeVehicleVisits` is not explicitly `false`. **Prod MySQL requires an active VPN connection** - without it the app hangs retrying `connect ETIMEDOUT` and never finishes booting (confirmed this session: the server sat retrying indefinitely until VPN was connected, then booted clean on the next restart). After any `.env` change: fully stop and restart the server (`ps aux | grep dist/src/main`, kill if needed, then restart) - `.env` is loaded once at boot, not hot-reloaded.

**Stale crawler detection** - `ElasticSearchService.getSiteLastCrawlDate(site)` aggregates `max(createdAt)` for the site; `ExportVehiclesService` surfaces a `staleCrawlWarning` string on the export response/manifest whenever that date is more than 3 days old. Discovered this session on `polovni-automobili`: its crawler died mid-June 2026 (last `createdAt`/`activeFrom` write: 2026-06-15T04:12Z; daily `activeTo` deactivation count ran ~3000/day through 2026-06-14 then dropped to zero) - every export of that site returned the exact same 77,659-record count regardless of how wide the requested date range was, because there was simply no newer data to find. **A stale-crawler site makes `onlyActive`/`includeActiveVehicles` look "correct" but frozen** - identical counts across different date ranges is the tell, not a query bug. To find the real last window of churn for such a site, run the daily `activeTo` `date_histogram` for the ~2 weeks before `max_createdAt` and use that as the range for a deliberate "capture the tail of real deactivation" export.

**Prevention-of-deactivation caveat** - some vehicles never receive `activeTo` at all regardless of real staleness, due to the "Prevention of vehicle deactivation" feature (https://preskok.atlassian.net/wiki/spaces/M/pages/4349984769/Prevention+of+vehicle+deactivation), which locks certain vehicles in `vehicle_visit` so they don't deactivate. For a site under this lock, `activeTo`-based reasoning about "how recently was this vehicle really active" can be misleading - cross-check `staleCrawlWarning`/`max(createdAt)` rather than trusting `activeTo` absence alone as "genuinely still active."

**Never sort ES pagination on a field that can be missing from matched documents** - `getDataVehiclesPageBySite` used to sort on `[dateField]` (`sort: [{ [dateField]: 'asc' }, { storeId: 'asc' }]`). This broke once `includeActiveVehicles` started matching currently-active documents that lack `activeTo` entirely (when `dateField`/the union's range field was `activeTo`) - sorting/`search_after`-paginating on a field absent from some hits is undefined. Fixed by always sorting on `createdAt` (present on every document regardless of active/deactivated status), matching `update-vehicle-urls`'s `getVehiclesForUrlFixing`, which sorts on `createdAt` for exactly this reason. Any future query mode added here should follow the same rule: sort on a field guaranteed present on every possible match, never on the field being ranged/unioned over.

**Verify "stage" is really stage before writing anything** - an endpoint someone hands you as "the new stage URL" may silently be the *same cluster as prod* if it shares prod's hostname pattern (e.g. same base domain, different port). Before any write, `GET /` (or `curl https://user:pass@host:port/`) on both the candidate endpoint and known-prod, and diff `cluster_uuid` + `cluster_name`. Identical UUID = same cluster, stop immediately.

**Stage S3 write access** - the static AWS key baked into `.env`'s STAGE block is **read-only** at the AWS IAM level for the vehicle-store bucket (confirmed via direct `PutObject`/`DeleteObject` AccessDenied tests) - flipping the app-level `_PERMISSION_WRITE` flag in `.env` does nothing if AWS itself denies it. For real write access, use an AWS SSO profile scoped to that bucket's account: `aws sso login --profile <stage-profile>` then `aws configure export-credentials --profile <stage-profile> --format env` for temporary `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`/`AWS_SESSION_TOKEN`, pasted into `.env`'s S3 block. These expire in a few hours. **The deployed stage worker has its own separate credentials** - a deployed-service AccessDenied is a different, infra-side fix.

**Never re-issue a duplicate call after a client-side timeout** on a long-running export/import/delete call - there's no cancellation-on-disconnect, so the server keeps processing regardless of the client. Re-issuing starts a second concurrent execution racing on the same job dir/manifest, corrupting counters. Instead: poll the manifest file or use Monitor with an until-loop on it.

**localstack instability at scale (local only)** - the local S3 emulator is memory-capped (~1GiB) and can crash-loop under heavy parallel `PutObject` load. No persistent volume means every crash wipes all previously-written local S3 objects back to zero. Mitigations: split a huge export into several smaller job dirs, or use a smaller `limit`. Local-only artifact - real AWS S3 doesn't have this ceiling.

**Chunk-resume manifest doesn't protect against partial in-chunk failure** - a chunk is marked `importedChunkFiles` once its processing loop finishes, regardless of individual item failures. A naive re-run skips it and silently leaves failed items unfixed. Fix: manually edit `import-manifest.json`, remove the falsely-marked chunk filename(s), reset the relevant counters to 0, then re-run.

**Bulk ES import must set `_id` explicitly** - `bulkIndexToDataIndex` must pass `_id: doc.storeId` on the bulk `index` action, or every storeId-keyed lookup/delete breaks silently later with 404s that look unrelated.

**Cleanup convention** - after a testing round, use the delete-vehicles endpoints (not hand-rolled queries) to wipe imported test data from local/stage ES + S3 + MySQL. **Never delete the raw exported NDJSON chunk files** (`tmp/exports/<site>/<jobId>/`) - expensive to regenerate from prod, fully reusable for re-importing after a wipe.

**Check export/import/delete completion** - HTTP clients often time out (2min) on large operations; the server keeps running. Poll `manifest.json`/`import-manifest.json` for progress, or grep Graylog for the operation's final log line.

**2026-07-29 perf-optimization measurement (polovni-automobili, onlyActive, prod read-only)** - baseline (2026-07-28, pre-optimization): 4m06s wall clock, 612MB peak RSS, 77,659/77,659/77,659 (es/s3/visits), `missingS3Count: 0`. After Tasks 1-5 (worker-pool pipelining + prefetch, concurrent vehicle_visit phase, `esPageSize` default 5000→1000, opt-in gzip), four runs against prod, all with identical record counts and `missingS3Count: 0` (correctness fully preserved), varying two knobs to isolate the cause of a peak-RSS regression:

| Run | `AWS_S3_MAX_SOCKETS` | `includeVehicleVisits` | Wall clock | Peak RSS |
|---|---|---|---|---|
| baseline (pre-Task-1..5) | n/a (didn't exist) | true (sequential) | 4m06s | 612MB |
| after, ceiling on | 200 | true (concurrent) | 1m50-55s | 746-763MB |
| after, ceiling off | unset (SDK default 50) | true (concurrent) | 2m53s | 725MB |
| after, ceiling on, visits off | 200 | false | 2m12s | 728MB |

**Peak RSS lands in a narrow 725-765MB band regardless of which knob is toggled** - ruling out both Task 1's raised socket ceiling and Task 4's concurrent visits phase as the *dominant* driver (each was hypothesized first, each moved RSS by <5% when removed, while removing the ceiling cost ~1 minute of wall clock for almost no memory benefit).

**Root cause, confirmed via profiling (2026-07-29 follow-up)** - three V8 heap snapshots taken via `--heapsnapshot-signal=SIGUSR2` at ~8s/~53s/~98s into a run showed the JS heap itself is small and *flat* (103.6MB → 91.1MB → 96.1MB, `JSArrayBufferData` under 4MB throughout) - ruling out a JS-object leak entirely. Switching to 1s-interval `process.memoryUsage()` sampling (via a `NODE_OPTIONS="--require <preload.cjs>"` script, no app changes) showed the real picture: `rss` tracks `heapTotal` with a constant ~260-270MB offset (fixed native/process footprint, not growing), and `heapTotal` itself balloons to 400-475MB *during page processing* and does not shrink back down between pages, because V8 doesn't eagerly return heap arena space to the OS. The peak working set is genuine: Task 3's prefetch means the next `esPageSize`-record ES page is already being fetched while the current page's records are still resolving through the `s3ReadBatchSize`-wide (200) worker pool, so roughly *two pages* of fully-parsed JS objects (which run several times larger in memory than their serialized NDJSON form) are resident at once. **Confirmed not a leak**: sampling 30s past export completion showed `rss`/`heapTotal` flatline immediately rather than continuing to climb.

**esPageSize is the actual memory/speed dial** - a follow-up run with `esPageSize: 500` (same site, ceiling 200, visits on) measured peak `rss` ~611MB / `heapTotal` ~420MB (down from ~738-763MB / ~474MB at the default 1000), at the cost of wall clock rising to 2m21s (vs 1m50-55s at 1000) - roughly a 15-20% memory reduction for a ~25% speed cost, tracking `esPageSize` × "~2 pages resident" as the working-set formula, not a 1:1 halving (the ~260-270MB fixed floor doesn't shrink). **Speed goal exceeded at the default (~2.2x, short of the ~3.3x/1m15s target); memory goal missed and reversed vs baseline at the default, but is a tunable tradeoff via `esPageSize` for callers that need to bound memory over wall clock.** `gzipChunks` was not exercised in any of these measurements.

---

## synthetic-seed-testing

**When to use** — data-fix endpoints that are too complex to test with a single real vehicle: need multiple edge cases (no clean URL, merge, deactivated, price delta). Faster than the export-import workflow, no prod access needed.

**Core pattern:**
- Write a `tmp/seed-tests.mjs` script (ES module, direct AWS SDK + ES client calls).
- Use a **fictional narrow date range** in the far future (e.g. `2025-07-01T10:00:00Z`). No real vehicles ever have `activeFrom` in this window → the data-fix endpoint only processes your test seeds. No need to wipe the DB.
- Step 1 of seed script: `deleteByQuery` all records for the target site in ES (removes stale previous test runs).
- ES Data index has **strict mapping** — only whitelisted fields accepted. Fetch the actual whitelist once: `curl http://elasticsearch8.devenv:9200/market-study-vehicle-data_rollover/_mapping` and build a `Set` of top-level field names. Use a `stripS3Fields` function before indexing.
- S3 key format: `md5(url).replace(/((.)(.)(.).*)/, '$2/$3/$4/$1')` — path-prefixed hash. Use this for both reads and writes in the seed script.
- Seed script prints expected counters at the end (wellDoneCount, noDataWithFixedUrlCount, alreadyOkVehiclesCount) so the tester knows what to verify.

**Test case checklist for URL-migration fixes** (MAR-1975 pattern — 9 cases covering all branches):
1. Old URL only, no clean URL, vehicle active → `noDataWithFixedUrl+1`, `activeTo: null`
2. Old URL only, no clean URL, vehicle active (duplicate for confidence)
3. Old URL + active clean URL → `alreadyOkVehicles+1`, `activeTo: null`
4. Old URL + active clean URL, price delta → `alreadyOkVehicles+1`, history delta in merged S3 doc
5. Old URL active + clean URL **deactivated** (`activeTo` set) → `alreadyOkVehicles+1`, `activeTo` must be preserved (NOT null)
6. Old URL only, old URL itself **deactivated** (`activeTo` set), no clean URL → `noDataWithFixedUrl+1`, `activeTo` must be preserved on the new clean URL S3 record
7. **History interleave A** — old URL has internal history (T1→T3 with price change), clean URL is a single snapshot at T2 in the middle (T1<T2<T3) → `unpatchAndRecalculate` path, merged `history.length=2`, `activeFrom=T1`, price=newest (T3)
8. **History interleave B** — both records have internal history, fully interleaved (T1_old < T2_clean < T3_old < T4_clean) → `unpatchAndRecalculate`, `history.length=3`, `activeFrom=T1`, price=T4
9. **History interleave C / quick path** — clean URL is the oldest record AND has history (T1→T2), old URL is the newest single snapshot (T3) → triggers **quick path** (`vehiclesWithHistory.length===1` and record-with-history is oldest), `history.length=2`, `activeFrom=T1`, price=T3

**recalculateHistoryOfVehicle path rules** (critical for designing seed cases):
- **Quick path** — fires when `vehiclesWithHistory.length === 1` AND the record with history is the oldest (no record-without-history has an older `createdAt`). Prepends the existing history array and recalculates only from current state forward.
- **Full path (unpatchAndRecalculate)** — fires when `vehiclesWithHistory.length >= 2`. Calls `completeVehicle` on each record to explode history deltas into individual snapshots, then `fullHistoryRecalculation` sorts ALL snapshots by `createdAt` oldest-first and rebuilds from scratch.
- `activeFrom` always = oldest `createdAt` across all merged snapshots. URL direction is irrelevant — purely timestamp-based.

**Seeding S3 records with pre-existing history** (for cases 7-9):
Use a `scalarDelta` helper and a `stripForHistory` helper to compute jsondiffpatch-format deltas without importing jsondiffpatch:
```javascript
// mirrors getVehicleForHistoryCalculation (strips fields excluded from diffing)
const stripForHistory = ({ history, activeFrom, activeTo, id, mappedValues, mlConfidence, ...rest }) => rest;

// jsondiffpatch scalar delta: { field: [oldVal, newVal] } for each changed field
const scalarDelta = (oldState, newState) => {
    const delta = {};
    const allKeys = new Set([...Object.keys(oldState), ...Object.keys(newState)]);
    for (const k of allKeys) {
        const a = oldState[k], b = newState[k];
        if (JSON.stringify(a) !== JSON.stringify(b)) {
            if (!(k in oldState)) delta[k] = [b];
            else if (!(k in newState)) delta[k] = [a, 0, 0];
            else delta[k] = [a, b];
        }
    }
    return delta;
};

// Example: build an S3 record whose history says price went from P1 to P2 between T1 and T3
const t1State = stripForHistory({ ...base, url: oldUrl, price: P1, createdAt: T1 });
const t3State = stripForHistory({ ...base, url: oldUrl, price: P2, createdAt: T3 });
const record = { ...base, url: oldUrl, price: P2, createdAt: T3, activeFrom: T1, history: [scalarDelta(t1State, t3State)] };
```
Good only for simple scalar fields (price, createdAt). Works because ISO date strings are <50 chars so jsondiffpatch uses the simple `[old, new]` format (no LCS text diff).

**Verify with a separate `tmp/verify-*.mjs`** — spot-check key fields (price, activeTo, activeFrom, history delta) in S3 and ES after running the fix endpoint.

**Source:** session 2026-06-08 (MAR-1975 — 6 edge cases); extended 2026-06-16 (cases 7-9, history interleaving + scalarDelta helper).

## github-merge-workflow

**Tool** — custom GitHub Actions workflow in `.github/workflows/rebase-and-ff.yml`, calls reusable workflow from `Preskok/github-actions`.

**Commands** — comment on PR to trigger:
- `/finish-pr` — rebase branch on develop, force-push branch, fast-forward develop (or fast-forward master to develop for releases). No merge commit, linear history.
- `/sync-pr` — sync long-lived branches without rebasing (master → develop after hotfix).
- `/rebase-pr` — admin only; force-rebase a stale branch.

**Never use GitHub's native merge buttons** (Merge / Squash / Rebase) — team rule, explicitly banned. They create merge commits or rewrite SHAs on shared branches.

**Feature → develop flow:**
1. Rebase branch locally on develop and force-push: `git rebase origin/develop && git push --force-with-lease`
2. Comment `/finish-pr` on the PR — bot fast-forwards develop, closes PR. No merge commit.
- The action no longer auto-rebases for you; you must rebase locally first before `/finish-pr`.

---

## svl-skip-write-path

When `shouldValidateListingVehicle: true` and the listing partial matches the stored S3 vehicle (SVL passes, detail visit skipped), the two ES indices diverge in what they persist for that write:

| Index | What's written | Consequence |
|---|---|---|
| `marketstudy_search_rollover` (old index) | `bulk-save-listing-vehicle.service.ts` (`saveUpdatedVehicles`) writes **only the listing `partialVehicle`** — never merged with the full S3 vehicle | Any field the listing parser doesn't set (`bodyType`, `fuelType`, `transmission`, `description`, `country`, `vehicleListUrl`, `coverImageUrl`, `nettoPrice`, `numberDoors`, `numberSeats`, etc.) is **absent** on that doc, even though the S3-stored vehicle has it |
| `market-study-vehicle-data_rollover` (data index) | `saveVehiclesToDataIndex(s3DataMappedVehicles)` sends the **full `s3Vehicle`** | `bodyType`/`fuelType`/`transmission` etc. are present and correct here |

This is cross-site (any site with SVL enabled hits it), not a bug introduced by one crawler. **When validating description/bodyType/etc. coverage for a site with SVL enabled, query the data index (or S3 directly), not the old index** — the old index will show false gaps for every vehicle whose detail was skipped this run.

Separately: `description` and `equipment` were observed **absent from the data index too** for an SVL-skip write, despite `Vehicle.ts` declaring `description` as a valid field and S3 having full content (3705 chars) for the same vehicle. Root cause not yet found — likely a gap in the `GENERATE_DATA_VEHICLE` mapping consumer (`crawler-messages-routing.service.ts:156` → downstream consumer). Cross-site, unconfirmed scope. Worth a deeper look if description-coverage validation keeps surfacing 0% on SVL-heavy sites.

**Source:** session 2026-07-01 (MAR-2113 rastetter — traced via S3 ground truth vs both ES indices for the same storeId).

**Develop → master flow:** Comment `/finish-pr` — pure fast-forward, no rebase, SHAs preserved exactly.

**If action fails with "Changes must be made through a pull request":** The fix is `FF_MERGE_TOKEN` — a fine-grained PAT (contents + PRs write) added as repo secret and bypass actor on the org ruleset. Matea (ams-owner) owns this for market-study.

**Org ruleset (as of 2026-06-24):** "Protect long-lived branches" applies org-wide (require PR, no force-push, no deletion). Per-project approval rules set by project owner (Matea for AMS via `ams-owner` team).

**Source:** session 2026-06-26; Confluence — https://preskok.atlassian.net/wiki/spaces/TT/pages/4242931715

---

## dealer-id-generation

**Formula** (`DealerHelper.calculateDealerId`, `src/shared/helpers/dealer.helper.ts:9-16`): MD5 hash of `site + site + url + name + branchName`, where `url` = `website || siteUrl` (note `site` is concatenated twice — once inside the inner string, once again as the hash prefix — harmless redundancy, not a bug, but looks like one on first read). Plain MD5 hex via `src/shared/utils/Hash.ts`. Result becomes `rawDealerData._id`, which is both the S3 key and the ES `_id` for the dealer doc (`store-dealer.service.ts:131,144`).

**No URL normalization before hashing** — `http://` vs `https://`, trailing slash, `www.` presence, and case are NOT stripped/normalized. Any difference in scheme alone produces a different MD5 → a different `_id` → a duplicate dealer document for what is obviously the same real-world dealer. Confirmed live: same "KONGSVINGER BILSENTER AS" dealer on finn.no split into two ES docs purely because one crawl recorded `siteUrl: http://www.kongsvingerbilserbs.no` and another `https://www.kongsvingerbilserbs.no`.

**No dedup across different `_id`s exists anywhere in the pipeline.** `store-dealer.service.ts` only merges dealers that already share the *exact same* `_id` within one RMQ batch (`getUniqueDealersFromRmqMessages`, `getFulfilledFullDealer`). There is no cross-`_id` reconciliation by normalized URL or by name+branchName.

**This is a known, documented limitation**, not a fresh discovery — the Confluence "Dealers" page (https://preskok.atlassian.net/wiki/spaces/M/pages/2839773203/Dealers) explicitly lists "multiple dealerIds for the same dealer — with currently no programmatical way to detect this" as one of only two open problems, and ties future unification work to `MAR-1450`. Link any new duplicate-dealer findings to `MAR-1450` rather than opening an unrelated fresh ticket.

**Source:** session 2026-07-08 (dealer duplicate investigation, finn.no Kongsvinger Bilsenter).

---

## fueltype-mapping-longest-match

**`DataMapperService.mapValue()`** (`src/mapping/data-mapper.service.ts:31-53`) resolves `rawFuelType` → `FuelTypeEnum` by joining every string in each `RegexMappings.ts` category into one `(a|b|c)` regex **with no `\b` word boundaries** (`RegexMappings.ts:489`), matching against the transliterated input, then picking whichever single match across ALL categories has the **longest matched substring** — not the most specific category, just raw string length.

**Practical effect** — a category wins purely because one of its literal entries happens to be a longer substring match than the correct category's entry for that particular raw string. E.g. a bare `'el'` sits in the `ELECTRIC` list (`RegexMappings.ts:155`) with no word boundary, so it can match inside any raw text merely containing "el" as a substring. Whether this actually flips the result depends entirely on what else matches and how long those matches are for that specific `rawFuelType` string — there's no guaranteed hybrid/gasoline/electric precedence, only "whichever matched substring is longest wins."

**Fixes for specific raw strings are added as literal compound entries**, not by fixing the algorithm — e.g. `'Hybrid bensin', // finn` and `'Hybrid diesel', // finn` were added directly to the `HYBRID` category (`RegexMappings.ts:143-145`) specifically so the whole phrase matches as one longer string than any competing single-word match (`'bensin'` alone would otherwise lose to something in another category). When a site's hybrid vehicles keep misclassifying, check for this pattern first: does the raw string need a compound literal entry rather than relying on individual word matches winning by luck?

**`mapRawValues()` (`CrawlerAbstract.ts:456-495`, calls `parseFuelType`/`parseTransmission`/price mapping) is only invoked from the real listing-crawl flow** — via `mapAndSaveCrawledVehicle()` (`VehicleAdCrawlerAbstract.ts`), itself only called from `consumerVehicleList` → `crawlListing`. It is **NOT** called by a bare `crawler.parseVehicle()` invocation. The `/api/v1/market-study/crawl-vehicle` debug endpoint historically called `parseVehicle()` directly and saved the result without ever running `mapRawValues()` — meaning `saveData: true` through that endpoint wrote vehicles with `fuelType`/`transmission`/mapped `brand`/`model` all `null`, into BOTH the old index (`saveVehicleToOldIndex`) and — since `saveVehicleS3()` publishes to `MS_EX_BULK_SAVE`, which drives the full downstream pipeline, not just S3 — the data index too. Fixed (2026-07-08) by adding an opt-in `includeMapping` boolean to the endpoint's DTO that calls `crawler.mapRawValues(vehicle)` (widened to `public`) before saving, when explicitly requested. **When debugging a mapping fix (fuelType, transmission, brand/model) via this endpoint, `includeMapping: true` is required** — without it, the endpoint only exercises the site-specific raw parser, not the shared mapping layer, regardless of `saveData`.

**Source:** session 2026-07-08 (finn.no fuelType "Hybrid bensin" → Electric investigation, MAR-2039).

---

## devenv2-orbstack-troubleshooting

**ES flood-stage watermark blocks writes and does NOT auto-clear once disk frees up** — Elasticsearch sets `index.blocks.read_only_allow_delete` on every index once disk usage crosses the flood-stage threshold (default 95% used). Freeing disk space afterward does not lift the block automatically; it must be cleared manually: `curl -X PUT "<ES_URL>/_all/_settings" -d '{"index.blocks.read_only_allow_delete": null}'`. This applies independently per ES cluster (devenv2 runs separate ES7-for-graylog and ES8-for-marketstudy clusters sharing the same OrbStack VM disk) — check both.

**`docker system prune` (no `-a`) removes stopped containers too, not just dangling images** — a container that's `Exited` (e.g. graylog after a disk-pressure crash) gets deleted along with genuinely-dangling image layers. If a needed service was stopped/crashed, recreate it via `docker compose up -d <service>` from the project's compose directory (e.g. `~/Projects/devenv2`) afterward - named volumes persist the actual data even though the container itself is gone, so nothing is lost, just needs recreating.

**"Pull images" / "import_definitions_*" from devenv2's README is for a different scenario than a routine restart** - it's for bootstrapping a fresh devenv2 setup or picking up new RabbitMQ queue/exchange definitions from the `rabbitmq-preskok`/`rabbitmq-stellantis` repos. A plain OrbStack restart or `docker compose up -d` on an existing stack does not need it - as long as the RabbitMQ container itself was only restarted (not recreated from the image), its existing queues/definitions/data are untouched. Check `docker ps -a` status (`Up`/`Restarting` = untouched data, `Created`/image pull activity = actually recreated) before assuming a re-import is needed.

**OrbStack disk usage as seen by containers ≠ the Mac's real disk usage** - `docker run --rm -v /:/host alpine df -h /host` reports the OrbStack VM's own virtual disk (small, fixed size, e.g. ~34GB), not the host Mac's actual free space. Check the Mac's real disk with a plain `df -h /` outside any container - a genuinely low-disk Mac (single-digit GB free) is what pushes the OrbStack VM disk to its own flood-stage threshold in the first place.

**Source:** session 2026-07-13 (auto1 MAR-2129, disk-pressure/OrbStack outage investigation).

---

## local-http-client-private-env-location

**JetBrains HTTP Client's `http-client.private.env.json` for `test/requests/**/*.http` files lives at `test/requests/requests_envs/http-client.private.env.json` — one shared file, not one per subfolder** (e.g. not `test/requests/ActiveVehicle/http-client.private.env.json`). It holds `development`/`stage`/`production` sections with `workerUrl`, `accessToken`, `reportingAccessToken`, `id`, etc. JetBrains HTTP Client resolves private-env files by walking up the directory tree from the `.http` file being run, so this one shared file at `requests_envs/` covers every `.http` file under `test/requests/`. A `.dist` template sits alongside it (`http-client.private.env.json.dist`) as the reference for required keys. This file is gitignored (`**/http-client.private.env.json`, never committed, no git history) — if it's missing, it can't be recovered from git; recreate manually from the `.dist` template and real credentials. Do not run `git stash -a`/`--all` to try to "preserve" it across branch switches — that command is unsafe in this repo (corrupts `node_modules`, deletes `.env`).

**Source:** session 2026-07-14 (car-gr work, investigating a "missing" `ActiveVehicle`-specific private env file that turned out to never have existed separately).

---

## monthly-parsed-per-site-report

**What it is** — a scheduled task (`monthly-parsed-per-site-report`, cron `0 14 1 * *`, fires 1st of month 2pm local) that replaces manually reading the Kibana "Parsed per site per day" visualization. Queries `marketstudy_search_rollover` (the same ES index discussed under `es-indices` - reachable directly over HTTPS with basic auth, no VPN needed; endpoint/credential resolution is session-private, not documented here) for a `by_site`/`by_day` aggregation over the last 7 days, and writes `market-study-knowledge/reports/<YYYY-MM>.md` + updates `reports/monthly-avg-per-site.xlsx` (one column per month, one row per site, `avg_per_day`).

**Fragility discovered (2026-07 first-ever run)** — the target ES alias is a rolling window over only ~8 backing indices (roughly 8 days of retention). The very first scheduled run fired 7 days late (2026-07-08 instead of 2026-07-01) and by execution time its target window (2026-06-24 to 2026-06-30) had already aged out of retention entirely - `_search` returned 0 hits, confirmed via `min`/`max` aggregation on `CreatedAt` across the whole alias. **There is no make-up mechanism**: a late-firing run doesn't widen its window, it just fails and writes an honest failure note (no fabricated data, no `.xlsx` touch, no commit) per the task's own safety rule. Any run more than ~2 days late permanently misses that month's data point.

**Manual recovery recipe** — if a scheduled run failed or you want a fresh data point mid-month: query the actual available range first (`min`/`max` agg on `CreatedAt`), then run the same `by_site`/`by_day` aggregation over the last 7 *actually available* days (not the calendar-month-boundary window the automated run would use), and label the report with a note explaining it's a manual/shifted-window capture. Sanity-check the aggregation against a site with an independently known count (e.g. otomoto's daily total, frequently posted in `#tt-market-study-checklist`) before trusting the rest - a site whose count looks implausibly large (e.g. autoscout ~2M/day) can still be correct if that site key aggregates many countries under one crawler entry; verify with a direct `_count` query on a single day/site before assuming an aggregation bug.

**Source:** session 2026-07-28/2026-07-30 (manually running the report for the first time after discovering its first automated run had silently failed).

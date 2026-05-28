# Foundational Knowledge — Market Study System

Architecture and operational context that explains WHY things are designed the way they are. This is historical/conceptual — helps understand the big picture when debugging.

---

## Index architecture (Elasticsearch)

- **Old search index** — `marketstudy_search_rollover` (alias). Capitalised fields (`Site`, `URL`, `Description`, `Price`, etc.). URL-unique list of currently-active vehicles only. Primary lookup by URL.
- **New search index** — was being built, later **frozen** (Mar 2025 deploy). Stops writing to it; reads continue.
- **Data index** — `market-study-vehicle-data_rollover` (alias). Lowercase fields (`site`, `url`, `price`, etc.). History index — stores full vehicle lifecycle, including deactivated docs and change history (progressive validation). Typically ~30x larger than the old search index (e.g. eurostocks: 30k in old vs 1M in data).
- **S3 raw response cache** — bucket `$AWS_S3_BUCKET_DAILY_CACHE`, keys `YYYYMMDD/[md5-hash]`. 7-day retention. Used by crawler for rerun on same day without repeat external requests.

The `workingUrl` vs `legacyUrl` pattern exists because sites change URL formats:
- `legacyUrl` — stable key used for S3 cache + deduplication. `storeId = md5(legacyUrl)`. Saved to **old search index `URL` field as-is** — it never gets rewritten there.
- `workingUrl` — current URL to actually fetch (update when site changes). On the in-memory `AdVehicle` object only. **At ES write time, [search-vehicle.service.ts:256](src/vehicle/search-vehicle.service.ts) does `url: vehicle.workingUrl ?? vehicle.url`** — so the data index `url` field contains the working URL when one is set, and the legacy URL otherwise.
- `workingUrl` is **NOT a separate persisted ES field.** Don't expect it in `_source`. It exists only in: in-memory AdVehicle → raw S3 vehicle JSON → swapped into `url` at write-time.

**Consequence for the same vehicle:**
- Old search index `URL` = legacy URL (e.g. `…/vehicles/cars/{bodyType}/vehicle/{id}/…`)
- Data index `url` = working URL (e.g. `…/en/vehicle/{id}/…`)

This is **by design** — don't flag the mismatch as a workingUrl-migration bug.

See [Working URL fix docs](https://preskok.atlassian.net/wiki/spaces/M/pages/3002302476/Working+URL+fix).

### Validation gate split between indices

The `"Skip saving data vehicle to ES due to failed validation"` log (context `VALIDATION`) **only blocks writes to the data index**. The old search index write path runs separately and **does not consume the same validation result** — bad docs (e.g. negative prices) can still appear in `marketstudy_search_rollover` even when their data-index counterpart was rejected. **This is the current architectural behaviour, not a bug** — it's a known split. When investigating "validation says skipped, why is it still in ES?", check which index you're looking at: probably the old search index.

---

## Queue architecture (RabbitMQ)

- `MS_[SITE]_LISTING_URLS_TO_FETCH` — per-site queues for big sites (autoscout, mobile, leboncoin)
- `MS_GENERAL_LISTING_URLS_TO_FETCH` — shared for small/medium sites
- `MS_BROWSER_CRAWLERS_LISTING_URLS_TO_FETCH` — for sites needing browser requests (puppeteer): subito, olx-ro, otomoto, etc. Isolated so slow browser crawls don't block axios-based sites.
- `MS_WEEKLY_LISTING_URLS_TO_FETCH` — **car-gr only**. Weekly cycle: Tue start → drains across week → Mon 23:25 purge before next crawl.
- `MS_HUNGARY_LISTING_URLS_TO_FETCH` — shared: mobile-bg (matchingDay 0) + hasznalt-auto (matchingDay 1). Max 6 consumers. Purged at 23:25 nightly.
- `MS_DL` — dead-letter for crawl consumers. **No TTL** — manual purge.
- `MS_BULK_DL` — dead-letter for bulk save. 24h TTL. Mostly dedup messages, not real failures.
- `MS_BULK_SAVE_DL` — bulk save worker DL. ES/MySQL connection issues usually.
- `MS_TASKS_DL` — long-running task DL (e.g. car-gr listing exceeded 2.5h timeout).

**Bulk save queue split — old vs new index** (frequent confusion):
- `MS_BULK_SAVE_VEHICLES` → saves to **old search index** (URL-unique). Property names lowercase (`url`, `site`).
- `MS_BULK_SAVE_SEARCH_VEHICLES` → saves to **new search index** (frozen Mar 2025; still receives writes but read-only consumers). Property names PascalCase (`URL`, `Site`).
- `MS_BULK_SAVE_LISTING_VEHICLE_CHECK` → SVL gating queue. Pass → routes to `MS_BULK_SAVE_VEHICLES`. Fail → routes back to `MS_GENERAL_LISTING_URLS_TO_FETCH` for detail visit.

When redelivering from `MS_BULK_SAVE_DL`, distinguish target queue by message property casing (lowercase = OLD, PascalCase = NEW).

Queue timeout: default 30 min. Raised to 2.5h for `MS_WEEKLY_...` to accommodate car-gr slow requests.

### RMQ dedup scope (DUPLICATED ID CASE)

`RmqBulkConsumer.messageReceiveCb` checks `x-deduplication-header` (or hash of message content) against an **in-memory `Map`** (`messagesList`) sized to the prefetch count. Logs `DUPLICATED ID CASE, ACK-ING MESSAGE` when a hit fires.

**What it catches:** the same RMQ message redelivered to the same consumer in the same batch — typical cause is channel restart / instance restart redelivering unacked messages.

**What it does NOT catch:** the same vehicle arriving from different listing pages. If the same vehicle is published to RMQ twice (e.g. it appears on both `opel/corsa` page 3 AND `opel/mokka-e` page 15 — common with broken model pages), the two messages have different content (different listingUrl/queryParams), hash differently, and both pass through the dedup. Both then go through full detail fetch + parse + ES upsert. Final ES state is correct (same `storeId` = upsert overwrites same document), but scrape.do credits and crawl time are wasted.

The Map is cleared after each batch is processed — there is no Redis-backed cross-batch dedup.

**Implication:** for sites with broken model pages that fall back to full brand catalog (eurostocks pattern), data integrity is preserved at upsert time but credit/time waste must be addressed at the listing parse layer if it matters.

---

## Deactivation pipeline

- Starts nightly at **22:00**
- Average: ~250k/day deactivations
- Peak: leboncoin days can reach 2M deactivations
- Safe threshold: ~900k — above this, pipeline slows down significantly
- On timeout: retry once → `MS_BULK_DL`
- Indexing ordering: multisearch before indexing; flag `bulk_save_search_vehicles` request_ids

**Deactivation safeguard** — can manually lock so a specific site doesn't deactivate tonight (used during autoscout hotfix when we knew crawl was broken but didn't want to mass-deactivate).

---

## Crawl reruns & scheduling

- Full crawl: 00:02 cron start
- Automatic producer reruns: 6 AM, 7 AM, 8 AM — triggered by log `"Problem preparing listingUrl messages for site!"`
- **NOT retried**: `"Prepared listingUrl messages 0 for site!"` — silent selector failure. Needs manual.
- `MS_WEEKLY_...` queue being not-empty Tue-Sun is NORMAL (car-gr crawls all week)
- `MS_HUNGARY_...` being not-empty in morning is NORMAL (SVL runs till ~8:30)
- `eurostocks` sends messages to RMQ directly from `getBrandsAndModels()` (legacy design, avoids blocking general queue) — excluded from "no vehicles" alert

---

## S3-vs-ES validation (Marko's script)

Dec 2024 implementation by Marko Lavrinec. Script compares saved S3 raw vehicle to ES entry. Mismatch emails indicate validator silently dropped fields beyond ES limits (too-many-doors, engineCapacity overflow, price too big, etc.).

First real email: subito 2025-01-09.

Context `VALIDATION` + specific message `"Vehicle S3 vs ES comparison failed in object prop"`.

---

## Zombie vehicles

Vehicles active in Data index but the crawler can no longer reach them (site URL changed, site gone, detection failed). Often leftovers from May-June 2024 deactivation-timeout incidents.

Matea's stock widget catches them as "active" when the crawler is effectively dead. Marko has a detection script.

Why they matter: they inflate historical counts, mislead stock widgets, and cause "this site is still active" false positives.

---

## Details URL validation

Picks last 5 URLs from ES Data index (past 2 days) per site. Uses crawler's `fetchRequestOptions` + optional `getFetchRequestOptionsForDetailsUrlValidation()` override (e.g. for different redirect behavior than main crawl).

Why small sites sometimes get "no URLs to validate" alert: <5 vehicles changed in past 2 days → nothing to validate → not a bug.

---

## ScraperAPI vs scrape.do

**Two different services, two different accounts, two different dashboards.**

- **ScraperAPI** — older, used by leboncoin, hasznalt-auto. Tiers: 1/10/25/30 (ultra_premium) credits. Retry escalates tiers. `Additional credits used for request` log shows retry happened.
- **scrape.do** — newer, used by car-gr, autoscout-ch, promo-neuve (attempted). Account: `tt@preskok.si`. Support has allowlisted hasznalt-auto, helped with car-gr.

Monthly credit check: 24th. >70% mid-period → consider disabling low-priority sites.

**ScraperAPI billing change risk (Nov 5 2025 incident):** ScraperAPI can change their credit billing model with no warning. All sites suddenly jumped to 10 credits/request regardless of configured tier. Budget burns in days, not a month. If ScraperAPI sites all fail or show massive credit consumption on the same date, contact ScraperAPI support immediately — do not assume it's a crawling issue. Pattern #90.

**scrape.do personal accounts — do NOT test with personal accounts.** Matea's personal account was permanently banned after fewer than 50 credits used while testing avto-net. Always use the team account `tt@preskok.si`. scrape.do has tight fingerprinting; even testing a site that is already a known-client on a personal account triggers suspicion.

---

## Alert / reporting infrastructure (from 2025-06-04 meeting)

Jira tickets:
- `MAR-1898` — crawling-not-finished check improvements
- `MAR-1899` — queues-not-empty check improvements
- `MAR-1900` — big-number-of-validation-logs report improvements
- `MAR-1901` — details-url-validation improvements
- `MAR-1902` — reducing MS_BULK_DL messages

Known site problems table: `https://preskok.slack.com/archives/C0859KQ45B2/p1749032315353719`.

Canvas files in the channel:
- `F08V4RBLGKV` — known reporting site specifics (per-site quirks that should not trigger alerts)
- `F0AQHFU4FDZ` — observations / false alarms

---

## Deploy flow & branches

- Bitbucket defaults for `hotfix/*` branches: **target master** (NOT develop). This bypasses develop review.
- Proper flow: merge to develop → deploy stage → deploy master → deploy prod
- Minimum 1 PR approve
- Deploy coordination: usually Matea handles prod deploys
- After deploying parser fix: redeliver DL messages via Jenkins job

Stage deploy mistakes (wrong branch to prod) have happened — double-check master is deployed if symptoms are "half-crawl" or "feature acts like stage".

---

## Stage environment

- **Stage instance control**: Jenkins (URL in internal infra docs / ask DevOps)
- Stage instances reset daily (automatically scaled down overnight). Increase manually when running a stage test.
- Consumer count = instances × 2 (2 workers per instance).
- Stage S3 bucket: separate from prod. Access requested via service request.
- Stage → MySQL can be dramatically slower than prod for identical queries — caching / different config / sometimes-corrupt `performance_schema` (Oct 2025 incident).
- Stage tests can be limited by using throttled listings like you'd do for `autoscout-ch` (cap the number of listings to avoid burning credits).

---

## Mid-day deploy protocol

1. Lock deactivation for the affected site (if risk)
2. Deploy to master
3. Rerun crawler on prod — responses served from S3 (no credits spent), re-parsed with new code
4. Verify via ES count + Graylog
5. Redeliver DL messages
6. Unlock deactivation

---

## On-call cadence

- Daily emails: vehicle count comparison (morning), validation logs (morning), 12:00 queues check, evening crawled-vehicles-comparison
- Weekly: AWS cost, scraper credit check (1x/month), stock widget (2x/month)
- Weekly rotation: one person per week is "on call". Documents findings in weekly Slack thread.

---

## Graylog reliability & retention

- Graylog is the primary debugging tool for production crawl issues. However it has had reliability problems:
- **Aug 8, 2025 incident:** Production Graylog logs permanently lost for that date. Root cause: Graylog's own ES went down for maintenance/issue while the production ES was also under stress. Logs were written nowhere and cannot be recovered. **Minimum recommended retention: 1 week.** This is the lesson from the outage — without a buffer, any infra hiccup causes permanent diagnostic loss.
- **False "no messages" / "queues empty" alerts:** Graylog downtime causes alert scripts that query Graylog for log lines to see 0 results and fire false alarms (Pattern #32 in failure-patterns.md covers this). When multiple alert emails arrive at once saying completely different sites are all empty, suspect Graylog before suspecting the crawlers.
- **Log shipping lag:** Graylog can be 5-10 minutes behind real-time during high-load periods. When debugging an active incident, cross-check with CloudWatch or ECS task logs if Graylog shows nothing recent.
- Graylog infra: managed by Stas. Report issues to `#tt-devops-support`.

---

## People / roles

- **Matea Lenček** (UQXNRJK17) — lead. Has RMQ, S3 delete, prod param-store access. Often deploys prod.
- **Filip Ožbolt** (U04GZH40QMD) — engineer, on-call rotation
- **Danijel Daskijević** (U042X3G1ZQT) — engineer, on-call rotation (ex-QA)
- **Gregor Džampo** (U052JEQQGNR) — product / business decisions (which sites matter, disable/prioritize)
- **Marko Lavrinec** (U03A150FJ65) — infra-adjacent; built S3-vs-ES validation, zombie detection
- **Stas** (devops) — hosts mobile proxies (9001-9007), handles Graylog/infra issues. Report to `#tt-devops-support`.

---

## Useful confluence pages

- [Working URL fix](https://preskok.atlassian.net/wiki/spaces/M/pages/3002302476/Working+URL+fix)
- [Site protection list](https://preskok.atlassian.net/wiki/spaces/M/pages/3898114050/Site+protection+list)
- [Price and discount handling](https://preskok.atlassian.net/wiki/spaces/M/pages/3614179347/Price+and+discount+handling) — canonical rules (mileage check, netto/brutto, catalog, leasing)
- [Data vehicle ES Index DB](https://preskok.atlassian.net/wiki/spaces/M/pages/3448274977/Data+vehicle+ES+Index+DB) — MySQL cache (Marko, Dec 2024)
- [Skip Visiting Listing Details](https://preskok.atlassian.net/wiki/spaces/M/pages/3456303118) — listings-only pattern (leboncoin, lacentrale)
- [Get Cheapest Vehicle API](https://preskok.atlassian.net/wiki/spaces/M/pages/3489234946/Get+Cheapest+Vehicle+API) — offers integration
- [Hasznalt-auto site notes](https://preskok.atlassian.net/wiki/spaces/M/pages/3601203215/Hasznalt-auto)
- Useful ElasticSearch queries (includes "Get daily number of unique URLs from old search index")
- Auto-connect known problems

---

## Price/discount canonical rules (Gregor 2025-03)

Handling of price/discountedPrice/discount varies per site and market. **When in doubt, match the rule the team documented in the Confluence "Price and discount handling" page, not what the site says.**

- **New vehicles:** discount often = difference between factory/catalog price and customer price (common on French dealers).
- **Used vehicles:** no default discount. Do NOT persist discount unless it's a genuine seller-driven markdown (start price visible on site + lowered price).
- **Catalog price vs seller price:** seller price is `price`. Catalog price can be higher or lower — if lower, discount is negative → don't save discount, save only price (cardoen, star-terre).
- **Netto (without VAT) price:** `rawNettoPrice` → `nettoPrice`. Classic trap: site shows price excluding 19% VAT as primary value (German commercial vehicles). Always check if site gives both and pick the brutto one as `price`.
- **Leasing / financing:** monthly installments should not be saved as price. If site marks leasing explicitly, skip. Otherwise use margin heuristic (DOFR > 5y + price < 2k → skip on blocket/finn).
- **Mileage-missing rule:** if `mileage` is missing/null, save ONLY `price by seller` (no discount, no catalog). Prevents junk data.
- **Avto-net / avto-cena local competition:** `avto-cena.si` is local competitor — future co-worker? Noted Dec 2024.

---

## Dealer handling

- `dealerId` = site + name + branchName (+ anything to make it unique).
- `branchName` typically = city. When multi-branch in same city (biltorvet, willhaben in Linz), add ZIP code or full address.
- Dealers currently stored in separate MySQL table with `branchAddress` column (no separate ZIP/city/street) — full address as single string works.
- Marko's dealer analysis: 17k pro dealers on leboncoin alone.
- Bulk "Partial dealer does not match with full dealer" logs usually mean `branchName` missing → fix per-site specifics.

---

## Body types

- Maintain consistent case — lowercase canonical. Mixed capitalization on input causes duplicates.
- `RawBodyType is missing translation` — 15k logs/day across all sites at one point. Reminder set every 16 weeks to sweep missing types.
- Problematic: `car-gr` `cars` body type maps to multiple real types depending on vehicle. Decide per-site.

---

## Tracking tools we've seen on sites

- **Datadome** — leboncoin, polovni-automobili (base protection)
- **Akamai** — leboncoin (added on top of Datadome Jan 2025 → ultra_premium required)
- **Cloudflare** — autoscout-ch, otomoto-ish, olx-ro, autoplius, pazar3, auto-connect (many)
- **CloudFront** — otomoto, blocket, lacentrale (AWS-based)
- **Incapsula** — ouestfrance-auto (fake 200)
- **first-id** — lacentrale (user cross-site tracking, fingerprint feeder)

These are services; actual block behavior per-site often depends on specific security tier + our IP/proxy pool.

---

## Kw ↔ HP conversion gotcha

- CIS uses **1.341** multiplier (kw → hp). Same as our AMS default.
- mobile.de and autoscout use **1.36** internally for ranges in URLs.
- URL generator (for listing URLs passed into search API) can be off-by-one-HP from what site expects → missed vehicle matches. Keep a small tolerance range when generating HP-based URL params.

---

## APPLICATION_MODE env

Run only a subset of AMS locally/dev by setting `APPLICATION_MODE=SEARCH_API` (or `CRAWLER`, etc.). Saves time and CPU when you only need part of the system.

---

## Things the team has decided NOT to fix

- eurocar-thoma chronic 9/12 stock — "don't investigate" (Gregor)
- garage-chambon supplier catalogue inflation — product decision to skip supplier vehicles
- Some site-side data bugs (recycled storeIds, fake counters) — cosmetic, not actionable

Always check with Gregor before investing time on buyer-stock anomalies — he may already know.

---

## Exchange rate service

- Source: ECB (European Central Bank) — `https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml`
- Updated daily. Fetched and cached by AMS.
- **Gap known Aug 24–30, 2022**: Exchange rate service didn't work for that period. Fallback rate was `1` (wrong). Bilbasen prices stored with incorrect EUR conversion for those dates.
- **Missing currencies**: ECB doesn't publish rates for Albanian (ALL), Macedonian (MKD), Serbian (RSD), Kosovo (not independent ISO). vozi.com affected (MKD/ALL prices). Solution: use alternative reliable source or store as null.
- If exchange rate service outage suspected: check if prices across ALL multi-currency sites look wrong for a specific date range. Fix: update the bilbasen-era fallback logic so outage doesn't silently store garbage.

---

## ms-bulksave normal operating configuration

- **Normal instances:** 1 (scales to 2 when bulk queues > 300k messages, scales back at 100k)
- **DO NOT** scale to 10 — this overwhelms ES (100% CPU incident July 2023)
- During full S3 remap: temporarily raised to 6 (see fix-playbook.md "Full S3 remap")
- Prefetch setting matters: high prefetch during ES stress events causes cascading timeouts. Reduce prefetch if ES starts timing out.

---

## Synthetic date conventions

When a site doesn't give full date precision, the team uses these conventions:
- **avto-net (year only)**: Store as `16.[month].YYYY` — day=16 signals "synthetic, year-only estimate"
- **oglasnik (year only)**: Store as `[year]-07-01` (production year + 6 months) as DOFR approximation
- These are established conventions — don't change without team agreement (downstream consumers depend on them)

---

## #tt-market-study channel history

The channel was created **January 11, 2023**. Events before that date are not documented in Slack and must be found in Confluence, Jira tickets, or git history. The previous private channel may have contained earlier discussions.

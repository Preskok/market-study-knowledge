# Fix Playbook — Operational Actions

Non-code fixes and implementation patterns. Confirm with user before destructive operations.

---

## Delete S3 cached response

```bash
AWS_PROFILE=preskok-prod aws s3 rm s3://$AWS_S3_BUCKET_DAILY_CACHE/[YYYYMMDD]/[md5-hash]
```

Find the hash:
- Graylog `"Response found in S3"` logs the key
- Error logs reference keys like `20260422/158d7b3b37a986151eeefb24fc4e4e85`

If user lacks delete permission, ask Matea (she has it, sometimes gets revoked).

Daily cache keys expire after 7 days. 4xx/5xx NOT cached — rerun on healthy site works without deletion. **200-with-empty-body IS cached** (auto-zeilinger pattern) — must delete.

---

## Rerun crawler on production

Via AMS admin UI. Auto-reruns: 6/7/8 AM on `"Problem preparing listingUrl messages for site!"`. Does NOT retry on `"Prepared 0 listingUrls"`.

**Cautions:**
- Rerun creates duplicates in Old index if messages still in queue
- Check queue is drained first
- Rerunning after SVL fix reads S3 responses (no credits spent) — subito 2025-03-26 pattern

---

## Redeliver DL messages

After parser fix deployed. Messages in `MS_DL`, `MS_BULK_SAVE_DL`, `MS_BULK_DL`, `MS_TASKS_DL`. Use Jenkins job or RMQ UI "redeliver to original queue". Matea has access.

- `MS_DL` no TTL — manual purge or redeliver
- `MS_BULK_DL` 24h TTL

---

## Purge queue

Removes waiting messages. Does NOT remove unacked (being processed). Unacked resolve by:
- Consumer ACK/NACK
- Message TTL expiry (30 min default)
- Consumer restart

For stuck message (infinite loop), restart consumer.

Matea has RMQ UI access.

**Special purge:** `MS_WEEKLY_LISTING_URLS_TO_FETCH` is purged every Mon pre-midnight for car-gr weekly cycle.

---

## Disable crawler

```typescript
[SiteKeys.SITE_NAME]: {
  ...
  isDisabled: true, // MAR-XXXX: reason
}
```

Requires deploy. Use when fix >1 day, credit burn, or site fully offline.

---

## Lock deactivation for a site

Before risky crawl/remap: lock deactivation for affected site so that night's deactivation won't kill legitimate vehicles. Matea routinely does this before hotfixes (subito, autoscout patterns).

---

## Swap proxy port

When `9007` etc. down:
1. Check `#tt-devops-support` (Stas may be on it)
2. AWS parameter store: swap to working port (9001, 9005)
3. Delete Redis `datadomeService` entry (cookie/proxy mapping cache)
4. Deploy

Available mobile proxies: `9001`-`9007`.

---

## Verify static proxy (willhaben)

```bash
curl -x $PROXY_URL ifconfig.co
# and check
$PROXY_URL (HTTP)
```
On office VPN the static proxy activates automatically. 429 from site may indicate proxy not actually used.

---

## Contact scrape.do support

Account: `tt@preskok.si`

History: allowlisted `hasznalt-auto`, helped with `car-gr`.

Reply to existing thread:
- Site URL + example request URLs
- Credits issue (e.g. "1-credit all fail, only 25-credit works")
- Ask to investigate / adjust credits for specific site

---

## Run `cache-active-vehicles`

Syncs ES active vehicles → MySQL `vehicle_visit`. Run when MySQL connection issues caused DL spam during deactivation, or concerned about wrong deactivations.

---

## Site returning from pause/hiatus — URL stability check

Before re-enabling a site that was disabled for days+ (car-gr pattern):

1. **Fetch a detail URL through the crawler (or manually).** Compare to a historical URL from ES/S3 for the same ad.
2. If the new URL format differs, implement legacyUrl + workingUrl BEFORE re-enabling. Otherwise we create S3 duplicates.
3. Announce re-enable in #tt-market-study before turning it on. If `car-gr`-style duplicates are unavoidable, document and accept new baseline from that day.
4. Don't trust "one good day" as "fixed" — wait a full week (leboncoin 2025-07-29 pattern).

---

## Change RMQ x-consumer-timeout on a queue

Timeout can't be modified on an existing queue — queue must be **deleted and recreated**. Messages preserved via shovel.

**Procedure (requires Stas or sim infra access):**
1. Update `rabbitmq-preskok` `definitions.json` — add `x-consumer-timeout` (ms) as an `arguments` entry for the queue. PR against main.
2. Shovel messages from queue → temporary queue (pre-created by Stas).
3. Wait for unacked messages to be ACKed (or close consumer channel forcibly if one message is stuck in long processing).
4. Delete the queue (will be auto-recreated by AMS on next publish with new config).
5. Shovel from temp queue back → new queue.

**Example:** `MS_LEBONCOIN_LISTING_URLS_TO_FETCH` raised 30min → 2h (`7200000`). Was needed because leboncoin listings could take 1h+ due to ScraperAPI latency — RMQ kept redelivering, each retry burned 1000+ credits reading S3/doing partial work.

**Warning:** Only change one queue at a time. Applying to all queues at once breaks stuck-message detection.

---

## Full S3 remap (Marko's pipeline)

Used after fundamental mapping change (e.g. improved model mapper). Remaps all saved raw S3 vehicles → new ES schema. Planned, runs over days.

**Prep:**
- Lock deactivation for affected sites (optional, if running during night).
- Block AMS_RESPONSE saving consumer if you want S3 written before ES.
- Ensure Data index rebuild prerequisites met.

**Scale up (Stas, via Terragrunt `iac` repo):**
- `ms-bulksave` → 6 instances (NOT 12 — that's consumer count, not instance count)
- `data-api worker` → 60 workers

Paths:
- `terragrunt/preskokProduction/eu-central-1/apps/rabbitmq-workers/DataApiWorker/terragrunt.hcl` — set `app_min_capacity`, `app_max_capacity`, `app_desired_count`
- `terragrunt/preskokProduction/eu-central-1/ecs/cluster1/terragrunt.hcl` — set `asg_min_size`, `asg_max_size`, `asg_desired_capacity`

**Purge queues before starting** — stop ms-ms autoscaling group (so messages don't keep flowing in), then purge all crawling queues. Restart ms-ms after.

**Monitor:**
- Grafana RMQ dashboard — watch `unroutable` counter (message hit exchange but didn't route to queue; means wrong routing key or delayed-exchange discard). NLB can route between multiple cluster IPs — you may need to switch Grafana var to see data.
- ms-bulksave memory — don't panic under 80%. Redeploy resets it.
- AMS_RESPONSE prefetch — raise 800 → 1400 during remap (saves to S3 faster); revert after.

**After:**
- Scale back: ms-bulksave → 1, data-api worker → 1
- Remove deactivation lock
- Verify counts in ES Data index

**Scope reference:** remap of 6.5M active vehicles = ~1 day. Full S3 (~130M) = ~2 days. Costs: data-api worker + ms-bulk scale = meaningful money — don't do full remap unless a DataAPI bug requires it.

---

## Redeliver after deploy (standard recovery flow)

1. Deploy fix to master → prod
2. Purge MS_DL first if you want clean monitoring
3. Redeliver messages (Jenkins)
4. Watch MS_DL for new entries — should not grow
5. If new DL entries, fix again or roll back

---

## Delete Redis cached value (auth tokens, cookie maps)

Some crawlers cache auth/session values in Redis (not S3) because they need to stay in sync with request headers (user-agent + token). Examples:
- eurostocks — auth xPlatformToken + user-agent
- datadomeService cookie/proxy mapping (relevant when rotating mobile-proxy port)

**Why Redis not S3:** `useS3Cache: false` on those specific requests (header binding means S3 replay would serve stale pairs).

**To force refresh** (e.g. after auth format change):
1. Install "Another Redis Desktop Manager" (Matea's recommendation).
2. Connect to prod/stage/local Redis — ask Matea if you don't have connection info for prod.
3. Find the key (naming usually per-site or service-level like `datadomeService`).
4. Delete it. Next request regenerates.

Key pattern varies — grep crawler code for `redis` / `REDIS` / `cacheService` to find the key name.

---

## Local crawler test

```bash
npx ts-node console/main.ts test-rmq --site=[site-key] --url=[detail-url]
npx ts-node console/main.ts sync:vehicles
```

Use prod token from LastPass (`Market Study Prod Token`). **Careful with credits. Never leave prod token in `.env`.**

Reproduce MS_DL failures locally:
1. Copy raw response from prod S3 to local S3 with same key
2. Publish payload to local RMQ
3. Observe parsing error

### Replay a problematic prod response in LocalStack

For deterministic parser-fix iteration without burning credits, copy the exact prod response into LocalStack under TODAY's date so the crawler reads it as if from cache.

```bash
# 1. Find the daily-cache key in Graylog ("Response found in S3" log) or by hashing the URL.
#    Hash format: md5(url + "_" + data)  — for GET-only, data is undefined → suffix "_undefined"

# 2. Pull the prod response locally
AWS_PROFILE=preskok-prod aws s3 cp \
  s3://$AWS_S3_BUCKET_DAILY_CACHE/[YYYYMMDD]/[md5] ./response

# 3. Upload to LocalStack under TODAY's date (so crawler treats it as fresh cache)
aws --endpoint-url=http://localhost:4566 s3 cp \
  ./response s3://local-ms-raw/$(date +%Y%m%d)/[md5]

# 4. If you get InvalidRequest "x-amz-trailer header not supported", disable checksum:
AWS_REQUEST_CHECKSUM_CALCULATION=when_required \
  aws --endpoint-url=http://localhost:4566 s3 cp \
  ./response s3://local-ms-raw/$(date +%Y%m%d)/[md5]

# 5. Run only the crawler path that hits this URL (single brand/listing filter)
#    — see CLAUDE.md § Local crawler testing recipe
```

For seeding a vehicle into the local **store** bucket (not daily cache) — first 3 chars of `storeId` form the directory hierarchy:
```bash
aws --endpoint-url=http://localhost:4566 s3 cp \
  ./vehicle-file s3://local-ms-store/a/b/c/abc...full-storeId
```

### Get clean (non-cached) responses while iterating

Useful when you need every request to hit the network (selector debugging, anti-bot work):
- Set `AWS_S3_BUCKET_DAILY_CACHE_PERMISSION_WRITE=false` in `.env` — reads still work, writes are skipped, so successive runs don't poison the cache with mid-debug responses.
- For one-off requests, pass `useS3Cache: false` in `fetchRequest` options.
- Always re-enable cache writes when done — running with writes disabled long-term breaks tomorrow's reruns.

### Wipe the local daily cache

```bash
curl -X POST 'http://localhost:3000/api/v1/market-study/delete-daily-cache' \
  -H 'Authorization: abcd' -H 'Content-Type: application/json'
```
Wipes ALL sites' daily cache (not per-site). Use when stale local cache is masking a code change.

---

## PR / Deploy

- **Hotfix PR target: develop** (NOT master — Bitbucket defaults `hotfix/*` to master, bypassing develop review)
- Minimum 1 approve
- Flow: merge to develop → deploy stage → deploy master → deploy prod

When squashing: edit commit message in PhpStorm or Gitkraken (don't forget ticket number).

---

## Queue timeouts

- Default RMQ: 30 min
- `MS_WEEKLY_LISTING_URLS_TO_FETCH`: 2.5h (car-gr)
- Consumers per queue: 1-4

---

## Credit management

- ScraperAPI + scrape.do dashboards (separate)
- Monthly check: 24th
- >70% mid-period → disable low-priority sites

---

## ScrapeDo migration & success rate testing

Use when migrating a site from DataDome/browser/direct to ScrapeDo, or when evaluating whether the current proxy tier is good enough.

### 1. Branch setup

```bash
git checkout master && git pull
git checkout -b feature/MAR-XXXX-<site>-scrapedo-migration
```

### 2. ProxyConfig selection

In the crawler service, declare:

```ts
private readonly proxyConfig: ScrapeDoProxyConfig = {
    browserAtRetry: null,       // 5 credits — datacenter + JS render
    superAtRetry: 1,            // 10 credits — residential + EU geo-targeting (start here for anti-bot sites)
    superBrowserAtRetry: null,  // 25 credits — residential + JS render (last resort)
};
```

**Credit tiers:**
| Param | Cost | When to use |
|---|---|---|
| `null` for all | 1 credit | No anti-bot, plain HTML |
| `browserAtRetry: N` | 5 credits | Mild JS gating, no residential needed |
| `superAtRetry: N` | 10 credits | DataDome / Cloudflare / moderate anti-bot |
| `superBrowserAtRetry: N` | 25 credits | Strongest protection, use as last resort |

`retryNr` starts at 0, so `superAtRetry: 1` means datacenter on first attempt, residential from retry 1 onward.

**Credits lock:** if `requestCost > maxRequestCost` fires more than 9 times in one crawl window, ScrapeDo auto-locks the site in Redis until next crawl day. Watch for `"ScrapeDo - activated credits lock"` in Graylog — means scrape.do is silently upgrading your tier (site is harder to reach than config assumes). Either increase the declared tier or contact support.

### 3. Narrow with a brand filter (always do this on a new branch)

**Policy: always add a brand filter when starting a new feature or bugfix branch.** Stage runs stay scoped, credits are preserved, and iteration is faster. Remove it only when explicitly told to or just before the PR is ready.

In `getBrandsAndModels()`, add just before the final `return`:

```ts
// TODO temporary test filter — remove before PR
return brandsAndModels.filter(a => a.brandName.toLowerCase().includes('<brand>'));
```

Pick a brand that has **1 000–2 000 listings on that site** — enough surface to catch bugs, fast enough to iterate. Check the site directly or use ES to find a brand in that range. The right brand is site-specific — don't default to Mitsubishi without checking.

### 4. Clear stale S3 cache (optional but recommended)

```bash
curl -X POST 'http://localhost:3000/api/v1/market-study/delete-daily-cache' \
  -H 'Authorization: abcd' -H 'Content-Type: application/json'
```

Or set `AWS_S3_BUCKET_DAILY_CACHE_PERMISSION_WRITE=false` in `.env` to skip writes (reads still work).

### 5. Start worker and trigger

```bash
APPLICATION_MODE=WORKER npm run start:dev
```

```bash
curl -X POST http://localhost:3000/api/v1/market-study/crawl-brands-and-models \
  -H 'Authorization: abcd' -H 'Content-Type: application/json' \
  -d '{"sites": ["<site>"]}'
```

Multiple workers are fine — port 3000 conflict on the 2nd+ instance is harmless; RMQ consumers still attach.

### 6. Monitor success rate (Graylog)

In Graylog (`$GRAYLOG_API_URL` prod or `http://graylog.devenv:8090` local):

```
# Successful ScrapeDo requests
facility:marketstudy* AND site:[SITE] AND message:"Finished scrapeDo request"

# Failed ScrapeDo requests
facility:marketstudy* AND site:[SITE] AND message:"Exception doing scrapeDo request"

# Credit lock triggered (expensive tier auto-upgraded >9x)
facility:marketstudy* AND site:[SITE] AND message:"ScrapeDo - activated credits lock"

# Cost overrun (tier auto-upgraded but not locked yet)
facility:marketstudy* AND site:[SITE] AND message:"Request cost is bigger than max cost"

# Site locked (skipping requests due to lock)
facility:marketstudy* AND site:[SITE] AND message:"Starting scrapeDo request" AND errorCode:"SCRAPE_DO_CREDITS_LOCKED"
```

**Success rate = `Finished` / (`Finished` + `Exception`) × 100**

Use the Graylog API with `POST /api/views/search/sync` (see `graylog-queries.md`) to get exact counts.

### 7. Pass/fail criteria

| Rate | Verdict |
|---|---|
| ≥ 60% | Good — ship it |
| 40–60% | Acceptable — monitor for a day before deciding |
| < 40% | Too low — escalate tier or contact support |

Context: Subito on DataDome proxies hit 60% on fresh proxies, dropped to 30% after a backfill burned proxy reputation. ScrapeDo residential proxies rotate automatically so reputation burn is less of an issue.

### 8. If success rate is insufficient

1. **Escalate tier** — bump `browserAtRetry: 2` or `superBrowserAtRetry: 3` in proxyConfig. Re-test.
2. **Contact scrape.do support** — account `tt@preskok.si`. Provide site URL + example blocked URLs + current credits used. They can allowlist the site (worked for hasznalt-auto, car-gr). **Never test with a personal account** — Matea's was permanently banned after <50 credits on avto-net.
3. **Check the credits lock** — if `"ScrapeDo - activated credits lock"` appears, scrape.do is auto-upgrading. Declare the higher tier explicitly in proxyConfig so the cost check passes cleanly.
4. **Wait / retry next day** — if proxy IPs were burned by a large run, success rate may recover on its own after 24h.

### 9. Before creating PR

- Remove the brand filter from `getBrandsAndModels()`
- Re-enable `AWS_S3_BUCKET_DAILY_CACHE_PERMISSION_WRITE` if you disabled it
- Remove any `console.log` / test leftover
- Run `npx prettier --write src/crawler/sites/<Site>/<Site>.service.ts && npx eslint --fix src/crawler/sites/<Site>/<Site>.service.ts`

---

## Emergency disable during crawl

1. Purge queue (stops new message processing)
2. Disable via config (requires deploy)
3. Monitor DL queues for trailing issues
4. Lock deactivation if near 22:00

---

## Investigation techniques (non-code)

### Next.js App Router site — where to find parseable data

Sites using Next.js App Router (identified by absence of `__NEXT_DATA__` script tag and presence of `self.__next_f.push([1,"..."])` inline scripts) embed data in RSC streaming payload in the static HTML. No JS execution needed.

**Step 1 — detect App Router vs Pages Router:**
```bash
grep -c '__NEXT_DATA__' response.html   # Pages Router: >0. App Router: 0
grep -c 'self.__next_f' response.html   # App Router: >0
```

**Step 2 — find data in RSC pushes:**
```python
import json, re
pushes = re.findall(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\[\s\S])*)"\]\)', body)
for i, p in enumerate(pushes):
    decoded = json.loads('"' + p + '"')   # decode JS string literal
    if '"posts":[' in decoded or '"makes":[' in decoded:
        print(f'push[{i}] has data')
        # look for field names: posts, makes, products, listings, items, data, results
```

**Step 3 — extract with balanced bracket parser** (implemented in `AutoConnect.service.ts` as `extractFromRscPayload` + `extractJsonArray`).

**Key pattern:** main/unfiltered listing page has full `posts` array. Brand-path pages (`/BMW`) may return only featured posts (~4). Brand+model query-param pages (`?make1=BMW&model1=3-Series`) return full filtered posts.

**`autoconnect.interoffice.al` lesson:** if the site's RSC pushes contain skeleton components and no data, the data comes from an internal backend domain. Check `<link rel="preconnect">` headers — if it's an internal subdomain (e.g. `*.interoffice.*`, `*.internal.*`), JS-enabled Puppeteer won't help because DNS won't resolve externally.

**Source:** session 2026-06-01 (auto-connect HTML refactor investigation).

### ScraperAPI per-domain stats
Dashboard shows success/fail per credit tier. Project `requests/day × avg credits` to decide disabling.

### Real counter discovery (mobile-bg pattern)
Query each brand-model API's `adverts_counter` field, sum:
```js
arr.map(Number).reduce((a,b) => a+b, 0)
```

### ES unique-URL query (Confluence)
"Get daily number of unique URLs from old search index" — accurate count (avoids duplicates from crumbling retries).

### Match RMQ re-delivery to listing timeouts
For each listing appearing multiple times in "LISTING_URL started" logs:
1. Grab `request_id`
2. Find "Response found in S3" at end
3. Check timespan ~30 min (default RMQ ACK timeout) = indicates redelivery

### Detail-page regression via ES
If all ES-saved vehicles for a day have `IsListingValidatedVehicle=true`, the details save step is broken (hasznalt-auto price parse death).

### Grafana instance up/down
Cross-check with RMQ duplicates to confirm "instance-died" pattern.

---

## Code Patterns — Crawler Implementation Quality

### RSC payload extraction (Next.js App Router sites)

Copy `extractFromRscPayload` + `extractJsonArray` from `AutoConnect.service.ts` into any App Router site's service. Finds any named array in the RSC streaming payload without JS execution.

```typescript
private extractFromRscPayload(html: string): { posts: Record<string, unknown>[]; makes: string[] } {
    const result = { posts: [] as Record<string, unknown>[], makes: [] as string[] };
    if (!html) return result;

    const scriptRegex = /self\.__next_f\.push\(\[1,"((?:[^"\\]|\\[\s\S])*)"\]\)/g;
    let match: RegExpExecArray | null;
    while ((match = scriptRegex.exec(html)) !== null) {
        let decoded: string;
        try { decoded = JSON.parse(`"${match[1]}"`); } catch { continue; }

        if (!result.makes.length) {
            const idx = decoded.indexOf('"makes":[');
            if (idx !== -1) { const arr = this.extractJsonArray(decoded, idx + 8); if (arr) try { result.makes = JSON.parse(arr); } catch {} }
        }
        if (!result.posts.length) {
            const idx = decoded.indexOf('"posts":[');
            if (idx !== -1) { const arr = this.extractJsonArray(decoded, idx + 8); if (arr) try { result.posts = JSON.parse(arr); } catch {} }
        }
        if (result.makes.length && result.posts.length) break;
    }
    return result;
}

private extractJsonArray(text: string, startIdx: number): string | null {
    let depth = 0, i = startIdx;
    while (i < text.length) {
        const c = text[i];
        if (c === '[' || c === '{') depth++;
        else if (c === ']' || c === '}') { depth--; if (depth === 0) return text.slice(startIdx, i + 1); }
        else if (c === '"') { i++; while (i < text.length && text[i] !== '"') { if (text[i] === '\\') i++; i++; } }
        i++;
    }
    return null;
}
```

**Field names to try:** `posts`, `makes`, `listings`, `vehicles`, `products`, `items`, `results`, `data`, `ads`.
**Source:** session 2026-06-01 (auto-connect refactor).

Apply these automatically when implementing or reviewing any crawler. These were established through Eurostocks refactoring session.

### Working URL fix — 3-step checklist

Per [Working URL docs](https://preskok.atlassian.net/wiki/spaces/M/pages/3002302476/Working+URL+fix):

**For `shouldValidateListingVehicle: false` / small crawlers — all 3 steps at once:**
1. Override `fetchRequest()` to rewrite URLs before requesting:
   ```ts
   public async fetchRequest(url, options) {
       const requestUrl = url?.includes('/vehicle/') ? this.getWorkingUrl(url) : url;
       return super.fetchRequest(requestUrl, options);
   }
   ```
2. Details parsing: `url: parseVehicleParams.url` (legacy), `workingUrl: partialVehicle?.workingUrl` (working)
3. Listing parsing: set both `url` (legacy) and `workingUrl` (working) in `partialVehicle`; `VehicleListItem.url` = legacy

**For `shouldValidateListingVehicle: true` / big crawlers — gradual rollout:**
- Phase 1: details-only `workingUrl`. Let it propagate over days/weeks.
- Phase 2: add `workingUrl` to listing partial. Now most S3 vehicles already have it → no spike.
- Adding `workingUrl` to listing before Phase 1 completes causes all vehicles to fail listing check → full details spike.

**Adding `shouldValidateListingVehicle` to a crawler that has workingUrl in listing already:**
- Existing S3 vehicles have no `workingUrl` → first run will re-detail all of them (spike)
- For small sites: acceptable one-time cost
- For large sites: Phase 1 first (details only), then add flag + listing workingUrl

### Avoid double-parsing in parseDealer

`parseDealer` is called right after `parseVehicleInput` in the same details fetch. If both need the same parsed data (RSC chunk, JSON object), pass it via `additional`:

```ts
// In parseVehicleInput:
parseVehicleParams.additional = { detailsData };

// In parseDealer signature:
parseDealer(parseDealerParams: ParseDealerParams<string, { detailsData: MyDetailType }>)

// In parseDealer body:
const detailsData = parseDealerParams.additional.detailsData;
```

No cast needed — generic types the field correctly.

### Listing → Details fallbacks

Every field parsed from listing that is also parsed in details should have a `|| partialVehicle?.field` fallback as last resort in details. Fields to always check: `name`, `rawVersion`, `rawTransmission`, `rawFuelType`, `mileage`, `rawMileage`, `price`, `rawPrice`, `rawBrand`, `rawModel`.

### Contact/address building — no template literals

Template literals produce undefined/empty/space artifacts when fields are missing. Use `filter(Boolean).join()`:

```ts
// Name
[dealerInfo.FirstName, dealerInfo.LastName].filter(Boolean).join(' ')

// Address line
[dealerInfo.Street, dealerInfo.HouseNumber, dealerInfo.HouseNumberExtension].filter(Boolean).join(' ')

// Full address
[city, address].filter(Boolean).join(', ')
```

### Skip logs

Every early `return` in `parseVehicleInput` / listing forEach that discards a vehicle must have a `this.logger.warn(...)` with `LoggingContexts.PARSER_DEBUGGING`. Minimum fields: `message`, `site: this.site`, `url` (for details) or `itemId` (for listing). This is what lets you diagnose production skip rates without deploying new code.

### Inline single-use private methods

If a private method is called only once and the logic is trivial, inline it with a comment:
```ts
// details URLs contain /vehicle/ and need to be rewritten to the current working format
const requestUrl = url?.includes('/vehicle/') ? this.getWorkingUrl(url) : url;
```

### Extract repeated field accesses to variables

If `dealerInfo.City` or `dealerInfo.PostalCode` appear more than once, extract:
```ts
const city = dealerInfo.City;
const zip = dealerInfo.PostalCode;
```

### parseDealer independence check

Before adding `parseDetailsScript()` or similar wrappers inside `parseDealer`, check if `parseDealer` is ever called independently (without a prior `parseVehicleInput`). If not — remove the wrapper and pass via `additional`. In HTML crawlers, `parseDealer` is always called after `parseVehicleInput` in the same `parseVehicle()` flow.

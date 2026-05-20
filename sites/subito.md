# subito (IT)

## Current status
🟡 **Operational with degraded success rate.** DataDome cookie-persistence fix deployed to prod 2026-04-30 (`bugfix/MAR-2039-subito-datadome-cookie`). After May 01 high-volume backfill, proxy reputation degraded — overall success rate locked at ~30% (vs 60% on day 1). Vehicles saved per day stabilized at ~220-255k (vs 400-468k on first two days). Listing completion is rock solid (~1100-1200 listings/day, 98%+ finish rate).

## History & quirks (newest first where known)
- **2026-05-04** — Found and fixed silent gap in `trySolveDataDome`: the `hasDataDomeCookie in Redis` branch only LOGGED "datadome cookie invalidated server-side despite being present in Redis" but never called `createValidDataDomeCookie`. So when DataDome invalidated a Redis-stored session, every retry just hit 403 → no recovery → producer crash (`getMappedBrandsAndModels` returns null → destructure throws). Local repro: warm session run prepares 11 listings; delete S3 daily cache + run again → "datadome cookie invalidated" × 3 + "Problem preparing". After fix: invalidated branch also calls `createValidDataDomeCookie`, so PARSER_DEBUGGING shows `start special logic for data dome` → `good special logic for data dome` instead of just the warning. Recovery still fails when proxy is IP-blocked at the network level (recovery URL also 403, original retry 403) — that's an infra problem, not code. Stage testing inconclusive: `Problem preparing` events found in Graylog were all timestamped BEFORE the cold-start commit (`c932034b` at 12:16) was deployed; no run has been triggered since deploy. **Lesson: when claiming "stage runs old code," verify by matching crash timestamp to commit deploy time, not by recognizing log strings (some debug strings exist in both old and new code).**
- **2026-05-04** — Bugfix branch rebased onto master, only two logical changes vs master: (1) `afterRequest` cookie persistence on 403 (the MAR-2039 fix), (2) chunk URL fix in `getMappedBrandsAndModels` (remove double-slash + add `fetchRequestOptions` so chunk JS goes through DataDome proxy flow). PR opened from bugfix → master.
- **2026-05-02 → 2026-05-03** — Success rate plateaued at ~30% overall (HTTP 39%, browser 19%). `forbidden` count creeping up (~10,800/day). `no_proxy_cook` settled at 7-8k/day vs 1,325 on day 1 — proxies that got burned on May 01 haven't recovered sessions. Recovery success steady at ~51%.
- **2026-05-01** — Massive volume spike: 254k requests (~4× normal). Looks like a backfill ran alongside regular crawl. Burned proxy reputation: success rate immediately dropped from 60% → 30%. `no_proxy_cook` spiked to 29,604 (22× day 1). Yet 468k vehicles saved due to sheer volume.
- **2026-04-30** — DataDome cookie-persistence fix (Change A) deployed to prod ~12:30 (partial day, ~29k requests). Success rate 60% — proxies fresh, DataDome hadn't fingerprinted them yet. 403k vehicles saved.
- **2026-04-29** — Production effectively dead (only 302 vehicles saved). Staging tests failed 5x in a row — root cause was the bad `enableJavaScript:true` cold-start change (Change B): Puppeteer request interceptor blocked DataDome challenge XHRs, killing `getMappedBrandsAndModels` entirely. Reverted; only kept Change A (afterRequest cookie persistence).
- **2026-04-28** — Pre-fix baseline: 271k vehicles. Hotfix was running with both Change A and Change B in prod (Change B less catastrophic in prod than staging, but still suboptimal).
- Selector churn monthly.
- Brand aliases in ~30 webpack chunks (`_next/static/chunks/*.js`).
- Smart `#1` → city-coupé/cabrio re-map (2025-02 Smart #1 `#` fragment collapsed to all Smart).
- Description emojis → BULK_SAVE_DL.
- 2025-04-24 browser-request migration (axios 403+proxy retries).

## DataDome architecture (active as of MAR-2039)

**Key files:** `src/crawler/sites/Subito/Subito.service.ts`, `src/crawler/utils/data-dome/data-dome.service.ts`

**Pool layout** (Redis DB5):
- `marketstudy_data-dome-subito-proxy` — MAIN pool (proxies 8010-8019, stable IPs, 67% of requests)
- `marketstudy_data-dome-subito-changeable-proxy` — CHANGEABLE pool (8021-8025, rotating, 33%)

**Per-request flow:**
1. `beforeRequest` picks pool, injects proxy + that proxy's cached cookieJar + UA from Redis
2. Request runs — axios (75% if proxy already has DataDome cookie / 60% if has session / 20% if cold) or browser (Puppeteer with `setJavaScriptEnabled(false)`)
3. `afterRequest` runs `trySolveDataDome` (probabilistic recovery on 403 — 20% stable / 33% changeable). The recovery flow visits `/annunci-italia/vendita/auto/` to validate/refresh the cookie. **Then persists cookieJar + UA back to Redis** — this is where MAR-2039 was broken: failure path passed `ex` directly, triggering the error branch in `updateProxyAfterRequest` which never saved the freshly-issued cookie.

**The MAR-2039 fix** (in `afterRequest`): after `trySolveDataDome`, if the result is still failed but the cookieJar now contains a `datadome` cookie, override `ex=null` and `response={statusCode:200}` before calling `updateProxyAfterRequest` — forces the save branch. Result: cookies acquired during recovery actually get persisted, so subsequent requests on that proxy have a session.

**Three branches in `trySolveDataDome` on 403** (all three now actually do recovery — the third was previously a silent log):

| Redis state | Probability gate | Action |
|---|---|---|
| `!cookies.length` (cold start) | 100% | call `createValidDataDomeCookie` |
| `hasDataDomeCookie = true` but 403 (invalidated) | 20% stable / 33% changeable | log warning + call `createValidDataDomeCookie` ← was missing pre-2026-05-04 |
| `hasCookies` but `!hasDataDomeCookie` | 20% / 33% | check jar; if jar has fresh DataDome cookie from Set-Cookie, call `createValidDataDomeCookie`; else log "browser must bootstrap" |

**Why axios beats browser on cold start:** when no DataDome cookie exists, browser request via Puppeteer's `page.goto()` throws on 403 → early-return path → `page.cookies()` never runs → DataDome's `Set-Cookie` from the 403 response is lost. Axios with `createCookieAgent` (tough-cookie) DOES capture it. So `fetchRequest` does `!hasCookies → always axios`, never browser, on cold start.

## Graylog log messages used in this crawler

For day-by-day analysis (filter `site:subito AND facility:marketstudy`):

| Message | Meaning |
|---|---|
| `Finished HTTP request` | Successful axios request |
| `Exception doing HTTP request` | Axios exception (timeout, conn reset, etc.) |
| `Could not complete HTTP request` | Axios request failed (rare, distinct from exception) |
| `Finished browser request` | Successful Puppeteer request |
| `Exception doing browser request` | Puppeteer request failed (often 403) |
| `Response was forbidden` | 403 received (DataDome block) |
| `Retry attempt` | Outer retry loop fired |
| `403 with no DataDome cookie on proxy — recovery skipped, browser must bootstrap session on next attempt` | Proxy is fully cold, can't even attempt recovery |
| `proxy has no cookies in Redis — fresh proxy, no session established yet` | First request on a fresh proxy |
| `datadome cookie invalidated server-side despite being present in Redis` | Cookie was valid in Redis but DataDome rejected it |
| `validating DataDome cookie via protected listing URL before retrying original` | Recovery flow started |
| `DataDome recovery succeeded — retrying original URL with refreshed cookie` | Recovery worked |
| `recovery URL blocked but fresh DataDome cookie received — retrying original URL` | Recovery URL still 403 but got new cookie via Set-Cookie |
| `Started crawling listing url` | Listing page producer fired |
| `Finished crawling listing url` | Listing page producer completed |

## Producer crash semantics (DO NOT mask)

`getBrandsAndModels()` destructures `getMappedBrandsAndModels()` directly:
```ts
const { mappedBrands, mappedModels } = await this.getMappedBrandsAndModels();
```

When `getMappedBrandsAndModels()` returns `null` (5 outer retries × multiple chunks all failed), this destructure throws `TypeError: Cannot destructure property 'mappedBrands' of null`. That exception propagates → emits `Problem preparing listingUrl messages for site!` → triggers the auto-retry at 6/7/8 AM.

**Do NOT add a null guard returning `[]`.** That would emit `Prepared 0 listingUrl messages` instead, which does NOT auto-retry. The crash IS the retry mechanism. Confirmed twice in different sessions — once Claude added a guard "to be safe" and got reverted.

## Improvement suggestions (not yet implemented)

1. **Proxy reputation rotation** — when a proxy's success rate drops below threshold, swap it out and let it cool down 24h before reintroducing.
2. **Cookie pre-warming** — before bulk crawl starts, send lightweight requests from each proxy to establish/refresh sessions, avoiding cold-start tax during real crawling.
3. **Recovery URL diversity** — currently always `/annunci-italia/vendita/auto/`. Rotating across 3-4 protected URLs would make the pattern less fingerprintable.
4. **Adaptive axios/browser ratio** — bump browser % temporarily for proxies with recently-invalidated cookies.
5. **Backfill crawl isolation** — large re-crawls (like the May 01 spike) should use a separate proxy pool so daily crawls don't get caught in fallout.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

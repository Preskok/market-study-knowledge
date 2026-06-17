---
name: crawler-test-flow
description: >
  ALWAYS invoke this skill when the user's message starts with "crawler-test-flow"
  followed by anything — e.g. "crawler-test-flow autoplius", "/crawler-test-flow subito",
  "crawler-test-flow auto-connect --paginate". Local-only end-to-end crawler flow tester
  for Market Study. Refuses to run against stage/prod. Verifies the pipeline reaches
  Elasticsearch with vehicles for one site/brand/model in under 60 seconds. Does NOT
  validate vehicle data quality (use crawler-data-validation for that). Single-source
  of truth for "did this crawler run end-to-end?" — every ✅ is backed by ES rows or a
  Graylog log line whose timestamp is greater than TEST_START_TS.
---

# crawler-test-flow — End-to-End Crawler Flow Test (Local)

Exercises the full crawl pipeline (`getBrandsAndModels` → listing fetch → `parseVehicleInput` → `parseEquipment` → `parseDealer` → bulk-save) for one site against a known-good narrowed sample, and reports pass/fail per phase.

> ⚠️ **Cardinal rule:** never ✅ without evidence whose timestamp ≥ `TEST_START_TS`. Evidence comes from local ES rows (primary) or Graylog log lines (secondary). No log/no rows ≠ pass.

---

## Trigger

| Command | Meaning |
|---|---|
| `crawler-test-flow [site]` | Standard run with the per-site known-good brand+model from `~/Projects/market-study-knowledge/sites/[slug].md` |
| `crawler-test-flow [site] --brand=X --model=Y` | Override the brand+model |
| `crawler-test-flow [site] --paginate` | Also verify pagination (≥2 listing pages — costs an extra rotation if the brand has <maxResults) |
| `crawler-test-flow [site] cleanup` | Skip everything else, revert all temporary mods |

`[site]` resolved via `~/Projects/market-study-knowledge/aliases.json` (same as `crawler-info`).

---

## Pipeline (one screen)

```
Phase 0   Detect crawler shape, look up known test brand+model         (read-only)
Phase 1   Pre-flight: worker / ES / VPN / pre-existing rows for brand   (read-only)
Phase 2   Apply test mod (Strategy A for nested-loop HTML; Strategy B for single-source/API)
Phase 3   Cache write-disabled, capture TEST_START_TS, trigger curl
Phase 4   Poll ES for rows since TEST_START_TS                          (primary verdict)
Phase 5   One combined Graylog query for getBrandsAndModels + errors    (secondary)
Phase 6   Emit report
Phase 7   Revert mods, clear changes-applied.json
```

Phases 0–3 must complete in under 60 seconds of wall-clock work. Phase 4 polls up to 90s. Total ~2 min, ~6 tool calls in the happy path.

---

## Phase 0 — Crawler shape + test pair

```bash
SLUG=$(jq -r --arg t "$INPUT" '.[$t // ($t|ascii_downcase) | tostring] // empty' ~/Projects/market-study-knowledge/aliases.json)
SVC="src/crawler/sites/$(echo "$SLUG" | sed 's/-//g; s/^./\U&/')/$(echo "$SLUG" | sed 's/-//g; s/^./\U&/').service.ts"
# (Adjust path resolution if the service folder uses CamelCase that doesn't match — fall back to find.)
```

Read the service file once and capture in one pass:

| Attribute | How |
|---|---|
| HTML or API | `grep -E "extends (HtmlAdVehicleCrawlerAbstract\|ApiAdVehicleCrawlerAbstract)" $SVC` |
| `parseDealer` overridden | `grep -nE "^\s+(public\|protected\|private)\s+parseDealer\s*\(" $SVC` |
| Uses VPN-only proxy | `grep -nE "PRESKOK_SET_\|specificProxy" $SVC` |
| `shouldValidateListingVehicle` | `grep -A6 "AdSiteKeysEnum.[A-Z_]*${SLUG_ENUM}" src/shared/const/CrawlingSites.ts \| grep shouldValidate` |

**Test brand+model lookup** — `grep -A1 "^## Test brand+model" ~/Projects/market-study-knowledge/sites/$SLUG.md`. Expected format inside that section:

```markdown
## Test brand+model
- brand: Volkswagen
- model: Golf
```

If the section is missing, ask the user once: *"No known test pair for [site]. Use first brand alphabetically, or do you have a popular brand+model in mind?"* — wait for input, then **after a successful run, append the section to the per-site file** so the next run is zero-question.

If `--brand=`/`--model=` flags were passed on the command line, use those instead and skip the lookup.

---

## Phase 1 — Pre-flight smoke check (one parallel block)

Run all four checks in a single message:

```bash
# 1. Worker on :3000
lsof -i :3000 | grep -E "node|nest" || echo "❌ no worker"

# 2. ES is local (refuse if not)
grep -E "^ELASTIC_SEARCH_URL=" .env

# 3. VPN reachable (only if Phase 0 found PRESKOK_SET_*)
nc -z -w 2 proxy.b2b-carmarket.eu 9001 && echo "vpn ok" || echo "❌ vpn down"

# 4. Existing rows for THIS brand+model already in ES (SVL idempotency check)
ES=$(grep ^ELASTIC_SEARCH_URL= .env | cut -d= -f2)
curl -s "$ES/marketstudy_search_rollover/_count" -H 'Content-Type: application/json' -d '{
  "query": {"bool": {"must": [
    {"term": {"Site": "[slug]"}},
    {"term": {"Brand": "[brand-lowercase]"}},
    {"term": {"Model": "[model-lowercase]"}}
  ]}}
}' | jq .count
```

**Refuse to start if:**
- No worker → **Claude starts it** (user does not): `npm run start:dev >> /tmp/market-study-dev.log 2>&1 &` then `until tail -20 /tmp/market-study-dev.log | grep -q "Nest application successfully started"; do sleep 3; done`. **CRITICAL: use `tail -20`, not the whole log** — the log accumulates old startup messages from prior runs, so `grep` on the whole file returns immediately even when the new process hasn't started yet. Do **not** use `APPLICATION_MODE=WORKER` — unset mode loads full stack (crawler + bulk-saver in one process); WORKER mode skips the bulk-saver and vehicles never reach ES. Record `"server_started_by_claude": true` in `changes-applied.json` so Phase 7 knows to kill it.
- ELASTIC_SEARCH_URL doesn't contain `devenv` or `localhost` → STOP, refuse.
- VPN required and proxy host unreachable → ask user to connect VPN, then continue.
- **Existing rows >0 AND `shouldValidateListingVehicle:true`** → SVL idempotency trap is loaded. Two options:
  - (a) Delete them: `curl -X POST "$ES/marketstudy_search_rollover/_delete_by_query" -H 'Content-Type: application/json' -d '{"query": {"bool": {"must": [{"term": {"Site": "[slug]"}}, {"term": {"Brand": "[b]"}}, {"term": {"Model": "[m]"}}]}}}'`
  - (b) Pick a different brand+model.
  - Ask user which.

---

## Phase 2 — Apply test mod

**Detect the loop structure first** — scan `getBrandsAndModels()` for nested `for` loops:
- `for (brand) { ... for (model) { brandsAndModels.push } }` → **Strategy A** (break inside, breaks out fast)
- `for (brand) { ... for (superModel) { ... for (model) { brandsAndModels.push } } }` → **Strategy A with 3 levels** — apply breaks at the model loop, the superModel loop, AND the brand loop. Same pattern, one extra level. Example: pazar3.
- Single loop or direct API call with one push → **Strategy B** (find at end)

HTML crawlers with nested brand+model loops MUST use Strategy A. Strategy B on a site that walks 30+ brands first takes 30–50 minutes.

### Strategy A — break-on-first-push (nested-loop HTML crawlers)

Insert two break lines inside `getBrandsAndModels()` — one after the first `push`, one after the inner loop closes:

```ts
for (const brand of brands) {
    // ...existing fetch logic untouched...
    for (const model of models) {
        // ...existing build logic untouched...
        brandsAndModels.push({ brandName, modelName, listingUrl, site: this.site });
        break; // TODO - claude /crawler-test-flow skill added this, remove after the test
    }
    if (brandsAndModels.length > 0) break; // TODO - claude /crawler-test-flow skill added this, remove after the test
}
return brandsAndModels;
```

If the target brand+model is unlikely to be first alphabetically (check per-site file), insert a conditional push instead:
```ts
if (brandName === '[BRAND]' && modelName === '[MODEL]') {
    brandsAndModels.push({ brandName, modelName, listingUrl, site: this.site });
    break; // TODO mod
}
```

### Strategy B — find at end (single-source or API crawlers)

```ts
async getBrandsAndModels(): Promise<...> {
    const brandsAndModels: Array<...> = [];
    // ...existing loops untouched...
    // TODO - claude /crawler-test-flow skill added this, remove after the test
    return [brandsAndModels.find((b) => b.brandName === '[BRAND]' && b.modelName === '[MODEL]') ?? brandsAndModels[0]];
}
```

---

Set `AWS_S3_BUCKET_DAILY_CACHE_PERMISSION_WRITE=false` in `.env` (default cache strategy — write-disabled, no cache pollution between iterations, cache reads still work for speed).

Record both changes in `~/.claude/skills/crawler-test-flow/changes-applied.json`:

```json
{
  "site": "[slug]", "brand": "[BRAND]", "model": "[MODEL]",
  "started_at": "[TS]",
  "strategy": "A|B",
  "server_started_by_claude": true,
  "changes": [
    {"file": "src/crawler/sites/[Site]/[Site].service.ts", "kind": "narrow-to-break|narrow-to-find"},
    {"file": ".env", "kind": "cache-write-disabled"}
  ]
}
```

`git diff --stat` and proceed — do **not** ask "apply these mods?" The mod is mechanical and will be reverted in Phase 7.

Wait for nest to recompile: `until tail -20 /tmp/market-study-dev.log | grep -qE "Nest application successfully started"; do sleep 3; done`. **Use `tail -20` not the whole log** — prior startup messages in the file cause immediate false-positive match. Also verify the compiled JS reflects the change before triggering: `grep -n "the-filter-string" dist/src/crawler/sites/[Site]/[Site].service.js`.

---

## Phase 3 — Trigger

```bash
API_TOKEN=$(grep -E "^API_TOKEN=" .env | cut -d= -f2)   # NOT http-client.env.json — that's a placeholder
TEST_START_TS=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)        # capture immediately before the trigger curl
curl -s -X POST "http://localhost:3000/api/v1/market-study/crawl-brands-and-models" \
  -H "Authorization: $API_TOKEN" -H "Content-Type: application/json" \
  -d '{"sites": ["[slug]"]}'
echo "TEST_START_TS=$TEST_START_TS"
```

---

## Phase 4 — ES verification (primary verdict)

ES sees vehicles directly. Poll every 10s up to 90s for the count to climb. **Stop polling on the first hit** (don't keep polling after it goes >0):

```bash
ES=$(grep ^ELASTIC_SEARCH_URL= .env | cut -d= -f2)
SLUG="[slug]"
TS="$TEST_START_TS"
for i in $(seq 1 9); do
  sleep 10
  R=$(curl -s "$ES/marketstudy_search_rollover/_search" -H 'Content-Type: application/json' -d "{
    \"size\": 0,
    \"query\": {\"bool\": {\"must\": [
      {\"term\": {\"Site\": \"$SLUG\"}},
      {\"range\": {\"CreatedAt\": {\"gte\": \"$TS\"}}}
    ]}},
    \"aggs\": {
      \"with_dealer\":    {\"filter\": {\"exists\": {\"field\": \"DealerId\"}}},
      \"with_equipment\": {\"filter\": {\"exists\": {\"field\": \"Equipment\"}}}
    }
  }" | jq -c '{total: .hits.total.value, dealers: .aggregations.with_dealer.doc_count, equipment: .aggregations.with_equipment.doc_count}')
  echo "$i: $R"
  if [ "$(echo "$R" | jq .total)" -gt 0 ]; then break; fi
done
```

Verdict from the final `R`:

| Field | What it means |
|---|---|
| `total > 0` | parseVehicleInput → bulk-save → ES write happened ✅ |
| `total = 0` after 90s | Pipeline didn't write. Check Phase 5 for getBrandsAndModels failures + DL + SVL idempotency. ❌ |
| `dealers > 0` | parseDealer extracted at least one dealer ✅ |
| `dealers = 0` and `parseDealer` overridden | ⚠️ — could be private-seller-only sample, OR selector is stale. Note in report. |
| `equipment > 0` | parseEquipment populated the field on at least one doc ✅ |

**Pagination** (only if `--paginate` flag was passed): the `getListingRequestOptions` in most crawlers includes `page` in the `vehicleListUrl`. Run an additional aggregation:
```json
"aggs": {"pages": {"cardinality": {"field": "VehicleListUrl.keyword"}}}
```
≥2 distinct values → pagination ✅. If <2, rotate to a different brand once and retry. After one rotation, accept ⚠️ "site has insufficient data on tested brands; pagination unverifiable" and stop.

---

## Phase 5 — Single Graylog batch query (secondary)

One POST covers four signals:

```bash
GL=$(grep ^GRAYLOG_API_URL= .env | cut -d= -f2)
TOK=$(grep ^GRAYLOG_AUTH_TOKEN= .env | cut -d= -f2)
NOW=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)
curl -s -X POST -u "$TOK:token" \
  -H "Content-Type: application/json" -H "X-Requested-By: curl" \
  "$GL/api/views/search/sync?timeout=30000" -d "{
    \"queries\": [{
      \"id\": \"q1\",
      \"timerange\": {\"type\": \"absolute\", \"from\": \"$TEST_START_TS\", \"to\": \"$NOW\"},
      \"query\": {\"type\": \"elasticsearch\", \"query_string\":
        \"facility:marketstudy-local AND site:[slug] AND (message:\\\"Prepared listingUrl messages\\\" OR message:\\\"Problem preparing listingUrl messages\\\" OR message:\\\"Too many retries for message, discarding it\\\" OR (level:3 AND NOT context:FETCH_EXTERNAL AND NOT context:RMQ_INFO))\"
      },
      \"search_types\": [{\"id\": \"st1\", \"type\": \"messages\", \"limit\": 50, \"offset\": 0}]
    }]
  }" | jq '.results.q1.search_types.st1.messages[].message | {timestamp, message}'
```

Parse the message types:
- `Prepared listingUrl messages 1...` → getBrandsAndModels ✅ (numberOfMessages > 0)
- `Problem preparing listingUrl messages` → getBrandsAndModels ❌ (producer threw)
- `Too many retries...` → DL hits, flag at report level
- Other level:3 entries → list verbatim in report

If Phase 4 said `total = 0` AND Phase 5 has no `Prepared listingUrl messages`, the failure is at getBrandsAndModels (likely VPN/proxy or selector). If Phase 4 said `total = 0` AND Phase 5 has `Prepared listingUrl messages 1`, the failure is downstream (parseVehicleInput, SVL skip, anti-bot).

---

## Phase 6 — Report

```
# crawler-test-flow — [site] [brand]/[model]

**Window:** [TEST_START_TS] → [NOW]   |   **Shape:** [HTML/API]   |   **Cache:** write-disabled

| Phase | Verdict | Evidence |
|---|:-:|---|
| getBrandsAndModels | ✅ | Graylog: "Prepared listingUrl messages 1" at HH:MM:SSZ |
| listing + parseVehicleInput | ✅ | ES: N rows for Site:[slug] CreatedAt>=[TS] |
| parseEquipment | ✅/⚠️ | ES: K/N rows have Equipment populated |
| parseDealer | ✅/⚠️/N/A | ES: K/N rows have DealerId; parseDealer overridden=true/false |
| pagination | ✅/⚠️/skipped | ES: D distinct VehicleListUrl values (only when --paginate) |
| Final save | ✅ | Implicit in ES total > 0 |

## Cross-checks
- DL hits: [N]   |   Error logs: [N]   |   Worker alive: yes/no

## Verdict
[Lead with failures if any. ✅ Flow OK if everything passed. Note any ⚠️ with what to investigate.]
```

If the report is the first successful run for this site **and** the user had to specify the brand+model, append the test pair to `~/Projects/market-study-knowledge/sites/[slug].md` so the next run skips the question:

```markdown
## Test brand+model
- brand: [BRAND]
- model: [MODEL]
- verified: [YYYY-MM-DD]
```

---

## Optional — Pivot to live debug on red

If Phase 4 returns `total = 0` and Phase 5 doesn't pinpoint the failure (e.g. listing prepared OK but no ES rows), re-launch with `npm run start:debug` instead of `start:dev` and attach via the `debugger-mcp` MCP to step through `parseVehicleInput` on the actual message. See the **Live Debug** section of the `crawler-debug` skill for the full tool sequence.

If you do this:
- Kill the existing watcher first (`kill $(lsof -ti :3000)`) — the inspect port (9229) accepts only one client.
- Record `"debug_server_started_by_claude": true` in `changes-applied.json` so Phase 7 kills the debug process too.

---

## Phase 7 — Cleanup

For each entry in `changes-applied.json`:
1. Show the diff line.
2. Apply the revert via Edit (default — no prompt, since mods are mechanical and tracked).
3. Confirm: `git diff src/crawler/sites/[Site]/[Site].service.ts .env` should be empty.
4. Delete `changes-applied.json`.
5. **Kill the dev server if Claude started it in Phase 1** — `kill $(lsof -ti :3000)`. Do not leave orphan nest watch processes running.

If the user runs `crawler-test-flow [site] cleanup`, jump straight here.

---

## Pitfalls — what to look for, what to do

| Pitfall | Detection | Recovery |
|---|---|---|
| SVL idempotency: existing rows for tested brand → no new rows on rerun | Phase 1 ES count > 0 | Delete by query OR pick a fresh brand |
| S3 cache idempotency: vehicles same as cached run, `searchVehiclesSize: 0` | (rare with write-disabled default) | Use Phase 1 cache delete or pick fresh brand |
| Stale "Finished saving" leaking into window | Always filter by TEST_START_TS | Built into all queries |
| Stale old-code server consuming RMQ tasks — fix looks broken but isn't | New server logs `EADDRINUSE` at startup, or `ps aux \| grep -E "node\|nest"` shows extra PIDs; "Prepared listingUrl messages 0" despite code being correct | Kill ALL stale node PIDs: `ps aux \| grep -E "(node\|nest)" \| grep market-study \| awk '{print $2}' \| xargs kill`. Then trigger again. Root cause: `nest start --watch` spawns a child; if a prior watcher/child is still alive it grabs the RMQ messages first with the OLD compiled code. |
| All cache hits — site might be dead | `Response found in S3` count vs total fetches in Graylog | Ignore unless investigating site reachability specifically |
| 1-page brand (no pagination) | < 2 distinct VehicleListUrl in ES | Skipped by default; with `--paginate` flag, rotate once then ⚠️ |
| parseDealer selector targets React-rendered content | dealers = 0 even with overridden parseDealer | Inspect 1 cached HTML for `class="skeleton"` near dealer block — if present, dealer parsing is broken at site-architecture level (real bug, not flaky test) |
| `fetchAndProcessVehicle is not a function` at startup | RMQ_SINGLE_CONSUMER errors before trigger | Stale RMQ messages from prior API-crawler run. Ignore unless they recur after `Prepared listingUrl messages` |
| VPN-only proxy site | Phase 1 nc check fails | Ask user to connect VPN |
| `Authorization: asdf` returns 401 | http-client.env.json placeholder ≠ real `.env` | Always read API_TOKEN from `.env` (typically `abcd`) |
| LocalStack S3 delete throws on `delete-daily-cache` | "Exception on deleteObjects while clearing S3 bucket" | We default to write-disabled; cache delete is no longer the default path |
| Worker crashed mid-run | `lsof -i :3000` empty at end | Restart server, mark report ❌ |
| Queue backlog blocks test: site queue has thousands of messages from production scheduler | `MS_[SITE]_LISTING_URLS_TO_FETCH` count >> 0 before trigger | Purge via `curl -X DELETE "$RMQ_API_URL/queues/MS/[QUEUE_NAME]/contents"`, then immediately trigger and poll ES |
| Pre-existing detail queue backlog (POLAND, etc.) looks alarming but doesn't block test | POLAND queue shows 9000+ messages; test completes anyway | Don't purge — pre-existing detail messages are mostly cache hits (fast), and your 1 listing message still gets published and processed. Only listing URL queues (`MS_[SITE]_LISTING_URLS_TO_FETCH`) block the trigger step. |
| `dealerId` absent from ES even though `parseDealer` is overridden | `marketstudy_search_rollover` never has `dealerId` — `vehicleToEsVehicle` doesn't map it | Verify dealer extraction via `market-study-raw-dealers` index with `site.keyword: "[slug]"` + `createdAt` range — presence of entries = `parseDealer` working |
| Brand name mismatch: Strategy A filter returns 0, `getBrandsAndModels` publishes 0 messages | `"Prepared listingUrl messages 0"` in Graylog despite VPN/proxy OK | Query ES for actual stored names: `"aggs":{"brands":{"terms":{"field":"Brand","size":20}}}` on `Site:[slug]`. Use `includes()` not `===` in the filter. |
| Browser-based detail crawler: ES rows arrive 10+ min after trigger | Listing queue message stays unacked for minutes; browser fetches ~2s each | Don't use fixed 90s poll. Use `until [ $(curl -s "$RMQ/queues/MS/MS_BULK_SAVE_VEHICLES" \| jq .messages) -eq 0 ]; do sleep 3; done` to catch exact flush point. |
| nth-day site: `getBrandsAndModels` returns 0 because today's date doesn't match `matchingDay` | `"Prepared listingUrl messages 0"`; no VPN/proxy error | Temporarily set `matchingDay` in `CrawlingSites.ts` to today's value: `(days since 2024-01-01) % runOnNthDays`. Revert in Phase 7 and add to `changes-applied.json`. |
| LocalStack SVL always fails on first local crawl | All `IsListingValidatedVehicle: false`; error log "Cannot read properties of undefined (reading '#text')" | Expected — LocalStack returns malformed XML on NoSuchKey; `rawRead()` returns `undefined`; SVL re-routes all vehicles. Not a bug. |
| aliases.json slug ≠ `AdSiteKeysEnum` for API trigger | Trigger 200 but `"Prepared listingUrl messages 0"` | POST body needs the enum string value, not the slug. Get it from `grep -r "CrawlerAlias" src/crawler/sites/[Site]/[Site].service.ts` → find matching enum in `src/shared/const/SiteKeys.ts`. |
| Proxy-dependent site: `useProxy: true` + local proxies down → "Listing url is empty" (false negative) | getBrandsAndModels prepares 1 message, listing is fetched, but 0 vehicles in ES; no error logged | Check `nc -z -w 2 localhost 8010` — if proxy down, this is not a code bug. Confirm by curling the listing/AJAX endpoint directly without proxy. activ-automobiles pattern: proxy down → no cookie → AJAX returns empty. |
| Redis devenv down causes cookie-based sites to fail locally | "Listing url is empty" even though site is reachable directly; `redis-cli -h redis.devenv ping` fails | Cookie stored in Redis (e.g. `CacheKeysEnum.ACTIV_AUTOMOBILES`) can't be written or read → AJAX calls sent without auth → empty response. Start Redis devenv or accept this as a false negative for that site. |
| Strategy B test mod placed at BOTTOM of function: loop still runs, wastes minutes | `getBrandsAndModels` takes 4+ minutes, "Problem preparing listingUrl messages", "Exception in iterateThroughVehicleListPages" | Always insert Strategy B `return [{ ... }]` as the **first line of the function body**, before any `fetchRequest` calls. Return at the bottom still executes the full loop first. |
| `tsc-watch` file change restarts server mid-crawl (e.g. `.env` edit) | Browser crawl silently killed; "Return message to rmq due to exception"; 0 vehicles in ES despite pipeline starting | Apply ALL test mods (service file + `.env`) BEFORE starting the server for that test run — never edit files after the server is up and a crawl is in flight. |
| Single-entry aggregator (`getBrandsAndModels` returns 1 entry) collects ALL pages before ES rows appear | 0 in ES after 90s poll despite S3 cache hits; `iterateThroughVehicleListPages` runs to completion first | Use S3 cache hit count as pagination proxy: N hits in <2s = N pages iterated ✅. Extend poll to 5+ minutes OR watch for bulk_save_q > 0 instead of ES count. |

---

## Reference files

| File | Purpose |
|---|---|
| `src/shared/const/CrawlingSites.ts` | Site key, queue, `shouldValidateListingVehicle`, `isDisabled` |
| `src/crawler/sites/[Site]/[Site].service.ts` | The crawler under test |
| `src/bulk-save-worker/bulk-save-worker.service.ts:189` | "Finished saving data vehicles..." (used only as Phase 5 secondary signal) |
| `~/Projects/market-study-knowledge/sites/[slug].md` | Per-site `## Test brand+model` and history |
| `~/Projects/market-study-knowledge/aliases.json` | site name → canonical slug |
| `~/Projects/market-study-knowledge/graylog-queries.md` | Auth + facility names + sync-API payload |
| [Useful ES queries (Confluence)](https://preskok.atlassian.net/wiki/spaces/M/pages/2677997569/Useful+ElasticSearch+queries) | Query patterns not already in this skill — also `src/database/elastic-search/elastic-search.service.ts` or ask user for Kibana saved-queries export |
| `~/.claude/skills/crawler-test-flow/changes-applied.json` | Per-run record of temp mods |

---

## Tone

Methodical, not chatty. Default narrowing without asking. Evidence-first reports. ES-first verification — Graylog is secondary. Cleanup is non-negotiable.

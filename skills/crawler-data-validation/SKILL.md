---
name: crawler-data-validation
description: ALWAYS invoke this skill when the user's message starts with "crawler-data-validation" followed by a site name — e.g. "crawler-data-validation autoscout-nl", "crawler-data-validation mobile-de stage", "crawler-data-validation otomoto prod --sample=10". Validates crawled vehicle ad data quality in Elasticsearch by systematically running through a standardised checklist (URLs, enums, numeric fields, flag consistency, price handling). Use for data quality reviews, post-crawler audits, or diagnosing field-level issues in any Market Study crawler site. Also triggers on "/crawler-data-validation". Sub-commands: "dealers" for dealer data, "workingurl" for workingUrl field validation.
---

# crawler-data-validation

Validate crawled data for a given site against a standard checklist. Fetches live sample docs from ES, runs every check, and produces a structured pass/fail report.

## Usage

```
crawler-data-validation <site> [env] [--sample=N]          # vehicle ad checks
crawler-data-validation dealers <site> [env]               # dealer data checks
crawler-data-validation workingurl <site> [env]            # workingUrl checks
```

- `<site>` — site key from `CrawlingSites.ts` (e.g. `autoscout-nl`, `mobile-de`, `otomoto`). Resolver aliases from `crawler-info` skill apply.
- `[env]` — `local` | `stage` | `prod` (default: `stage`)
- `[--sample=N]` — number of ads to sample (default: 5, max: 20)

---

## Vehicle ad validation

### Step 0 — Resolve site slug & read per-site history

Resolve the canonical slug via `~/Projects/market-study-knowledge/aliases.json`, then read `~/Projects/market-study-knowledge/sites/<slug>.md`. This surfaces known quirks (e.g. `skipDetailsUrlValidation`, multi-country setup, known field gaps) that affect what counts as PASS vs FAIL in the checks below. Do this before querying ES.

**Need a query not listed in this skill?** Check [Useful ElasticSearch queries](https://preskok.atlassian.net/wiki/spaces/M/pages/2677997569/Useful+ElasticSearch+queries) on Confluence, look at `src/database/elastic-search/elastic-search.service.ts` for existing patterns, or ask the user for their Kibana saved-queries export.

### Index architecture cheat sheet (read before querying)

| Alias | Casing | What's in it | Has `workingUrl` field? |
|-------|--------|--------------|--------------------------|
| `marketstudy_search_rollover` (old search / "Old vehicle index" in Kibana) | **Capitalised** (`Site`, `URL`, `Description`, `Price`, `Brand`, `Model`, `CreatedAt`…) | Currently-active vehicles only. `URL` is the **legacy URL** as crawled, never swapped to workingUrl. | No |
| `market-study-vehicle-data_rollover` (data index, history) | **lowercase** (`site`, `url`, `price`, `brand`, `model`, `createdAt`…) | Full lifecycle incl. deactivated; ~30× larger than old search. `url` = `workingUrl ?? legacyUrl` (i.e. working URL when one is set). | No — `workingUrl` is not a persisted ES field. Only on AdVehicle + S3 vehicle JSON. |

**`workingUrl` is NOT in ES as its own field** ([search-vehicle.service.ts:256](src/vehicle/search-vehicle.service.ts) swaps it into `url` at write time). Don't flag `workingUrl: null` in data index `_source` — that field is never expected to be there.

**For the same vehicle: old-index `URL` ≠ data-index `url`** when the site has a working-URL fix in place. Old index keeps the legacy form (for storeId stability); data index has the new working form. **This is by design — never flag it as a workingUrl-migration bug.** To compare URLs for the same vehicle, match by `VehicleId` substring or by `storeId = md5(legacyUrl)`.

### Validation gate behaviour (important when investigating "why is bad data in ES?")

The Graylog log `"Skip saving data vehicle to ES due to failed validation"` (context `VALIDATION`) **only blocks writes to the data index**. The **old search index (`marketstudy_search_rollover`) write path is separate and does NOT respect the same validation gate** — so docs that failed validation can still appear there. This is the current architectural behaviour, not a bug. When a Graylog count for G2 matches the count of bad docs in `marketstudy_search_rollover`, that's the expected pattern: data index correctly rejected them, old search index accepted them anyway.

### Fetching the stored vehicle JSON from S3 (when ES isn't enough)

Several fields are **NOT in ES** and live only in the per-vehicle S3 JSON. When a check needs them, invoke `ams-s3 <storeId>` (see the `ams-s3` skill). Typical reasons to drop into S3:

| Want to verify | Why ES isn't enough |
|---|---|
| `workingUrl` (literal field, not the swapped one) | `workingUrl` is not a persisted ES field — only in S3 vehicle JSON + in-memory AdVehicle |
| `description` matches source | If old-index `Description` is empty for the sampled docs, the S3 JSON may contain the full description that was scraped before truncation/null-out |
| Change history / progressive validation diffs | Stored as part of the S3 vehicle JSON; data index aggregates but doesn't expose every prior value |
| Raw scraped fields the mapper might be dropping (rawHorsePower, rawVersion, rawBodyType, rawIsUsed) | ES only stores the normalised value — S3 has the raw and lets you confirm what the parser actually extracted |
| `equipment` full list incl. tabs/keys | ES may flatten this; S3 has the structured form |
| Confirm whether validation skip applied | If a doc is in old search but not data index, fetching the S3 JSON tells you what got computed; missing/empty S3 JSON tells you the upstream pipeline rejected it |

**How to fetch — easiest first:**
- **Just pass the URL to `ams-s3`** — the skill resolves the storeId itself: `ams-s3 <URL>` or `ams-s3 prod <URL>`. No manual md5 needed.
- If you already have a storeId (e.g. the `_id` from the data index — that's the storeId verbatim): `ams-s3 <storeId>`
- For dealers: `ams-s3 <storeId> --dealer`
- Only compute `md5(legacyURL)` manually as a last resort if `ams-s3` is unavailable.

**Use sparingly** — every S3 fetch is a network call. Reach for it only when an ES check is ambiguous or reports an issue that the raw vehicle JSON would resolve (e.g. "is this an empty Description because the source had nothing, or because the parser dropped it?"). For most checks, ES is sufficient.

### Step 1 — Load config & resolve env

Resolve ES URL in this priority order:

1. `~/.claude/skills/crawler-data-validation/config.json` → `envs[ENV].url`
2. Active (uncommented) `ELASTIC_SEARCH_URL` line in `/Users/filipozbolt/Projects/market-study/.env` — use for `local`
3. Commented `ELASTIC_SEARCH_URL` lines in `.env` — match by pattern (`devenv` = local, `stage`/`beta`/`kibanastage` = stage, `cloud.es.io`/`prod` = prod)

```bash
ENV_FILE="/Users/filipozbolt/Projects/market-study/.env"
# active line = local devenv
LOCAL_ES=$(grep -E "^ELASTIC_SEARCH_URL=" "$ENV_FILE" | cut -d= -f2-)
# 1st commented line = stage (kibanastage / kibana proxy)
STAGE_ES=$(grep -E "^#ELASTIC_SEARCH_URL=" "$ENV_FILE" | head -1 | sed 's/^#ELASTIC_SEARCH_URL=//')
# 2nd commented line = prod (cloud.es.io)
PROD_ES=$(grep -E "^#ELASTIC_SEARCH_URL=" "$ENV_FILE" | sed -n '2p' | sed 's/^#ELASTIC_SEARCH_URL=//')
```

Primary index: read `ELASTIC_SEARCH_INDEX` from `.env` (default: `marketstudy_search_rollover`).

**⚠️ Stage ES note:** The stage URL in `.env` (`kibanastage8.b2b-carmarket.com`) is a Kibana proxy and does NOT serve ES queries directly — it returns nginx headers. The actual stage ES is on an internal hostname only reachable from within the stage network. If queries return non-JSON, ask the user for the correct internal stage ES hostname.

Also check `src/shared/const/CrawlingSites.ts` for the site entry — note whether `shouldValidateListingVehicle` is `true` for this site.

### Step 2 — Fetch sample ads

**⚠️ Sample randomly from TODAY — not the newest N.** Sorting by `CreatedAt desc` returns clustered docs (same brand/model crawled in the same minute) and skews every check. Use a random function_score over today's window so brands/models vary.

```bash
curl -s "<ES_URL>/marketstudy_search_rollover/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "size": <N>,
    "query": {
      "function_score": {
        "query": {"bool": {"must": [
          {"term": {"Site": "<SITE_KEY>"}},
          {"range": {"CreatedAt": {"gte": "now/d"}}}
        ]}},
        "random_score": {"seed": 42, "field": "_seq_no"}
      }
    },
    "_source": [
      "URL", "WorkingUrl", "VehicleListUrl", "CoverImageUrl", "Description",
      "Engine", "EngineCapacity", "HorsePower",
      "Transmission", "DriveTrain", "FuelType",
      "Mileage", "IsUsed", "DateOfFirstRegistration",
      "Country", "Equipment", "Price", "NettoPrice", "OriginalPriceBrutto", "OriginalPriceNetto", "Percent",
      "IsCommercial", "BodyType", "Stock", "ToOrder",
      "Vin", "EmissionsCO2",
      "Brand", "Model", "Name", "NameNormalized",
      "NumberDoors", "NumberSeats",
      "BatteryCapacity", "BatteryRange",
      "IsListingValidatedVehicle", "CreatedAt"
    ]
  }' | jq '.hits.hits[]._source'
```

If zero hits: verify the site key against `src/shared/const/CrawlingSites.ts` and retry. If still zero, stop and report.

Store the parsed docs for use in all checks below.

---

### Step 3 — Run the checklist

For each check, state:
- ✅ **PASS** — all sampled ads satisfy the condition
- ❌ **FAIL** — one or more ads violate the condition (show offending values)
- ⚠️ **WARN** — anomaly worth investigating but not a definite bug
- N/A — field not applicable for this site (explain why)

Every check must appear in the final report, even if N/A.

---

#### URL & link checks

**[1] `url` — takes you to the actual ad**
Curl-check 2–3 sampled `URL` values — no browser needed:
```bash
curl -sI -L --max-redirs 5 -A "Mozilla/5.0" "<URL>" | grep -E "^HTTP|^Location"
```
- `HTTP/... 200` → ✅ resolves to a real page
- `301`/`302` chain ending in `200` → note the final destination; ⚠️ if redirected away from the ad (e.g. to homepage)
- `403`/`429` → site is blocking curl; note as ⚠️ WARN (not a data bug — try with `-H "Accept-Language: en"` or accept as unverifiable)
- `404`/`410` → ad is gone; check if this is a stale doc that should have been deactivated → ⚠️ WARN or ❌ FAIL depending on count

**[2] `url` — no session IDs or unrelated parameters**
Inspect each `URL` string. Reject any that contain parameters not directly identifying the vehicle (e.g. `sessionid=`, `sid=`, `tracking_id=`, `utm_`, `ref=`, `fbclid=`). Path-based IDs and make/model slugs are fine.

**[3] `vehicleListUrl` — takes you to the correct brand/model listing**
Open 2–3 sampled `VehicleListUrl` values in the browser. Confirm each resolves to a listing filtered by the ad's `Brand`/`Model`.

**[4] `coverImageUrl` — resolves to an actual image**
Curl-check 2–3 sampled `CoverImageUrl` values:
```bash
curl -sI "<URL>" | grep -E "HTTP|content-type"
```
Expect HTTP 200 + `Content-Type: image/*`.

---

#### Vehicle identity & basics

**[5] `brand` / `model` — not null or empty**
Scan all sampled docs. Any null, empty string, or literal `"null"` is ❌ FAIL.

**[6] `name` / `nameNormalized` — matches the title on the source ad**
**The crawler stores `Name` raw, as-is, from the source listing.** Do NOT flag long names, equipment dumps, pipes, slashes, emojis, or special characters as bugs — that's how the source displays them. Only check:
- Empty or null values → ❌ FAIL
- `Name` doesn't match the title shown on the live ad page → ❌ FAIL (curl the URL and grep for the title)
- Names that don't include the brand → ⚠️ WARN (possible parse issue, but some sites legitimately exclude brand)

**[7] `Description` — matches the description on the ad**
`Description` IS stored in `marketstudy_search_rollover` (the "Old vehicle index" in Kibana) — field is **capitalised `Description` alongside `Site`**. Coverage is partial and site-dependent (e.g. Eurostocks: ~80% of docs populated, the rest empty because dealers didn't fill the description on the source site).

**Always check aggregation coverage first, not a small sample.** A 5-doc sample sorted by `CreatedAt desc` can easily land on the 20% with no description and produce a false negative. Use:
```bash
curl -s "<ES_URL>/marketstudy_search_rollover/_search?track_total_hits=true" \
  -H 'Content-Type: application/json' \
  -d '{
    "size": 0,
    "query": {"term": {"Site": "<SITE_KEY>"}},
    "aggs": {
      "has_desc": {"filter": {"exists": {"field": "Description"}}},
      "with_content": {"filter": {"bool": {"must": [{"exists": {"field": "Description"}}], "must_not": [{"term": {"Description.keyword": ""}}]}}}
    }
  }' | jq '{total: .hits.total.value, has_desc: .aggregations.has_desc.doc_count, with_content: .aggregations.with_content.doc_count}'
```
- `with_content / total > 60%` → ✅ PASS, dealer-fill-rate is the limiter, not the crawler
- `with_content / total < 30%` → ⚠️ WARN, check whether the crawler is reading the wrong source field (e.g. Eurostocks page has both `Description` and `MetaDescription` in its SSR JSON — pick whichever has content)
- `0` → ❌ FAIL, crawler isn't extracting at all

Then fetch 1–2 docs that DO have content and compare to the live ad page.

**[8] `bodyType` — is one of `BodyTypeEnum`**
Valid values: `minivan`, `suv`, `limousine`, `hatchback`, `estate`, `coupe`, `cabrio`, `commercial-vehicle`, `commercial-vehicle-light`, `other`.
Any value outside this set is ❌ FAIL.

---

#### Engine & mechanical

**[9] `engine` — is an actual engine string (or ad title containing engine info)**
Review sampled `Engine` values. Should be a real engine descriptor (e.g. `"2.0 TDI"`, `"1.4 TSI"`). Flag empty strings, placeholders, or completely unrelated text.

**[10] `horsePower` — stored as HP, not kW**
The crawler **always** stores HP (kW is converted via `CrawlerHelper.kwToHp()` in code). Typical cars: 50–1000 HP. Hyper/EV outliers exist legitimately: Tesla Plaid ~1020 HP, Porsche Cayenne Turbo Electric ~1140 HP, Lamborghini Revuelto ~1000 HP, tuner cars (e.g. Porsche 997 9ff) can hit 1000+. **Don't auto-flag values 1000–1500 — verify against the ad first.** Real bugs are extreme outliers (e.g. 87,882 HP on a Ford S-Max — caused by parsing a raw cm³ or other numeric field through the kW→HP multiplier).

If you find outliers (e.g. > 1500 or < 30), **do not assume a parser bug without checking**. Fetch the ES docs with the anomalous values to get their `URL`, then curl the live ad:
```bash
curl -sL -A "Mozilla/5.0" "<URL>" | grep -i -E "pk|kw|horse|vermogen|cv|ps" | head -20
```
- If the site itself shows the same wrong value → source data is corrupt; parser is correct. Report as ⚠️ WARN (not our bug).
- If the site shows a sensible value (e.g. 150 HP) but ES has 138217 → parser is extracting the wrong element. Report as ❌ FAIL.

A parser bug typically affects a large proportion of docs consistently. A handful of outliers in 50k docs strongly suggests source-side bad data, not a systematic parser failure.

**[11] `transmission` — is one of `TransmissionTypeEnum`**
Valid values: `automatic`, `manual`, `semi_auto`, `cvt`, `sequential`.
Any value outside this set is ❌ FAIL.

**[12] `driveTrain` — is one of `DriveTrainEnum`**
Valid values: `RWD`, `FWD`, `AWD`.
Any value outside this set is ❌ FAIL.

**[13] `fuelType` — is one of `FuelTypeEnum`**
Valid values: `diesel`, `electric`, `gasoline`, `hybrid`, `gas`, `ethanol`, `other`.
Any value outside this set is ❌ FAIL.

**[14] `engineCapacity` — stored as litres (e.g. `1.2`), not cm³ (e.g. `1199`)**
Valid range: `0.6`–`9.0`. Values like `1199`, `1984`, `2995` mean cm³ — ❌ FAIL.

For outliers > 9 L: fetch the docs and curl their `URL` to check what the site actually shows. An electric vehicle may legitimately show `0` or no displacement; a handful of odd values (e.g. `10`, `22`) may be source data issues on specific ads rather than a systematic parser unit error. Distinguish: if only a few docs are affected, check those specific ads before calling it a FAIL.

**[15] `emissionsCO2` — crawled correctly**
If present: should be in g/km, typically 0–400. Values clearly in a different unit or > 500 are suspicious.
If `fuelType = electric`: should be `0` or absent.

**[16] `vin` — crawled correctly**
If present: 17 alphanumeric characters, no I/O/Q. Flag wrong-length values or placeholder strings like `"N/A"` stored as VIN. If the site doesn't provide VINs, mark N/A.

---

#### Mileage & usage flags

**[17] `mileage` — crawled correctly**
Review sampled `Mileage` values. Should be in kilometres. Flag values that look like miles (different order of magnitude for the market) or obviously wrong round numbers.

**[18] `mileage = 0` / low mileage + `isUsed` flag**
```bash
curl -s "<ES_URL>/marketstudy_search_rollover/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "size": 10,
    "query": {
      "bool": {
        "must": [{"term": {"Site": "<SITE_KEY>"}}],
        "filter": [{"range": {"Mileage": {"lte": 100}}}]
      }
    },
    "_source": ["URL", "Mileage", "IsUsed", "Brand", "Model"]
  }' | jq '.hits.hits[]._source'
```
- `IsUsed = false` + `Mileage = 0` → ✅ expected (new car)
- `IsUsed = true` + `Mileage = 0` → ⚠️ WARN — investigate

**[19] `isUsed = false` + `mileage > 1000` — flag anomaly**
```bash
curl -s "<ES_URL>/marketstudy_search_rollover/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "size": 5,
    "query": {
      "bool": {
        "must": [
          {"term": {"Site": "<SITE_KEY>"}},
          {"term": {"IsUsed": false}},
          {"range": {"Mileage": {"gt": 1000}}}
        ]
      }
    },
    "_source": ["URL", "Mileage", "IsUsed", "Brand", "Model"]
  }' | jq '.hits.hits[]._source'
```
If hits: open URLs to check if these are demo/pre-reg cars or if `IsUsed` is wrongly `false`.

**[20] `isUsed` — crawled correctly**
Open 2–3 ads where `IsUsed = true` and 2–3 where `IsUsed = false`. Confirm the flag matches the ad's used/new status.

---

#### Date & location

**[21] `dateOfFirstRegistration` — crawled correctly**
Review format and plausibility. Expected: ISO date string (e.g. `"2019-03-01"` or `"2019-03"`). Flag: wrong format, future dates, or pre-1950.

**[22] `isUsed = false` + `dateOfFirstRegistration` present — flag anomaly**
New cars should not have a `DateOfFirstRegistration`:
```bash
curl -s "<ES_URL>/marketstudy_search_rollover/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "size": 5,
    "query": {
      "bool": {
        "must": [
          {"term": {"Site": "<SITE_KEY>"}},
          {"term": {"IsUsed": false}},
          {"exists": {"field": "DateOfFirstRegistration"}}
        ]
      }
    },
    "_source": ["URL", "IsUsed", "DateOfFirstRegistration", "Brand", "Model"]
  }' | jq '.hits.hits[]._source'
```
If hits: ⚠️ WARN — open URLs and investigate.

**[23] `country` — crawled correctly (for multi-country sites)**
If this site crawls multiple countries, check `Country` varies across the sample. For single-country sites, verify it matches the expected country.

---

#### Pricing & discount

**[24] `price` — crawled correctly, decimals handled**
Check sampled `Price` values. Prices should be whole numbers or clean 2-decimal values. Flag floating-point noise (e.g. `24989.999`). Decimals must be handled in the crawler.

**[25] `price = 0` — investigate**
```bash
curl -s "<ES_URL>/marketstudy_search_rollover/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "size": 5,
    "query": {
      "bool": {
        "must": [
          {"term": {"Site": "<SITE_KEY>"}},
          {"term": {"Price": 0}}
        ]
      }
    },
    "_source": ["URL", "Price", "Brand", "Model", "IsUsed"]
  }' | jq '.hits.hits[]._source'
```
If hits: open URLs — is `Price = 0` intentional (POA / price-on-request) or a crawling bug?

**[26] `nettoPrice` ≤ `price` when both present**
Netto price must not exceed brutto. Scan sampled docs for any where `NettoPrice > Price`. If found: ❌ FAIL.

**[27] `discount` / `percent` — crawled correctly**
Check sampled `Percent` values. Should be a numeric percentage (e.g. `10`, `15.5`). Flag: values > 100 or < -100.
Also: if `Percent > 0` but `OriginalPriceBrutto` is absent, that's ⚠️ WARN — discount without an original price to reference.

**[28] `equipment` — crawled correctly**
Review sampled `Equipment` objects. If equipment items include prices, check for floating-point noise (e.g. `1299.9999` instead of `1300`).

---

#### Commercial & body type flags

**⚠️ Constants vs crawled fields — always check the code first.**
For `IsCommercial`, `Stock` (isOnStock), and `ToOrder` (isToOrder): if an aggregation shows the field is 100% constant (e.g. all `true` or all `false`), grep the site's service file:
```bash
grep -nE "isOnStock|isToOrder|isCommercial" src/crawler/sites/<SiteName>/<SiteName>.service.ts
```
- If hardcoded (e.g. `isOnStock: true, isToOrder: false`) → ✅ **EXPECTED**, not a warning. Note in report as "intentionally constant per code".
- If field is set from parsed data but still shows as constant in ES → ⚠️ WARN, possible parser silently returning the same value.

**[29] `isCommercial` — crawled correctly**
Open 2–3 ads where `IsCommercial = true` (commercial vehicles) and 2–3 where `false` (passenger cars). Confirm visually.

**[30] `bodyType` commercial variants → `isCommercial = true`**
Any ad with `BodyType` of `commercial-vehicle` or `commercial-vehicle-light` must have `IsCommercial = true`:
```bash
curl -s "<ES_URL>/marketstudy_search_rollover/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "size": 10,
    "query": {
      "bool": {
        "must": [
          {"term": {"Site": "<SITE_KEY>"}},
          {"terms": {"BodyType": ["commercial-vehicle", "commercial-vehicle-light"]}}
        ]
      }
    },
    "_source": ["URL", "BodyType", "IsCommercial"]
  }' | jq '.hits.hits[]._source'
```
Any hit where `IsCommercial` is `false` or absent → ❌ FAIL.

---

#### Stock flags

**[31] `isOnStock` (`Stock`) — crawled correctly**
Open 2–3 ads where `Stock = true` and confirm the source page indicates the vehicle is in stock.

**[32] `isToOrder` (`ToOrder`) — crawled correctly**
Open 2–3 ads where `ToOrder = true` and confirm the source page indicates to-order / not yet in stock.

**[33] `isOnStock` XOR `isToOrder` — they must differ**
`Stock` and `ToOrder` should never both be `true` or both `false`:
```bash
# Both true
curl -s "<ES_URL>/marketstudy_search_rollover/_search" \
  -H 'Content-Type: application/json' \
  -d '{"size":5,"query":{"bool":{"must":[{"term":{"Site":"<SITE_KEY>"}},{"term":{"Stock":true}},{"term":{"ToOrder":true}}]}},"_source":["URL","Stock","ToOrder"]}' \
  | jq '.hits.hits[]._source'

# Both false
curl -s "<ES_URL>/marketstudy_search_rollover/_search" \
  -H 'Content-Type: application/json' \
  -d '{"size":5,"query":{"bool":{"must":[{"term":{"Site":"<SITE_KEY>"}},{"term":{"Stock":false}},{"term":{"ToOrder":false}}]}},"_source":["URL","Stock","ToOrder"]}' \
  | jq '.hits.hits[]._source'
```
Any hits in either query → ❌ FAIL. Open the URLs and investigate.

---

#### Physical dimensions

**[34] `numberDoors` — plausible value**
Valid range: 2–5. Values of 0, 1, or > 5 are bugs. For any outliers found, fetch the docs and curl their `URL` to see what the site displays. Values like 15, 25, 255 are classic byte/int overflow or string-parse bugs in the crawler — but verify a sample before concluding that, as the source site might also display garbage data on certain listings.

**[35] `numberSeats` — plausible value**
Valid range: 1–9. Values outside this range are suspicious. Same as [34]: for any outliers, curl 2–3 live ad URLs to determine whether the bad value originates on the site or in the parser before classifying as FAIL.

---

#### Electric vehicle specific

**[36] EV fields present when `fuelType = electric`**
For any ad where `FuelType = electric`:
- `BatteryCapacity` should be present and plausible (10–200 kWh)
- `BatteryRange` should be present and plausible (50–1000 km)
- `EmissionsCO2` should be `0` or absent

If `BatteryCapacity` / `BatteryRange` are absent on electric vehicles → ⚠️ WARN.

**[37] Non-EV ads have no EV fields**
For ads where `FuelType ≠ electric`: `BatteryCapacity` and `BatteryRange` should be absent or null.

---

#### Freshness & validation status

**[38] `createdAt` — data is recent**
Check `CreatedAt` of sampled ads. If all docs are more than 2 weeks old, the crawler may have stalled. Flag for investigation.

**[39] `isListingValidatedVehicle` — if `shouldValidateListingVehicle = true` for this site**
First check `CrawlingSites.ts` — if `shouldValidateListingVehicle: true` is not set, mark this check N/A.

**Only check docs from the most recent crawl run** — old docs predate the feature and will naturally have `false`. A fixed time window is wrong because multiple runs may fall within it. Instead, find the exact start time of the last run from Graylog first:

```bash
# Step 1 — find when the last crawl started for this site (look back up to 7 days)
curl -s -X POST -u "$TOKEN:token" \
  -H "Content-Type: application/json" -H "X-Requested-By: curl" \
  "$GURL/api/views/search/sync?timeout=30000" \
  -d '{
    "queries": [{
      "id": "q1",
      "timerange": {"type": "relative", "range": 604800},
      "query": {"type": "elasticsearch", "query_string": "facility:marketstudy* AND site:<SITE_KEY> AND message:\"Started crawling listing url\""},
      "search_types": [{"id": "st1", "type": "messages", "limit": 1, "offset": 0, "sort": [{"field": "timestamp", "order": "DESC"}]}]
    }]
  }' | jq '.results.q1.search_types.st1.messages[0].message.timestamp'
```

This gives you the timestamp of the most recent listing crawl start (e.g. `"2026-05-07T10:30:00.000Z"`). Use that as the `CreatedAt` lower bound in ES:

```bash
# Step 2 — check IsListingValidatedVehicle only for docs from that run onward
LAST_RUN="<timestamp from step 1>"

curl -s "<ES_URL>/marketstudy_search_rollover/_search" \
  -H 'Content-Type: application/json' \
  -d "{
    \"size\": 0,
    \"query\": {
      \"bool\": {
        \"must\": [{\"term\": {\"Site\": \"<SITE_KEY>\"}}],
        \"filter\": [{\"range\": {\"CreatedAt\": {\"gte\": \"$LAST_RUN\"}}}]
      }
    },
    \"aggs\": {
      \"validated_true\":  {\"filter\": {\"term\": {\"IsListingValidatedVehicle\": true}}},
      \"validated_false\": {\"filter\": {\"term\": {\"IsListingValidatedVehicle\": false}}},
      \"field_missing\":   {\"missing\": {\"field\": \"IsListingValidatedVehicle\"}}
    }
  }" | jq '{run_since: "<LAST_RUN>", total: .hits.total.value, true: .aggregations.validated_true.doc_count, false: .aggregations.validated_false.doc_count, missing: .aggregations.field_missing.doc_count}'
```

- All docs from this run `true` → ✅
- Any `false` or missing → ❌ FAIL — listing validation not running or flag not being persisted
- `total = 0` → no docs created since last crawl start — cross-check with check [38] freshness

**⚠️ First-run nuance.** SVL needs a previous version of the vehicle to compare against, and to legitimately mark `IsListingValidatedVehicle = true` (meaning "we trusted the listing and skipped re-visiting details"). On the very first crawl after enabling `shouldValidateListingVehicle`, every vehicle is necessarily new → no previous version → details are re-visited → flag may stay `false`. So `0 true / N false` is acceptable on the first run.

**However:** if the site has months-old data and a fresh crawl has run since the feature was enabled but flag is **still 0% true across all docs**, that's a real bug. Cross-check with [workingUrl validation](#workingurl-validation) — both features tend to land together, so if neither has propagated, the new code likely isn't reaching prod or the persistence path is broken. Verify deploy state before concluding.

---

### Step 3b — Always run Graylog validation alongside vehicle checks

After finishing the vehicle ad checklist, **automatically run the Graylog validation section** (see "Graylog validation" below) for the same site. **Use the last crawl start timestamp as the time window**, not a fixed 24h range — find it first via the `"Started crawling listing url"` Graylog query (see "Site-specific check overrides" at the bottom of this skill), then pass it as an absolute `from` to all G-checks. Using 24h includes noise from previous sessions and prior code versions. This catches issues that don't surface in ES: pagination crashes, DLQ floods, SVL listing-validation failures (level 6 logs `"Details URL validation failed"`), and HTTP error codes. Merge both reports into the final summary so the user sees data quality AND runtime health in one verdict.

If Graylog isn't reachable from the current environment (e.g. local-only `graylog.devenv` URL while validating prod), explicitly say so in the report rather than silently skipping.

### Step 4 — Report

Output a structured summary — every check listed, even if N/A:

```
## Crawler Data Validation — <SITE_KEY> (<ENV>) — <DATE>
Sample: <N> ads

| #  | Check                                                   | Result | Notes |
|----|---------------------------------------------------------|--------|-------|
|  1 | url → resolves to actual ad                             | ✅     |       |
|  2 | url → no session/tracking params                        | ✅     |       |
...
| 39 | isListingValidatedVehicle (if applicable)               | N/A    | shouldValidateListingVehicle not set for this site |

### Failures & warnings
<For each ❌ or ⚠️: what was found, example URLs/values, and where to look in the crawler.>

### Overall verdict
<PASS / FAIL — N checks failed, M warnings>
```

Link failing checks to `src/crawler/sites/<SiteName>/<SiteName>.service.ts`.

---

## Dealer data validation

Usage: `crawler-data-validation dealers <site> [env]`

Index: `market-study-raw-dealers`

### Fetch sample dealers

```bash
curl -s "<ES_URL>/market-study-raw-dealers/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "size": 10,
    "query": {"term": {"site": "<SITE_KEY>"}},
    "_source": ["name","siteUrl","website","location","contacts","logoUrl","isDealer","foundOn","branchName","dealerFrom"]
  }' | jq '.hits.hits[]._source'
```

### Dealer checklist

| # | Check | How |
|---|-------|-----|
| 1 | `name` — not null or empty | scan docs |
| 2 | `siteUrl` — resolves to dealer page on source site | open in browser |
| 3 | `siteUrl` — no session/tracking params | inspect URL string |
| 4 | `website` — if present, resolves (HTTP 200, not 404) | `curl -sI` |
| 5 | `location.address` — not empty, contains street + city | review values |
| 6 | `location.country` — matches expected country for this site | review values |
| 7 | `contacts[].email` — valid email format if present | regex check `/.+@.+\..+/` |
| 8 | `contacts[].phone` — plausible phone format for the country | review values |
| 9 | `logoUrl` — if present, resolves to an image (`Content-Type: image/*`) | `curl -sI` |
| 10 | `isDealer` — spot-check `true` and `false` cases against source | browser |
| 11 | `dealerId` stability — same dealer name + site + website always produces the same `_id` | query same dealer twice, compare |
| 12 | No duplicate dealers — no two docs with same `name` + `site` producing different `_id` | ES terms agg on `name` + `site` |
| 13 | `foundOn` — date is plausible (not future, not pre-2015) | review values |
| 14 | `branchName` — if present, not empty and not identical to `name` | review values |
| 15 | Active dealers have vehicles — cross-check `market-study-dealers` index for vehicle count > 0 | `getAllVehiclesFromDealer()` query |

---

## Graylog validation

Usage: `crawler-data-validation graylog <site> [env] [--hours=N]`

Default window: last 24h (`--hours=24`). Adjust with e.g. `--hours=72` for a 3-day view.

### Step 0 — Load credentials

`.env` typically has the local URL active and **prod/stage URLs commented out**. Resolve in the same priority order as ES (active line = local, commented lines = stage/prod by pattern). Common values:
- Local: `http://graylog.devenv:8090` (not reachable for prod log validation)
- Stage: `https://graylog3beta.b2b-carmarket.com`
- Prod: `https://graylog3.b2b-carmarket.com`

```bash
ENV_FILE="/Users/filipozbolt/Projects/market-study/.env"
# Match by pattern in commented lines:
STAGE_GURL=$(grep -E "^#+GRAYLOG_API_URL=.*(beta|stage)" "$ENV_FILE" | head -1 | sed 's/^#*GRAYLOG_API_URL=//')
PROD_GURL=$(grep -E "^#+GRAYLOG_API_URL=https://graylog3\." "$ENV_FILE" | grep -v beta | head -1 | sed 's/^#*GRAYLOG_API_URL=//')
STAGE_TOKEN=$(grep -E "^#+GRAYLOG_AUTH_TOKEN=" "$ENV_FILE" | sed -n '1p' | sed 's/^#*GRAYLOG_AUTH_TOKEN=//')
PROD_TOKEN=$(grep -E "^#+GRAYLOG_AUTH_TOKEN=" "$ENV_FILE" | sed -n '2p' | sed 's/^#*GRAYLOG_AUTH_TOKEN=//')
```

**⚠️ Auth quirk:** Graylog tokens contain characters that confuse `curl -u "$TOKEN:token"` (it interprets them as a password prompt). Use an explicit Basic Auth header instead:
```bash
AUTH=$(printf "%s:token" "$TOKEN" | base64)
curl -H "Authorization: Basic $AUTH" -H "X-Requested-By: curl" ...
```

Defaults:
```bash
SITE=<site-key>
HOURS=24
RANGE=$((HOURS * 3600))
```

### Step 1 — Run all queries

Run every query below. Use this base pattern for each — substitute `QUERY_STRING` and adjust `limit` when you want sample messages:

```bash
curl -s -X POST -u "$TOKEN:token" \
  -H "Content-Type: application/json" -H "X-Requested-By: curl" \
  "$GURL/api/views/search/sync?timeout=30000" \
  -d "{
    \"queries\": [{
      \"id\": \"q1\",
      \"timerange\": {\"type\": \"relative\", \"range\": $RANGE},
      \"query\": {\"type\": \"elasticsearch\", \"query_string\": \"QUERY_STRING\"},
      \"search_types\": [{\"id\": \"st1\", \"type\": \"messages\", \"limit\": 5, \"offset\": 0}]
    }]
  }" | jq '{count: .results.q1.search_types.st1.total_results, samples: [.results.q1.search_types.st1.messages[].message | {message, url, site, errorCode}]}'
```

#### G0 — Level 3 errors (application errors, excluding HTTP noise)

⚠️ **Run this first and treat any hits as high priority.**

```
facility:marketstudy* AND level:3 AND site:<SITE> AND NOT context:FETCH_EXTERNAL AND NOT context:RMQ_INFO AND NOT full_message:"Too many retries for message, discarding it"
```

This strips out HTTP-level errors (`FETCH_EXTERNAL` — covered by G6) and DLQ noise (`Too many retries` — covered by G4), leaving only genuine application-level errors: parser crashes, unexpected exceptions, DB/RMQ failures, validation service errors, and anything else that shouldn't be happening.

Increase the `limit` to 20 so you get a meaningful sample of distinct error messages, not just a count:

```bash
# same base curl, but limit:20 and pull the full message field
... | jq '{count: .results.q1.search_types.st1.total_results, samples: [.results.q1.search_types.st1.messages[].message | {level, message, context, url, site, stack}]}'
```

For each unique error message in the sample, group by `message` and `context` to understand the pattern — one recurring error is more serious than the same total count spread across many different messages.

Pass condition: 0 → ✅; 1–10 → ⚠️ WARN (review samples); > 10 → ❌ FAIL (escalate)

---

#### G1 — SVL failures (listing→details field mismatch)
```
facility:marketstudy* AND site:<SITE> AND message:"Details URL validation failed"
```
Captures cases where a field crawled from the listing page (price, mileage, name) doesn't match what's on the details page — triggers a details re-fetch. High counts indicate the listing parser and details parser are diverging on a field.

Sample the messages: inspect which field is mismatching most.

Pass condition: low baseline is OK; a sudden spike → ⚠️ WARN; sustained high count → ❌ FAIL

---

#### G2 — Field validation failures (invalid values blocked from ES)
```
facility:marketstudy* AND site:<SITE> AND message:"Skip saving data vehicle to ES due to failed validation"
```
Captures vehicles where crawled field values failed Zod/range validation and were not saved to ES. Occasional hits = OK (some ads are malformed on the source). Sustained high count means the crawler is consistently producing out-of-range values.

**When you find failures, always open the source ad URL before concluding the parser is broken.** The site itself may contain the bad value — a listing with `horsePower: 138217` might literally display `138217` on the page, meaning the parser is correct and the source data is wrong. Pull the `url` field from the log message and check the live ad:

```bash
# Get sample failure messages including the URL and the offending field
... | jq '[.results.q1.search_types.st1.messages[].message | {message, url, site, field, value}]'
```

Open 2–3 of the failing URLs and verify the displayed value. Then report:
- **Source is wrong** (site displays the bad value) → parser is working correctly; the validation block is doing its job. Note as ⚠️ WARN — data quality issue on the source site, not a crawler bug.
- **Source is correct** (site shows a sensible value, crawler extracted garbage) → parser bug. Note as ❌ FAIL with the field and example URL.

Pass condition: sporadic = OK; > 20 in window → ⚠️ WARN; > 100 → ❌ FAIL

---

#### G3 — Pagination crash
```
facility:marketstudy* AND site:<SITE> AND message:"Exception in iterateThroughVehicleListPages"
```
Any hit means the listing page iterator threw and stopped — some pages were not crawled at all.

Pass condition: 0 hits → ✅; any hits → ❌ FAIL

---

#### G4 — Dead Letter Queue (messages that exhausted all retries)
```
facility:marketstudy* AND site:<SITE> AND message:"Too many retries for message, discarding it"
```
Each hit = one vehicle URL that was attempted multiple times and permanently discarded. Some DLQ entries are expected for genuinely broken URLs; a high count means the site is systematically unreachable or blocking requests.

Pass condition: < 10 in window = OK; > 20 → ⚠️ WARN; > 50 → ❌ FAIL

---

#### G5 — "Vehicle changed too much" (price/field anomalies)
```
facility:marketstudy* AND site:<SITE> AND message:"Vehicle has changed too much"
```
Triggered when a vehicle update exceeds the change threshold — either the source data is genuinely volatile (price fluctuations, re-listings) or the crawler is scraping noise/junk into a field.

Pass condition: occasional = OK; sustained → ⚠️ WARN; investigate which field is changing

---

#### G6 — HTTP error code breakdown

Run one query per code. Collect all counts and display as a table (Step 2).

```bash
# Run for each code — substitute CODE
facility:marketstudy* AND site:<SITE> AND errorCode:CODE
```

Codes to check:

| Code | Meaning | Pass condition |
|------|---------|----------------|
| 301/302 | Redirects — crawler should follow these, logged ones are unexpected | Any → ⚠️ WARN |
| 400 | Bad request — crawler sending malformed requests | Any → ❌ FAIL |
| 401 | Unauthorised — auth broke | Any → ❌ FAIL |
| 403 | Forbidden — site blocking crawler / anti-bot | Baseline OK; rising trend → ⚠️ |
| 404 | Not found — ads deactivated mid-crawl (normal churn) | Expected; high count vs active vehicles → ⚠️ |
| 410 | Gone — permanent deactivation (some sites use this) | Expected; same as 404 |
| 429 | Rate limited — too many requests or proxy quota | Any → ⚠️ WARN; frequent → ❌ FAIL |
| 500 | Server error on source site | Occasional = OK; sustained → ⚠️ site instability |
| 502 | Bad gateway — proxy or source infrastructure issue | Any → ⚠️ WARN |
| 503 | Service unavailable — source site down | Any → ⚠️ WARN |
| 504 | Gateway timeout | Any → ⚠️ WARN |

Run each and note the count. Also run a catch-all for any other non-2xx/3xx codes:
```
facility:marketstudy* AND site:<SITE> AND _exists_:errorCode AND NOT errorCode:200 AND NOT errorCode:301 AND NOT errorCode:302 AND NOT errorCode:304 AND NOT errorCode:403 AND NOT errorCode:404 AND NOT errorCode:410 AND NOT errorCode:429 AND NOT errorCode:500 AND NOT errorCode:502 AND NOT errorCode:503 AND NOT errorCode:504
```
Sample those messages to identify any exotic codes.

---

### Step 2 — Report

```
## Graylog Validation — <SITE_KEY> (<ENV>) — last <N>h — <DATE>

### Checklist

| #  | Check                                        | Count | Result | Notes |
|----|----------------------------------------------|-------|--------|-------|
| G0 | ⚠️ Level 3 errors (app errors, excl. HTTP)  |       | ✅/⚠️/❌ |       |
| G1 | SVL failures (Details URL validation failed) |       | ✅/⚠️/❌ |       |
| G2 | Field validation failures (skip saving)      |       | ✅/⚠️/❌ |       |
| G3 | Pagination crash                             |       | ✅/❌   |       |
| G4 | Dead Letter Queue entries                    |       | ✅/⚠️/❌ |       |
| G5 | Vehicle changed too much                     |       | ✅/⚠️   |       |

### HTTP error code breakdown

| Code | Count | Verdict |
|------|-------|---------|
| 301  |       |         |
| 302  |       |         |
| 400  |       |         |
| 401  |       |         |
| 403  |       |         |
| 404  |       |         |
| 410  |       |         |
| 429  |       |         |
| 500  |       |         |
| 502  |       |         |
| 503  |       |         |
| 504  |       |         |
| other |      |         |

### Sample messages (for any ⚠️ or ❌)
<For each failing check: paste 1–3 sample log messages showing url, message, errorCode.>

### Overall verdict
<PASS / FAIL — N checks failed, M warnings>
```

---

## workingUrl validation

Usage: `crawler-data-validation workingurl <site> [env]`

### How it works (read before running checks)

**Working URL** = the current, browser-accessible details URL. Saved to S3 as `workingUrl`, and saved to ES new search + data index **as `url`** (overwrites the legacy URL field).

**Legacy URL** = the old URL, still used to generate storeId (S3 key + data index ID). Saved to ES old search index as `url`. Never appears as `url` in the new search/data index once the fix is active.

So in ES new search index: the `URL` field **is** the working URL — there is no separate `WorkingUrl` field in ES. The fix is entirely transparent to ES consumers.

**For `shouldValidateListingVehicle = true` / large sites**: rollout is gradual. Working URL is first assigned only in details parsing. Only after enough vehicles are migrated is it also assigned in listing parsing (which triggers a details re-parse for all remaining vehicles). During this window, some vehicles will still carry the legacy URL as `url` in ES.

### Step 0 — Confirm the site uses workingUrl

Check the crawler source: `src/crawler/sites/<SiteName>/<SiteName>.service.ts`
Look for `workingUrl` assignment in `parseVehicleDetails()` or `parseVehicleList()`.

If not present → mark all checks N/A and stop.

### Step 1 — Determine rollout phase

Check whether `workingUrl` is assigned in **listing parsing** as well as details:
- Only in details (`parseVehicleDetails`) → **Phase 1** (gradual rollout, not all vehicles migrated yet)
- Also in listing (`parseVehicleList`) → **Phase 2** (full rollout, all active vehicles should be migrated)

This affects which checks are expected to pass.

### workingUrl checklist

**[1] `url` in ES resolves (HTTP 200)**
The `URL` field in ES should be the working URL and must resolve. `curl -sI` on 3–5 sampled `URL` values from ES. Any 404 is ❌ FAIL.

**[2] `url` in ES — no session/tracking params**
Inspect the `URL` values from ES. Same rule as vehicle check [2] — no `utm_`, `sessionid=`, etc.

**[3] `url` in ES uses the new URL pattern (not the legacy pattern)**
Compare the ES `URL` values against the known legacy URL pattern for this site (e.g. `/angebote/` for AutoScout). If ES URLs still contain the legacy pattern, the fix is not applied yet. In Phase 1 this may be partially true — quantify what % still have the old pattern:
```bash
curl -s "<ES_URL>/marketstudy_search_rollover/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "size": 0,
    "query": {"term": {"Site": "<SITE_KEY>"}},
    "aggs": {
      "legacy_url_count": {
        "filter": {"wildcard": {"URL": "*<LEGACY_PATTERN>*"}}
      }
    }
  }' | jq '.aggregations'
```
Phase 1: some legacy URLs expected ⚠️. Phase 2: any legacy URLs → ❌ FAIL.

**[4] `workingUrl` exists in S3 for sampled vehicles**
Fetch 2–3 vehicle docs from S3 — invoke `ams-s3 <storeId>` (or `ams-s3 <storeId> --dealer` for dealer records) for each. The skill saves the JSON locally and opens it. Confirm `workingUrl` field is present and matches what ES has as `url`.

**[5] Legacy URL correctly generates the same storeId as before**
For a vehicle that has been migrated: confirm its storeId / S3 key is still derived from the legacy URL (not the working URL). This ensures no duplicates were created. Check by comparing the S3 key against the expected legacy URL hash.

**[6] Working URL points to the same vehicle as the legacy URL**
Open a working URL (from ES `url`) in the browser. Then manually reconstruct the legacy URL for the same vehicle. Confirm both show the same vehicle (same make/model/year/price). If the URL transform is lossy (can't reconstruct), just confirm the working URL shows the right vehicle.

**[7] URL transformation is consistent**
Review 5–10 ES `URL` values. All migrated vehicles should show the same structural transformation (e.g. every one replaces `/angebote/` with `/offers/`). A mix of old and new patterns in Phase 2 is ❌ FAIL.

**[8] Phase 2 only — all active vehicles have working URL**
If Phase 2 (listing parsing also assigns `workingUrl`): query for any active vehicles still using the legacy URL pattern. There should be none. Any remaining → ❌ FAIL, trigger re-crawl investigation.

**[9] No regressions after reassignment**
If `workingUrl` was recently changed to a new value (e.g. the working URL itself changed again): confirm ES `url` values reflect the newest working URL pattern, not the previous working URL. Old working URLs that now 404 are ❌ FAIL.

### workingUrl + legacyUrl integrity suite (W1-W5)

When the question is *"are workingUrl and legacyUrl wired up correctly?"* rather than *"is rollout complete?"*, run these layered invariants. Cheap → expensive.

**W1 — storeId invariant (per-vehicle)**
For N random currently-active vehicles, assert `md5(<old-index URL>) == <data-index _id>`. This is the fundamental identity guarantee — if it fails, the same vehicle exists as two unrelated docs and everything else is meaningless.
```bash
LEGACY=$(curl -s "$ES/marketstudy_search_rollover/_search" -H 'Content-Type: application/json' \
  -d "{\"size\":1,\"query\":{\"bool\":{\"must\":[{\"term\":{\"Site\":\"<SITE>\"}},{\"wildcard\":{\"URL\":\"*<VID>*\"}}]}},\"_source\":[\"URL\"]}" | jq -r '.hits.hits[0]._source.URL')
EXPECTED=$(echo -n "$LEGACY" | md5)
ACTUAL=$(curl -s "$ES/market-study-vehicle-data_rollover/_search" -H 'Content-Type: application/json' \
  -d "{\"size\":1,\"query\":{\"bool\":{\"must\":[{\"term\":{\"site\":\"<SITE>\"}},{\"wildcard\":{\"url\":\"*<VID>*\"}}]}}}" | jq -r '.hits.hits[0]._id')
[ "$EXPECTED" = "$ACTUAL" ] && echo "✅" || echo "❌ EXPECTED=$EXPECTED ACTUAL=$ACTUAL"
```

**W2 — Index-level URL pattern split (bulk aggregation)**
For sites with a working-URL fix, the two indices serve different purposes — don't mis-classify the split as a migration bug:

| Index | Subset | Expected URL pattern |
|---|---|---|
| Old search `URL` | All active docs | **100% legacy** by design (used for storeId stability) |
| Data index `url` | **Active subset** | **~100% working** — these get re-crawled, so they pick up the new URL |
| Data index `url` | **Inactive/historical subset** | **mostly legacy** — never re-visited, so their URL stays whatever was written at last crawl. Will decay slowly, not a bug. |

When validating, **always split active vs historical** before measuring "migration coverage". E.g. for eurostocks: 30,276/30,286 active-in-data-index have working URL (99.97% ✅), while 987k inactive docs still on legacy (⚠️ expected). The naive single-aggregation reads as "3% migrated" and is misleading.

**W3 — Cross-era stability (one doc demonstrates the whole pipeline)**

**Active = `activeTo` MISSING in the data index.** Once a vehicle goes inactive on the source site, `activeTo` gets stamped with the last-seen timestamp; while it's still active, the field is absent. So:
```json
{"bool": {"must": [{"term": {"site": "<SITE>"}}], "must_not": [{"exists": {"field": "activeTo"}}]}}
```

**Use `activeFrom` for "first ever seen".** It's the most persistent timestamp available. **Don't trust `createdAt` for this** — both indices reset it on doc-rewrite/rollover. Observed example on eurostocks: `activeFrom: 2022-03-14` but `createdAt: 2026-05-25` on the same doc. Old-index `CreatedAt` (capitalised) is similarly unreliable.

**`activeFrom` caveat — it resets on reactivation.** When a vehicle is deactivated (`activeTo` stamped) and later re-detected, `activeFrom` is updated to the reactivation time (`activeTo` cleared). So `activeFrom: today` doesn't necessarily mean "newly listed today" — it may be "reactivated today after being marked gone". To tell these apart, look for an inactive twin doc with the same VehicleId/storeId — if none exists, it was a persistent reactivation; if one exists with `activeTo` in the same window, it might be storeId churn from a workingUrl break (see the "url-change alert" entry in `market-study-knowledge.md`).

Find a **currently-active** doc whose `activeFrom < <URL-change deploy date>`. Assert:
1. data-index `_id` is identical to what it was before deploy (storeId stable ⇒ no identity break) — best confirmed by checking S3 vehicle JSON for the `_id` exists and was last written today
2. data-index `url` now matches the **working** URL pattern (proves the write-time `workingUrl ?? url` swap is happening on a doc that originally stored a legacy URL)
3. old-index `URL` is still the **legacy** URL pattern (proves the old index isn't accidentally getting the working URL through the same write path)
4. `md5(old-index URL) == data-index _id` (W1 must still hold on this old vehicle)

Query template:
```bash
curl -s "$ES/market-study-vehicle-data_rollover/_search" -H 'Content-Type: application/json' -d '{
  "size": 5,
  "query": {"bool": {
    "must": [
      {"term":  {"site": "<SITE>"}},
      {"range": {"activeFrom": {"lt": "<DEPLOY_DATE>"}}}
    ],
    "must_not": [{"exists": {"field": "activeTo"}}]
  }},
  "sort": [{"activeFrom": "asc"}],
  "_source": ["url","activeFrom","createdAt"]
}'
```

**Pitfall to watch for:** "active" has two definitions and they give wildly different counts:
- ✅ **Right:** `activeTo` missing in data index → currently active (eurostocks: 30,276)
- ❌ Wrong: any presence in data index → includes years-old inactives (eurostocks: ~1M)

A naïve "what fraction of data-index docs have the working URL pattern?" without the `activeTo`-missing filter gives ~3% migrated (misleading — 97% of those docs are inactive and were never going to be re-crawled). The right scope is the active set, which on eurostocks is 100% working.

**W4 — S3 ground truth (strongest invariant — needs `ams-s3`)**
For 2–3 random active vehicles, fetch the S3 vehicle JSON via `ams-s3 <data-index _id>` (the storeId IS the `_id`). Assert all four:
- `s3.legacyUrl == old-index.URL`
- `s3.workingUrl == data-index.url` (or `s3.url == data-index.url` when no separate workingUrl was set)
- `md5(s3.legacyUrl) == data-index._id`
- The working URL resolves (curl HTTP 200) OR the legacy URL 301-redirects to a 200

If all four hold for the sample, the URL/storeId machine end-to-end is consistent. Most failures show up here first.

**W5 — Live URL resolution**
`curl -sI -L --max-redirs 5` on 3–5 active sampled vehicles:
- Old-index `URL` → expect `301` then `200` (legacy auto-redirects to working)
- Data-index `url` → expect `200` directly

---

## Site-specific check overrides

Some checks are always N/A or always expected for certain site types. Apply before running Step 3 to avoid false positives.

**[22] `isUsed=false` + `dateOfFirstRegistration` — mandataire / pre-order sites**
Sites selling pre-allocated new cars (e.g. auto-ici, auto-aramis) have cars that are already first-licensed before sale. `dateOfFirstRegistration` on `isUsed=false` docs is **expected** — mark as N/A, not WARN.

**[27] `Percent` without `OriginalPriceBrutto` — Euro-priced sites**
Sites that display a catalogue discount percentage (e.g. auto-ici `percentage_part`) but do NOT expose the brand's original MSRP as a separate field. `OriginalPriceBrutto` is not stored for these sites by design. Mark as N/A, not WARN.

**Graylog time window — use last crawl start, not 24h**
Running G0–G6 over the last 24h includes log noise from earlier sessions / prior code versions. Always find the last crawl start first, then use an absolute time range:

```bash
# Step 1 - find last crawl start
curl -s -X POST -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" -H "X-Requested-By: curl" \
  "$GURL/api/views/search/sync?timeout=30000" \
  -d "{
    \"queries\": [{
      \"id\": \"q1\",
      \"timerange\": {\"type\": \"relative\", \"range\": 604800},
      \"query\": {\"type\": \"elasticsearch\", \"query_string\": \"facility:marketstudy* AND site:<SITE> AND message:\\\"Started crawling listing url\\\"\"},
      \"search_types\": [{\"id\": \"st1\", \"type\": \"messages\", \"limit\": 1, \"offset\": 0, \"sort\": [{\"field\": \"timestamp\", \"order\": \"DESC\"}]}]
    }]
  }" | jq '.results.q1.search_types.st1.messages[0].message.timestamp'

# Step 2 - use that timestamp as the absolute "from" in all G-checks
# "timerange": {"type": "absolute", "from": "<LAST_RUN>", "to": "2099-01-01T00:00:00.000Z"}
```

Same principle applies to ES check [39] (`IsListingValidatedVehicle`) — scope the query to `CreatedAt >= last run start`, not `now/d`.

Hard 404 on legacy = legacy URL rotted (not a crawler bug, but flag it; cache lookups still work via md5 hash).

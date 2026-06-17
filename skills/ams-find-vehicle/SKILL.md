---
name: ams-find-vehicle
description: Use when a vehicle is missing from search results, expected to be crawled but not showing up in ES, or when debugging "where did this vehicle go" across the pipeline (ES indices, S3, Graylog). Also use when asked to trace a specific vehicle by URL or storeId across prod/stage.
---

# ams-find-vehicle

Structured 5-phase workflow for tracing a missing vehicle through the Market Study pipeline.

---

## Phase 0 — Gather identifiers

Before querying anything, collect:

| Needed | Why |
|--------|-----|
| Vehicle URL (any format) | Starting point for storeId |
| Site key (e.g. `eurostocks`, `autoscout-de`) | Scopes Graylog queries |
| Expected time window | Narrows logs; "today's crawl" vs "since deploy" |
| Env (prod / stage / local) | Determines which ES + S3 to hit |

**Compute storeId** (stable key across all systems):
```bash
echo -n "https://exact-legacy-url.com/vehicle/123" | md5
# or on Linux: md5sum (strip trailing " -")
```

`storeId = md5(legacyUrl)` — the URL the crawler first discovered it under, before any workingUrl migration.

> **Gotcha:** Old search index stores `legacyUrl` in `URL`; Data index stores `workingUrl` in `url`. Searching old search by workingUrl won't find it. See Phase 2.

---

## Phase 2 — Check Elasticsearch

Env vars from `.env`: `ELASTIC_SEARCH_URL`, `ELASTIC_SEARCH_INDEX` (old search), `ELASTIC_SEARCH_VEHICLE_DATA` (data index).

### Old search index (what users see)
```bash
# By legacyUrl (stored as-is, uppercase URL field)
curl -s "$ELASTIC_SEARCH_URL/$ELASTIC_SEARCH_INDEX/_search" \
  -H "Content-Type: application/json" \
  -d '{"query": {"term": {"URL.keyword": "LEGACY_URL_HERE"}}, "size": 1, "_source": ["URL","Site","storeId","isActive"]}'

# By storeId
curl -s "$ELASTIC_SEARCH_URL/$ELASTIC_SEARCH_INDEX/_search" \
  -H "Content-Type: application/json" \
  -d '{"query": {"term": {"storeId.keyword": "STOREID_HERE"}}, "size": 1, "_source": ["URL","Site","storeId","isActive"]}'
```

### Data index (history + full lifecycle)
```bash
# By workingUrl or legacyUrl (stored as url, lowercase)
curl -s "$ELASTIC_SEARCH_URL/$ELASTIC_SEARCH_VEHICLE_DATA/_search" \
  -H "Content-Type: application/json" \
  -d '{"query": {"term": {"url.keyword": "URL_HERE"}}, "size": 1, "_source": ["url","site","storeId","isActive","updatedAt"]}'

# By storeId (most reliable across URL format changes)
curl -s "$ELASTIC_SEARCH_URL/$ELASTIC_SEARCH_VEHICLE_DATA/_search" \
  -H "Content-Type: application/json" \
  -d '{"query": {"term": {"storeId.keyword": "STOREID_HERE"}}, "size": 3, "_source": ["url","site","storeId","isActive","updatedAt"]}'
```

Record what you find:

| | Old search | Data index |
|-|------------|------------|
| Found? | ☐ yes / ☐ no | ☐ yes / ☐ no |
| isActive | | |
| updatedAt | | |

---

## Phase 3 — Check S3

Two S3 objects to look for:

| Object | What it is | How to fetch |
|--------|-----------|--------------|
| Stored vehicle JSON | Normalised AdVehicle; source of truth for ES write | `ams-s3 STOREID [env]` |
| Raw response cache | Daily HTML/JSON from the site | `ams-s3 URL [env]` (keyed `YYYYMMDD/md5(url)`) |

```bash
# Stored vehicle JSON (most useful — confirms crawler saved it)
# Run: ams-s3 <storeId> [prod|stage|local]

# Raw response cache (confirms crawler fetched the page today)
# Run: ams-s3 <vehicle-url> [prod|stage|local]
```

If stored vehicle JSON exists → crawler ran and parsed it → problem is in bulk-save or ES write.
If only raw cache exists → crawler fetched the page but parsing failed or SVL skipped it before saving.
If neither exists → crawler never fetched this vehicle.

---

## Phase 4 — Check Graylog pipeline

Use the sync API (works on Graylog 4 + 6). Auth + URL from `.env` → `GRAYLOG_AUTH_TOKEN` / `GRAYLOG_API_URL`.

Run queries in this order — stop when you find the break point:

```bash
# 1. Was the listing page crawled at all?
facility:marketstudy* AND site:[SITE] AND message:"Finished crawling listing url"

# 2. Was this vehicle published from listing parse? (look for storeId in full_message)
facility:marketstudy* AND site:[SITE] AND context:PARSER_DEBUGGING

# 3. Did it fail validation before ES write?
facility:marketstudy* AND site:[SITE] AND message:"Skip saving data vehicle to ES due to failed validation"

# 4. Was it deduped out? (same storeId already in batch)
facility:marketstudy* AND site:[SITE] AND message:"DUPLICATED ID CASE, DISCARDING MESSAGE"

# 5. Did bulk-save fail?
facility:marketstudy* AND level:3 AND context:RMQ_BULK_CONSUMER AND site:[SITE]

# 6. Is it in dead letter?
facility:marketstudy* AND message:"Too many retries for message, discarding it" AND site:[SITE]

# 7. Was it S3-cache hit (served from cache, not re-fetched)?
facility:marketstudy* AND message:"Response found in S3" AND site:[SITE]
```

---

## Phase 5 — Root cause map

| S3 vehicle JSON | Old search ES | Data ES | Root cause |
|-----------------|---------------|---------|------------|
| ✅ | ✅ | ✅ | Vehicle is fine. Wrong URL searched — check legacyUrl vs workingUrl mismatch. |
| ✅ | ❌ | ✅ | **Deactivated.** `isActive=false` in old search. Deactivation ran after crawl. |
| ✅ | ❌ | ❌ | **Bulk-save write failed.** Check `MS_BULK_SAVE_DL`. Redeliver from DL queue. |
| ❌ | ❌ | ❌ (Graylog: crawled) | **Parse failed or SVL gate skipped details.** Check PARSER_DEBUGGING logs. SVL may have wrongly classified as sold (check `bulk-save-listing-vehicle.service.ts` logic). |
| ❌ | ❌ | ❌ (Graylog: not crawled) | **Crawl never reached this vehicle.** Check getBrandsAndModels output, listing 403/404 errors, or site disabled in CrawlingSites.ts. |
| ✅ | ✅ | ❌ | Validation blocked data-index write only — old search write path is separate. Cosmetic: old search OK, data index diverged. |

---

## Quick reference

```bash
# Compute storeId
echo -n "LEGACY_URL" | md5

# ES old search (legacyUrl, uppercase fields)
curl -s "$ELASTIC_SEARCH_URL/$ELASTIC_SEARCH_INDEX/_search" -H "Content-Type: application/json" \
  -d '{"query":{"term":{"storeId.keyword":"STOREID"}},"size":1}'

# ES data index (workingUrl, lowercase fields, full history)
curl -s "$ELASTIC_SEARCH_URL/$ELASTIC_SEARCH_VEHICLE_DATA/_search" -H "Content-Type: application/json" \
  -d '{"query":{"term":{"storeId.keyword":"STOREID"}},"size":3}'

# S3 stored vehicle JSON
# ams-s3 STOREID [prod|stage]

# Graylog: validation blocks
# facility:marketstudy* AND site:[SITE] AND message:"Skip saving data vehicle to ES due to failed validation"

# Graylog: dead letter
# facility:marketstudy* AND message:"Too many retries for message, discarding it" AND site:[SITE]
```

---

## Key gotchas

- **legacyUrl ≠ workingUrl in ES.** Old search stores `legacyUrl` in `URL`. Data index stores `workingUrl` in `url`. Always try storeId, not URL, for cross-index lookups.
- **Validation split.** `"Skip saving data vehicle to ES due to failed validation"` only blocks the data index. Old search can still have the vehicle even after validation rejected it.
- **SVL gate** (`MS_BULK_SAVE_LISTING_VEHICLE_CHECK`) routes sold vehicles to skip detail fetch. If SVL wrongly tagged a vehicle as sold, it still goes through bulk-save from listing data — but with fewer fields. Check if the vehicle appears but with missing detail-page fields.
- **Dedup is in-memory per batch**, not cross-batch Redis. Same vehicle from two listing pages will both be processed; only the last ES upsert wins (same storeId = same doc).
- **New search index frozen** since Mar 2025 — still receives writes but do not query it for debugging, reads are disabled.

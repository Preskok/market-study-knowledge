# Graylog Query Templates

URL: `.env` → `GRAYLOG_API_URL` / `GRAYLOG_AUTH_TOKEN`. Three commented blocks (`# local` / `# stage` / `# prod`); local is active by default, stage (Graylog 6.x beta) and prod (Graylog 6.1.x) credentials populated but commented. Read directly from those lines for non-local queries — don't uncomment (breaks running app).
Local: Graylog 4.2 on devenv (active by default).

Time: Relative `from=86400` (24h), Absolute `from=2026-04-22T00:00:00.000Z&to=2026-04-22T23:59:59.000Z`.

Auth: Basic with `<TOKEN>:token` (token in `.env` → `GRAYLOG_AUTH_TOKEN`).

Facility: prod = `marketstudy`, stage = `marketstudy-stage`, **local = `marketstudy-local`** (set by `GRAYLOG_FACILITY` in `.env`). The wildcard `facility:marketstudy*` matches all three; use the exact name when isolating a specific environment.

---

## API note: use views/search/sync, NOT universal/relative

The legacy `/api/search/universal/relative` endpoint **returns 400 "must not be empty" on Graylog 6.x**.
Use `POST /api/views/search/sync` instead. Works on both Graylog 4 (local) and 6 (prod).

```bash
curl -s -X POST -u "$TOKEN:token" \
  -H "Content-Type: application/json" -H "X-Requested-By: curl" \
  "$GRAYLOG_API_URL/api/views/search/sync?timeout=30000" \
  -d '{
    "queries": [{
      "id": "q1",
      "timerange": {"type": "absolute", "from": "2026-05-03T00:00:00.000Z", "to": "2026-05-04T00:00:00.000Z"},
      "query": {"type": "elasticsearch", "query_string": "site:subito AND facility:marketstudy AND message:\"Finished HTTP request\""},
      "search_types": [{"id": "st1", "type": "messages", "limit": 1, "offset": 0}]
    }]
  }'
```

Read `results.q1.search_types.st1.total_results` for the count. Use `messages` type with `limit:1` rather than `pivot`/`terms` — those frequently fail with cryptic errors on the sync endpoint.

For multi-day per-metric matrices see `multi-day-trend-analysis.md`.

---

## General

```
facility:marketstudy* AND level:3
facility:marketstudy* AND site:[SITE]
facility:marketstudy* AND level:3 AND site:[SITE]

# Clean error log (Marko's saved query style)
facility:marketstudy* AND level:3 AND NOT context:FETCH_EXTERNAL AND NOT context:RMQ_INFO AND NOT full_message:"Too many retries for message, discarding it"
```

---

## Specific issues

```
# Producer failed
facility:marketstudy* AND site:[SITE] AND message:"Problem preparing listingUrl messages for site"

# Pagination exception
facility:marketstudy* AND site:[SITE] AND message:"Exception in iterateThroughVehicleListPages"

# Cheerio undefined
facility:marketstudy* AND site:[SITE] AND message:"cheerio.load() expects a string"

# HTTP status
facility:marketstudy* AND site:[SITE] AND errorCode:403
facility:marketstudy* AND site:[SITE] AND errorCode:404
facility:marketstudy* AND site:[SITE] AND errorCode:410   # fake 410 pattern (hasznalt-auto)

# ScrapeDo / browser / curl
facility:marketstudy* AND site:[SITE] AND full_message:"Exception doing scrapeDo request"
facility:marketstudy* AND site:[SITE] AND full_message:"Exception doing browser request"
facility:marketstudy* AND "exception doing curl request"

# Chromium / Puppeteer timeouts (wraps net::ERR_TUNNEL_CONNECTION_FAILED, ERR_CONNECTION_RESET, etc.)
# Do NOT search "net::ERR" or "TUNNEL" — those strings never reach Graylog.
facility:marketstudy* AND site:[SITE] AND "Browser timeout reached"

# Correlate Browser-timeout to upstream proxy: join via request_id to the "Starting browser request"
# log (same request_id), which carries specificProxy.
facility:marketstudy* AND site:[SITE] AND "Starting browser request"
```

---

## Infrastructure / RMQ / DB

```
# Bulk consumer (MySQL/ES)
facility:marketstudy* AND level:3 AND NOT context:FETCH_EXTERNAL AND context:RMQ_BULK_CONSUMER

# DB dropped
facility:marketstudy* AND message:"ECONNREFUSED"

# S3 cache key visible in log
facility:marketstudy* AND message:"Response found in S3" AND site:[SITE]

# DL entries
facility:marketstudy* AND message:"Too many retries for message, discarding it"

# Duplicate RMQ listing sends (channel/instance restart detection)
facility:marketstudy* AND message:"Sending shuffled"

# RMQ dedup (not failures)
facility:marketstudy* AND message:"DUPLICATED ID CASE, DISCARDING MESSAGE"
```

---

## Validation

```
facility:marketstudy* AND site:[SITE] AND context:VALIDATION_PROGRESSIVE
facility:marketstudy* AND site:[SITE] AND context:VALIDATION_PROGRESSIVE AND changes:"{\"MODEL\":*}"
facility:marketstudy* AND context:VALIDATION AND message:"Details URL validation failed"
facility:marketstudy* AND site:[SITE] AND message:"Skip saving data vehicle to ES due to failed validation"

# S3-vs-ES comparison failures
facility:marketstudy* AND context:VALIDATION AND message:"Vehicle S3 vs ES comparison failed in object prop"
```

---

## Tracing a single run

```
request_id:"market_study-production-[HASH]-..."
facility:marketstudy* AND site:[SITE] AND context:REQUEST_LOGGER
```

---

## Marko's saved query (S3-vs-ES validation anomalies)

```
facility:marketstudy* AND context:VALIDATION 
  AND NOT full_message:"Finished validating data vehicles" 
  AND NOT message:"Details URL validation failed for URL" 
  AND NOT message:"Reassigned value(s) of failed data vehicle validation fields to null" 
  AND NOT message:"Skip saving data vehicle to ES due to failed validation" 
  AND NOT message:"No URLs for details URLs validation for site" 
  AND NOT message:"Got less URLs for details URLs validation for site than expected" 
  AND NOT message:"Prepared tasks for details URL validation" 
  AND NOT full_message:"S3 vehicle not found in ES" 
  AND NOT message:"Finished S3 and ES vehicle validation" 
  AND NOT message:"Vehicle validation failed in object prop"
```
(Saved query ID: `66b09450411f8078b7959414`)

---

## Tips

- "Show Top Values" defaults to top 15 — increase limit.
- Export CSV, group in PhpStorm as cross-check.
- "Show surrounding messages" ±10s correlates errors across contexts. Use this when an error has no `request_id` (e.g. `Errored RMQ channel MS_RECEIVE_CRAWL_JOBS`) but you want to see what happened in the same time window.
- Filebeat `filebeat_*` catches silent worker kills Graylog misses.
- Retention ~7-10 days (varies with overall log volume across Preskok projects).
- `RMQ_RECEIVE_CRAWL_JOBS` errors are outside rtracer — match by timestamp.
- `upper:` for case-insensitive substring inside a field — but `upper:` itself is case-sensitive about the keyword.

---

## Streams, Event Definitions, Alerts (per-site grace periods)

The pipeline for setting up a per-site rate-limited alert (e.g. "warn me when scrape.do `maxRequestCost` is exceeded for ANY site, but no more than once per 10 min PER SITE"):

```
Stream (filter: marketstudy + WARN + "Request cost is bigger than max cost")
   ↓
Event Definition (Event Key = `site`, aggregation window = 10 min)
   ↓
Alert / Notification (email with site, message count, sample log)
```

**Why all three layers:**
- **Stream** — a sieve at the door. Pre-filters incoming logs so the Event Definition only scans relevant volume. Skipping streams forces Event Definitions to scan all historical messages → slow + can miss real-time messages.
- **Event Definition** — `event_key` (e.g. `site`) lets Graylog apply the grace period **per value**, not globally. Without it, one noisy site mutes alerts for all other sites.
- **Alert from Stream alone** is fine for "fire on any matching message", but **cannot** use Event Key → no per-site cooldown. Use Event Definition whenever you want per-key grouping.

**Aggregation pattern** — "10 messages for site X in the last 10 minutes" → Event Definition with COUNT > 10, window 10m, key = `site`.

**Grace period scoping** — set on the Event Definition, not the Stream. Honored per-Event-Key — so site A muting itself doesn't mute site B.

**Reference:** [Graylog Event Definitions use case docs](https://go2docs.graylog.org/6-1/interacting_with_your_log_data/event_definitions_use_case.htm).

## Contexts
`CRAWLER` / `REQUEST_LOGGER` / `FETCH_EXTERNAL` / `VALIDATION` / `VALIDATION_PROGRESSIVE` / `PARSER_DEBUGGING` / `RMQ_INFO` / `RMQ_BULK_CONSUMER` / `TASK`

---

## DataDome-protected sites (Subito, etc.)

Per-request log messages — useful for `request_id` tracing or per-day counting:

```
# Successful axios request
facility:marketstudy AND site:[SITE] AND message:"Finished HTTP request"

# Successful browser (Puppeteer) request
facility:marketstudy AND site:[SITE] AND message:"Finished browser request"

# 403 received
facility:marketstudy AND site:[SITE] AND message:"Response was forbidden"

# Cookie persistence health (Subito MAR-2039 indicator)
facility:marketstudy AND site:subito AND message:"proxy has no cookies in Redis"
facility:marketstudy AND site:subito AND message:"datadome cookie invalidated server-side"
facility:marketstudy AND site:subito AND message:"403 with no DataDome cookie on proxy"

# Recovery flow events
facility:marketstudy AND site:subito AND message:"validating DataDome cookie via protected listing URL"
facility:marketstudy AND site:subito AND message:"DataDome recovery succeeded"
facility:marketstudy AND site:subito AND message:"recovery URL blocked but fresh DataDome cookie received"

# Listing-level (producer) — almost always healthy even when detail fetches fail
facility:marketstudy AND site:[SITE] AND message:"Started crawling listing url"
facility:marketstudy AND site:[SITE] AND message:"Finished crawling listing url"
```

Quick health snapshot: if `Response was forbidden` count is rising day-over-day while `Finished crawling listing url` stays stable, anti-bot is adapting — **do a multi-day trend analysis** (see `multi-day-trend-analysis.md`).

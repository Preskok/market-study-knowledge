# Multi-Day Crawl Trend Analysis

**Use this when:** A crawler's vehicle count is dropping over multiple days and you suspect anti-bot pressure (DataDome, Cloudflare, Akamai) or proxy reputation degradation rather than a code/selector failure.

**Do NOT use this when:** The drop is sudden (overnight), zero vehicles for one site (likely selector broke), or producer threw exceptions (`Problem preparing listingUrl messages`). Those are deterministic bugs — read the code.

---

## Decision tree: which analysis to run

```
Vehicle count dropped — but how?
├─ Sudden zero / parser exceptions → SELECTOR ANALYSIS
│   • read crawler code, diff with last working version
│   • check Slack for site-redesign mentions
│   • check failure-patterns.md sections "Parsing / HTML / JSON" and "Per-property drop"
│
├─ Per-property drop only (e.g. ENGINECAPACITY 78%) → SELECTOR ANALYSIS for that field
│
├─ Gradual drop over 2-7 days, requests still happening → REQUEST/ANTI-BOT TREND ANALYSIS (this doc)
│   • DataDome / Cloudflare / Akamai signature
│   • Forbidden count creeping up in Graylog
│   • `lst_started` / `lst_finished` still healthy
│
└─ Sudden volume spike (5x+ requests, success rate halved) → BACKFILL/RE-CRAWL FALLOUT
    • Check if backfill ran that day
    • Damage to proxy reputation may persist for days
```

---

## The methodology

### Step 1 — Pull unique vehicles per day from Elasticsearch

This is your ground-truth output count. Doc count includes updates; URL cardinality is the real vehicle count.

```bash
# Credentials in /Users/filipozbolt/Projects/market-study/.env (commented ELASTIC_SEARCH_URL line)
curl -s -u "$ES_USER:$ES_PASS" \
  "https://es-marketstudy.es.eu-central-1.aws.cloud.es.io:9243/marketstudy_search_rollover/_search" \
  -H "Content-Type: application/json" -d '{
  "size": 0,
  "query": {"bool": {"must": [
    {"range": {"CreatedAt": {"gte": "now-7d/d", "lte": "now+1d/d", "time_zone": "Europe/Ljubljana"}}},
    {"term": {"Site": {"value": "<SITE>"}}}
  ]}},
  "aggs": {"site_group": {"terms": {"field": "Site", "size": 100}, "aggs": {
    "daily": {"date_histogram": {"field": "CreatedAt", "calendar_interval": "1d", "time_zone": "Europe/Ljubljana", "format": "8uMMdd"},
      "aggs": {"url_count": {"cardinality": {"field": "URL", "precision_threshold": 40000}}}}}}}}'
```

### Step 2 — Discover the crawler's distinct log message strings

Every crawler emits a different set of messages. Sample 200 messages for one day to see what's there:

```python
# pseudocode — one views/search/sync POST with limit=200, then dedupe message field
msgs_seen = set(m['message']['message'] for m in result.messages)
```

You're looking for things like:
- `Finished HTTP request` / `Exception doing HTTP request`
- `Finished browser request` / `Exception doing browser request`
- `Response was forbidden` (403)
- Site-specific anti-bot messages (e.g. for Subito: `proxy has no cookies in Redis`, `datadome cookie invalidated server-side`, etc.)
- `Started crawling listing url` / `Finished crawling listing url`
- `Retry attempt`

### Step 3 — Build the per-day per-metric matrix

For each day, count each message type. This is N queries (~10-15 metrics × 4-7 days = 40-100 queries). Run them via Python script for speed (parallel-friendly via threading if needed).

The Graylog 6.x endpoint that works: **`POST /api/views/search/sync`** with `messages` search type and `limit:1` — read `total_results` from the response.

```python
def count_msg(from_ts, to_ts, message_query):
    payload = {"queries": [{
        "id": "q1",
        "timerange": {"type": "absolute", "from": from_ts, "to": to_ts},
        "query": {"type": "elasticsearch", "query_string": f'site:<SITE> AND facility:marketstudy AND message:"{message_query}"'},
        "search_types": [{"id": "st1", "type": "messages", "limit": 1, "offset": 0}]
    }]}
    r = requests.post(f"{GRAYLOG_URL}/api/views/search/sync?timeout=30000",
                      auth=(TOKEN, "token"),
                      headers={"Content-Type": "application/json", "X-Requested-By": "curl"},
                      json=payload, timeout=40)
    return r.json()['results']['q1']['search_types']['st1']['total_results']
```

### Step 4 — Present the comparison table

Format that's easy to interpret:

```
=== FULL METRIC TABLE ===
Metric              Day 1    Day 2    Day 3    Day 4
--------------------------------------------------------
http_fin            12549    53808    13588    15099
http_ex              5615    81415    20660    23276
br_fin               4746    22233     5691     6090
br_ex                5990    96255    22671    25460
forbidden            8345     8623    10876    11029   ← creeping up = anti-bot stronger
no_proxy_cook        1325    29604     7166     8117   ← spike on volume day, never recovered
rec_succ              908    23286     5781     6552
rec_blocked           860    22772     5663     6432
lst_started          1193     1202     1122     1149
lst_finished         1180     1181     1106     1133

=== DERIVED STATS ===
total_requests      28936   253729    62904    70142
http_SR%             69.0     39.8     39.3     39.1   ← sudden halving = anti-bot adapted
browser_SR%          44.2     18.8     20.1     19.3
overall_SR%          59.8     30.0     30.6     30.2
listing_completion%  98.9     98.3     98.6     98.6   ← still healthy = code OK
```

### Step 5 — Combine with ES vehicles for the full picture

```
| Date  | Unique vehicles (ES) | Total requests | Overall SR% | Forbidden | no_proxy_cook |
|-------|---------------------:|---------------:|------------:|----------:|--------------:|
| Day 1 |              403,166 |         28,936 |        60   |     8,345 |         1,325 |
| Day 2 |              468,133 |        253,729 |        30   |     8,623 |        29,604 |  ← backfill
| Day 3 |              219,284 |         62,904 |        31   |    10,876 |         7,166 |
| Day 4 |              254,545 |         70,142 |        30   |    11,029 |         8,117 |
```

### Step 6 — Interpret

What each pattern usually means:

| Pattern | Likely cause |
|---|---|
| Forbidden count slowly rising day after day, total requests stable | Anti-bot is adapting to proxy fingerprints |
| Forbidden count stable, success rate stable | Steady state; nothing changed |
| Volume spike one day → success rate drop that doesn't recover | Backfill burned proxy reputation; need cooldown or fresh IPs |
| `no_proxy_cook` (or equivalent fresh-proxy log) high | Proxy sessions not being persisted (could be a cookie persistence bug — see Subito MAR-2039) |
| `lst_finished / lst_started` ≈ 100% but vehicles dropping | Crawler is reaching pages but failing to parse details — check detail-fetch success rate |
| Recovery success rate steady over time | Recovery mechanism itself is working; the issue is upstream (proxy/cookie state) |
| Recovery success rate degrading | Recovery URL itself is being blocked — diversify recovery URLs |

---

## Key tooling notes

- **Time zone:** Logs are UTC, business days are Europe/Ljubljana (UTC+2). Day boundaries: `YYYY-MM-(DD-1)T22:00:00Z` to `YYYY-MM-DDT22:00:00Z`.
- **Graylog 6.x quirk:** The legacy `/api/search/universal/relative` returns 400 "must not be empty". Use `/api/views/search/sync` (Graylog 6.x supports both Graylog 4 and 6 with this endpoint).
- **Auth:** Basic auth with token as username, literal string `"token"` as password. Token in `.env` `GRAYLOG_AUTH_TOKEN` (commented prod section).
- **Pivot/terms search type often fails** on the views/search/sync endpoint with cryptic errors. The simplest reliable approach is `messages` type with `limit:1` and reading `total_results` per query — slower but always works.
- **Parallel queries:** Python `concurrent.futures.ThreadPoolExecutor(max_workers=10)` cuts a 60-query matrix from minutes to ~15s.

---

## Common conclusions and next steps

After the analysis, you'll usually land on one of:

1. **"Anti-bot is winning"** — Recommend: rotate proxies, diversify recovery URLs, contact scrape.do support if available, consider escalation to higher tier.
2. **"Proxy pool burnt by backfill"** — Recommend: separate proxy pool for backfills, let main pool cool down 24-72h, monitor `forbidden` count trending back down.
3. **"Cookie persistence bug"** — Recommend: check the `afterRequest` flow, verify cookies acquired during recovery are actually saved to Redis. (Subito MAR-2039 fix pattern.)
4. **"It's actually fine"** — One-off spike, normal variance. Document and move on.

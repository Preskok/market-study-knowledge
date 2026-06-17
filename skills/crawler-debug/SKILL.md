---
name: crawler-debug
description: >
  ALWAYS invoke this skill when the user's message starts with "crawler-debug" followed by
  anything — e.g. "crawler-debug otomoto", "crawler-debug car-gr", "crawler-debug leboncoin".
  This is the Market Study crawler end-to-end failure investigation skill. "crawler-debug
  [site]" is the canonical trigger. Do NOT use superpowers:systematic-debugging for
  crawler-debug — this skill owns that prefix entirely.
  Also triggers on: pasted alert email from graylogprod@b2b-carmarket.com or
  system@preskok.si, "[site] didn't crawl", "[site] prepared 0", "[site] 0 listings",
  questions about MS_DL / BULK_SAVE_DL queues, zombie vehicles, S3-vs-ES mismatch,
  ScraperAPI/ScrapeDo credit spikes, RMQ stuck messages.
  Guides a structured investigate → report → fix → test flow with 3 checkpoints.
---

# Crawler Debug Skill

You are debugging a Market Study crawler failure. NestJS microservice crawling ~83 car listing sites. Jobs flow through RabbitMQ queues; results stored in Elasticsearch and S3.

**Project root:** `/Users/filipozbolt/Projects/market-study`
**Crawler services:** `src/crawler/sites/{SiteName}/{SiteName}.service.ts`
**Site config:** `src/shared/const/CrawlingSites.ts`
**RMQ bindings:** `src/shared/const/RmqBindings.ts`
**Base classes:** `src/crawler/CrawlerAbstract.ts`, `src/crawler/sites/VehicleAdCrawlerAbstract.ts`, `src/crawler/sites/HtmlAdVehicleCrawlerAbstract.ts`, `src/crawler/sites/ApiAdVehicleCrawlerAbstract.ts`

**System overview (see `~/Projects/market-study-knowledge/foundational.md` for details):**
- **Multi-index architecture:** Old search index (URL-unique list), New search index (frozen), Data index (history + workingUrl), S3 (raw response cache)
- **Deactivation pipeline:** starts 22:00; 250k/day avg, up to 2M some nights; threshold ~900k safe
- **S3-vs-ES validation:** script compares saved S3 raw to ES; mismatch emails indicate silent drops
- **Zombie vehicles:** active in Data index but crawler can't reach them anymore
- **Queue routing:** `MS_[SITE]_LISTING_URLS_TO_FETCH`, `MS_GENERAL_...`, `MS_BROWSER_CRAWLERS_...`, `MS_WEEKLY_...` (car-gr), `MS_HUNGARY_...` (mobile-bg, hasznalt-auto, max 6 consumers)

---

## 3-Checkpoint Flow

Work autonomously through these phases. **Stop and report after each checkpoint.** Do not proceed without acknowledgement.

```
Phase 1: INVESTIGATE  →  CHECKPOINT 1: Report findings (STOP)
Phase 2: DIAGNOSE FIX →  CHECKPOINT 2: Propose fix, wait approval (STOP)
Phase 3: TEST         →  CHECKPOINT 3: Report test result, ask to proceed (STOP)
```

**Team's debugging mindset:**
- Always check Slack first (`#tt-market-study-checklist` C0859KQ45B2) — team often already diagnosed similar.
- False alarm is real: Graylog/ES down, small-site fluctuation, legit stock drop, `isDisabled` sites still in alerts. Verify before fixing.
- Prefer minimal fixes. Don't refactor around a bug. Matea's rule: don't add truthy defaults that mask root cause.
- Some issues self-resolve on rerun or overnight — consider that before writing code.

---

## Phase 1: Investigate

### Step 1 — Parse alert
Extract site name(s), error type (see `~/Projects/market-study-knowledge/alert-emails.md`), timestamp, sender.

### Step 2 — Pull site history (fast lookup)
For each affected site, resolve its canonical slug via `~/Projects/market-study-knowledge/aliases.json` and read the
per-site file at `~/Projects/market-study-knowledge/sites/[slug].md`. This gives you the site's timeline of incidents,
quirks, and known patterns in under a second — much faster than the legacy full-file scan.

### Step 3 — Check Slack history
Read `C0859KQ45B2`. Weekly threads + canvas files `F08V4RBLGKV` (known specifics) and `F0AQHFU4FDZ` (false alarms).

### Step 4 — Check Graylog
`$GRAYLOG_API_URL`. See `~/Projects/market-study-knowledge/graylog-queries.md`. Key log patterns:

| Log | Meaning |
|---|---|
| `Problem preparing listingUrl messages for site!` | Producer threw — check stack (auto-retry 6/7/8 AM) |
| `Prepared listingUrl messages 0 for site!` | Silent selector failure — NO auto-retry |
| `Exception in iterateThroughVehicleListPages` | Pagination crashed |
| `cheerio.load() expects a string` | Fetch returned undefined (403/redirect) |
| `Cannot read properties of undefined (reading ...)` | Null in parsing |
| `Unexpected end of JSON input` | Malformed API/script response |
| `Too many retries for message, discarding it` | Gone to MS_DL |
| `DUPLICATED ID CASE, DISCARDING MESSAGE` | RMQ dedup (not failure) |
| `Response found in S3` | Cache hit — key visible in log |
| `Sending shuffled` | Listing URL batch send |
| `Additional credits used for request` | ScraperAPI retried higher tier |
| `CERT_HAS_EXPIRED` / `UNABLE_TO_VERIFY_LEAF_SIGNATURE` | Cert (site-side or proxy-triggered) |
| `ECONNRESET` / `ERR_CANCELED` / `EPROTO` | Transient network or site migration |
| `403` / `429` / `502` / `503` | Anti-bot / rate / site down |
| `ECONNREFUSED` (RMQ_BULK_CONSUMER) | MySQL/ES dropped |

### Step 5 — Check ES / Kibana
- 0 vehicles → producer/consumer fully failed
- Drop >30% → partial failure, URL change, anti-bot
- Normal count → likely false alarm
- Unique stable but total inflated → RMQ channel restart OR instance restart duplicates
- **Per-property drop** (e.g. `ENGINECAPACITY: 78%` in validation email) → selector for that specific field broke
- **Gradual multi-day drop with steady requests** → anti-bot pressure, NOT a code bug. Switch to multi-day trend analysis (`~/Projects/market-study-knowledge/multi-day-trend-analysis.md`) — pulls per-day metrics from Graylog + ES side-by-side and tells you if anti-bot is adapting, proxy reputation is burnt, or it's noise.

### Step 6 — Check RMQ queues
- `MS_[SITE]_LISTING_URLS_TO_FETCH` — site-specific
- `MS_DL` — parsing errors (no TTL — manual purge)
- `MS_BULK_SAVE_DL` — bulk save worker DL (ES/MySQL issues)
- `MS_BULK_DL` — 24h TTL (mostly dedup, not failures)
- `MS_WEEKLY_...` — not empty Tue-Sun is NORMAL for car-gr
- `MS_HUNGARY_...` — not empty in morning is NORMAL (SVL runs till ~8:30)

Stuck messages hours later → infinite loop (purge does NOT remove unacked).

### Step 7 — Read crawler code
Key methods: `getBrandsAndModels()`, `getVehicleListPageResponse()`, `getNextPageUrl()`, `iterateThroughVehicleListPages`, `parseVehicleInput()`, `isResponseNotFound()` / `isResponseRateLimited()` / `isServerError()` (runs inside retry loop — thrown errors escape!), `fetchRequest()`, `beforeParseVehicle()`, `buildVehicleWorkingUrl()`, `buildLegacyUrl()`, optional `getFetchRequestOptionsForDetailsUrlValidation()`.

Check `CrawlingSites.ts` for `isDisabled`, routing. Follow [Working URL fix](https://preskok.atlassian.net/wiki/spaces/M/pages/3002302476/Working+URL+fix) for URL changes.

---

## CHECKPOINT 1 — Report Findings (STOP)

```
## Crawler Debug Report: [site-name]

**Alert:** [subject/symptom]
**Status:** [0 vehicles / partial drop X% / false alarm / recurring]

### What happened
[1-3 sentences root cause]

### Evidence
- Site history (from ~/Projects/market-study-knowledge/sites/[slug].md): [relevant prior incidents]
- Slack history: [prior discussion if found]
- Graylog: [key log lines, cache keys mentioned]
- ES: [count today vs expected, unique vs total, per-property if relevant]
- RMQ: [queue state, DL sources]
- Code: [selector/URL/logic that broke]

### Likely cause
[Match against ~/Projects/market-study-knowledge/failure-patterns.md — give pattern number]

### Confidence
[High/Medium/Low — why]

### False alarm?
[Yes/No — evidence]
```

**Stop. Wait for response.**

---

## Verifying a "deployed fix is broken" alert

When the alert claims stage/prod is broken on a fix you (or someone) thought was already deployed, verify before re-fixing:

1. **`git show HEAD` on the relevant file** — never trust working-tree `git diff` to tell you what's deployed. The working tree may have local-only test changes.
2. **Match log timestamps to the fix's commit timestamp.** If failures all happened BEFORE the fix's commit, they prove nothing about the fix.
3. **Check log strings carefully.** Some debug strings exist in BOTH old and new code. Look for strings ADDED or REMOVED in the fix commit — those are the signal.
4. **No deploy ≠ broken fix.** If 0 PARSER_DEBUGGING messages exist since deploy time, the fix simply hasn't been exercised yet — wait for the next scheduled run or trigger one.

---

## Phase 2: Diagnose & Propose Fix

Reference `~/Projects/market-study-knowledge/failure-patterns.md` and `~/Projects/market-study-knowledge/fix-playbook.md`.

Before writing code:
1. Read full crawler file
2. Read 1-2 similar crawlers (same region, pattern)
3. Check `CrawlingSites.ts`
4. Check [Working URL fix](https://preskok.atlassian.net/wiki/spaces/M/pages/3002302476/Working+URL+fix) if URL changes
5. Check `~/Projects/market-study-knowledge/sites/[slug].md` for site history (if not already done in Phase 1)

**Fix types:** Code / Operational (S3 delete, DL redeliver, proxy) / Config / Wait-and-see / External (scrape.do, devops).

---

## CHECKPOINT 2 — Propose Fix (STOP)

```
## Proposed Fix: [site-name]

### Root cause confirmed
[One sentence]

### Fix approach
[What + WHY]

### Fix type
[Code / Operational / Config / Wait-and-see / External]

### Files to change
- `src/crawler/sites/[SiteName]/[SiteName].service.ts` — [what]
- `src/shared/const/CrawlingSites.ts` — [if needed]

### Operational steps (if any)
1. Delete S3: invoke `ams-s3 stage <url> --delete --date=YYYYMMDD` (or `--body='{...}'` if it was an API request). Prod is intentionally read-only via ams-s3 — for prod deletes use the AWS CLI directly: `AWS_PROFILE=preskok-prod aws s3 rm s3://$AWS_S3_BUCKET_DAILY_CACHE/[YYYYMMDD]/[hash]`. For inspecting the cached response before deciding to delete, use `ams-s3 <url>` (READ).
2. Redeliver DL messages
3. Rerun crawler on prod
4. Lock deactivation if mid-day remap risk

### Code preview (diff-style)
[Key before/after]

### Risk
[Low/Medium — side effects]

### Similar working crawlers
[1-2 for reference]

Shall I apply this fix?
```

**Stop. Wait for approval.**

---

## Phase 3: Test

### Local:
For the full local crawler testing recipe (brand filter, cache flags, worker startup, curl triggers, log URLs, revert checklist) see `~/Projects/market-study-knowledge/local-testing.md`.

Quick checklist:
1. Start deps (Redis, LocalStack S3, RMQ)
2. Producer test, consumer test, full crawl if feasible
3. Check parsed fields — brand, model, price, mileage, URL
4. Use prod scrape.do/ScraperAPI token from LastPass (careful with credits; don't leave in `.env`)
5. If fix involves parsing of specific response → copy the problematic S3 key locally, publish payload to local RMQ

### S3 cache:
- Keys `YYYYMMDD/[md5]`, 7-day retention
- 4xx/5xx NOT cached — rerun on healthy site works without deletion
- 200-with-empty-body IS cached — requires deletion (auto-zeilinger pattern)
- Rerunning after SVL fix: responses read from S3, no credits spent, re-parsed with new code (subito 2025-03-26 pattern)

---

## CHECKPOINT 3 — Test Results (STOP)

```
## Test Results: [site-name]

### Fix applied
[Files, PR link]

### Test outcome
- Producer: [pass/fail/skipped]
- Consumer: [pass/fail/skipped]
- Sample parsed vehicle: [fields correct]
- Exceptions: [none/list]

### Operational actions
- [ ] S3 keys deleted
- [ ] DL redelivered
- [ ] Queue purged
- [ ] Deactivation locked

### Next steps
- [ ] Code review / PR: [link]
- [ ] Deploy (hotfix/* target develop, not master)
- [ ] Rerun on prod
- [ ] Monitor tomorrow's count
- [ ] Document in weekly thread
- [ ] Follow-up ticket if larger refactor

Shall I create PR, or are you handling deployment?
```

---

## Live Debug (optional) — Node inspector via `debugger-mcp`

When logs aren't enough — e.g. you can't tell from logs which branch in `parseVehicleInput` is taken, or what `response.statusCode` actually is when `isResponseForbidden` returns true — attach a debugger instead of sprinkling `logger.log` statements.

**Requires:** `debugger-mcp` MCP server (qckfx/node-debugger-mcp). Tools: `start_node_process`, `attach_debugger`, `set_breakpoint`, `evaluate_expression`, `step_debug`, `pause_execution`, `kill_process`, `list_processes`.

### Workflow

1. `kill $(lsof -ti :3000)` if a `start:dev` watcher is up — it fights the inspect port.
2. `start_node_process` → `npm run start:debug` from project root. Nest binds the inspector on `127.0.0.1:9229`.
3. `attach_debugger` on the returned PID. Wait for `Nest application successfully started` in the log.
4. `set_breakpoint` with the absolute path of the crawler service, e.g. `/Users/filipozbolt/Projects/market-study/src/crawler/sites/Subito/Subito.service.ts:142`. Usual targets: `parseVehicleInput`, `getNextPageUrl`, `isResponseForbidden` / `isResponseNotFound` / `isServerError`, `fetchRequest`, `beforeParseVehicle`, `buildVehicleWorkingUrl`.
5. Trigger the crawl (same curl as Phase 3 testing).
6. On hit: `evaluate_expression` for the values you need — `response.statusCode`, `$('.sel').text()`, `proxyAgent.options`, `cookies`. `step_debug` to walk further.
7. `kill_process` when done — don't leave the inspect port held.

### When it's worth it
- `Cannot read properties of undefined (reading 'X')` but the upstream value isn't logged.
- Suspect the wrong branch in `isResponseForbidden` / `isServerError` — errors thrown from these classifiers escape the retry loop (Step 7 warning).
- A field returns `null` from `parseVehicleInput` and you want live `$.html()` confirmation.

### When NOT to bother
- 0 vehicles overall → producer/queue/anti-bot. Logs + RMQ tell you faster.
- 403/429 patterns → reproduce with curl, no debugger needed.
- Multi-day gradual drop → `~/Projects/market-study-knowledge/multi-day-trend-analysis.md`.

---

## Reference Files — Tiered Loading

Load only what each phase needs. Deeper files cost tokens; don't read them speculatively.

**Tier 1 — load immediately at session start (always):**
| File | Purpose |
|------|---------|
| `~/Projects/market-study-knowledge/aliases.json` | Resolve site slug (as24 → autoscout, etc.) — tiny JSON |
| `~/Projects/market-study-knowledge/sites/[slug].md` | Per-site history, quirks, known patterns |
| `~/Projects/market-study-knowledge/sites/_index.md` | Status overview (🟡/🔴/⛔) — read if slug unknown |

**Tier 2 — load only if Tier 1 doesn't resolve the cause:**
| File | How to load |
|------|-------------|
| `~/Projects/market-study-knowledge/failure-patterns.md` | **Grep `**Tags:**` lines only** — identify symptom tags from evidence (e.g. `ms-dl 403 datadome`), grep for matching tags. Never read the full file. Tags: `drop-zero` `drop-sudden` `drop-gradual` `prepared-0` `ms-dl` `duplicate` `credit` `false-alarm` `403` `null-parse` `url-change` `selector` `fake-200` `ssl` `getBrandsAndModels` `svl` `bulk-save` `rmq-stuck` `s3` `es` `datadome` `cloudflare` `scrapedo` `scraperapi` `proxy` `infra` |
| `~/Projects/market-study-knowledge/fix-playbook.md` | Grep the specific section header (S3 delete / DL redeliver / proxy swap) |
| `~/Projects/market-study-knowledge/alert-emails.md` | Grep or read to decode alert subject / false-alarm signals |

**Tier 3 — load only for deep-dive investigations:**
| File | When |
|------|------|
| `~/Projects/market-study-knowledge/graylog-queries.md` | Need specific Graylog query templates |
| `~/Projects/market-study-knowledge/multi-day-trend-analysis.md` | Step 5 shows gradual multi-day drop (anti-bot pressure, not code) |
| `~/Projects/market-study-knowledge/foundational.md` | Architecture question about indexes, queues, deactivation, zombies |

## External Resources

- **Graylog:** `$GRAYLOG_API_URL`
- **scrape.do / ScraperAPI Dashboards** (separate services, separate accounts)
- **AWS S3:** `$AWS_S3_BUCKET_DAILY_CACHE` (`YYYYMMDD/[md5]`)
- **Jira:** `https://preskok.atlassian.net/browse/MAR-XXXX`
- **Bitbucket PRs:** `https://bitbucket.org/b2bcarmarket/market-study/pull-requests`
- **Working URL docs:** `https://preskok.atlassian.net/wiki/spaces/M/pages/3002302476/Working+URL+fix`
- **Useful ES queries:** [Confluence page](https://preskok.atlassian.net/wiki/spaces/M/pages/2677997569/Useful+ElasticSearch+queries) — also check `src/database/elastic-search/elastic-search.service.ts` for existing patterns, or ask the user for their Kibana saved-queries export
- **Slack on-duty:** `#tt-market-study-checklist` (C0859KQ45B2)
- **Slack devops:** `#tt-devops-support` (C01QGRF1803)

## Investigation Context

Facts that only matter during debugging — loaded here so they don't pollute every session.

**Cheerio null behavior** — `$(null)` is safe (returns empty jQuery object). Only `$.load(null)` throws. The Cheerio wrapper patches `$.load` only — it does NOT patch `$()`.

**partialVehicle shared reference in SVL path** — `partialVehicle` in `getFullVehicleFromS3` is the SAME object reference as the `vehicleLink` sent to the detail crawl queue. Deleting fields from it (e.g. `delete partialVehicle.someField`) also mutates what was published to RMQ.

**Spike timing: commit time ≠ deploy/crawl time** — crawls run ~07:00. A fix committed at 15:05 means the morning spike was from the old (broken) code. Any side-effect of the fix appears the next morning, not the same day. Match Graylog timestamps to commit time before concluding the fix caused or didn't cause something.

**Null URL vehicles still indexed daily** — vehicles with `url=null` ARE saved to ES (storeId = md5(null) is stable). A spike in vehicle count after a URL-fix deploy is caused by the fix restoring real URLs, which triggers re-index of previously null-URL records — not a regression.

**Persistent vs transient anomaly** — a single-day volume drop is not evidence of broken code. Persistent bugs cause persistent symptoms across multiple runs. If the next day's count is normal without a fix being deployed, it was a transient site issue (downtime, anti-bot blip, stock fluctuation) — do not ship a fix for it.

---

## Documentation Rules

- **No sensitive literals in saved files** — never write actual bucket names, account IDs, or AWS profile values into reference/site docs. Always use env var placeholders: `$AWS_S3_BUCKET_DAILY_CACHE`, `$AWS_PROFILE`. Correct form: `AWS_PROFILE=preskok-prod aws s3 cp s3://$AWS_S3_BUCKET_DAILY_CACHE/YYYYMMDD/<hash> - | head -c 500`.
- **Credentials belong in `.env`** — if a secret key, token, password, or username was used or discovered during debugging and is NOT already in `.env`, add it there (follow the existing `# local` / `# stage` / `# prod` comment-block pattern). Never leave credentials in reference docs, Graylog query snippets, or curl examples.

## Coding Style Rules

- Follow existing crawler style — no new abstractions.
- Minimal fix: specific `find()` / URL line, don't refactor.
- Follow [Working URL pattern](https://preskok.atlassian.net/wiki/spaces/M/pages/3002302476/Working+URL+fix): override `fetchRequest()` or `beforeParseVehicle()` (HTML only). Keep `legacyUrl` stable for S3 cache.
- Skip-and-log unrecoverable items (`site`, `modelName`, `PARSER_DEBUGGING`) — don't throw.
- Defensive fetch: `const html = await this.fetchRequest(url) ?? '';` prevents `$.load()` on undefined.
- **Don't mask errors with truthy defaults** (Matea's rule). Handle via retry / `isServerError()`.
- **Remove safeguards from `getBrandsAndModels()`** if they prevent auto-rerun (commauto, auto-elite pattern).
- Do not disable crawler unless confirmed — prefer fix.
- Hotfix PRs: target **develop** explicitly.
- URL-encode generated URLs: `#`, `:`, `&`, `(`, `)`, spaces, Cyrillic↔Latin.

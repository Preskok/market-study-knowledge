# crawler-estimate-credit-cost Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the `crawler-estimate-credit-cost` personal skill that estimates minimum ScrapeDo credit cost per day for a Market Study crawler site, by combining Graylog request-volume counts with live ScrapeDo tier tests.

**Architecture:** A single self-contained `SKILL.md` (technique/reference skill, no supporting files needed — all content fits inline per the writing-skills size guidance) at `~/.claude/skills/crawler-estimate-credit-cost/SKILL.md`, following the exact structure and Graylog/ScrapeDo conventions already used by `crawler-test-flow` and `crawler-security`. Built directly from the approved design spec at `docs/superpowers/specs/2026-07-10-crawler-estimate-credit-cost-design.md`.

**Tech Stack:** Markdown skill file, bash (curl against Graylog `views/search/sync` API and `api.scrape.do`), no code changes to the `market-study` app itself.

---

### Task 1: Scaffold skill directory and frontmatter

**Files:**
- Create: `~/.claude/skills/crawler-estimate-credit-cost/SKILL.md`

- [ ] **Step 1: Create the directory and write the frontmatter + overview**

```markdown
---
name: crawler-estimate-credit-cost
description: >
  ALWAYS invoke this skill when the user's message starts with "crawler-estimate-credit-cost"
  followed by a site name — e.g. "crawler-estimate-credit-cost autoplius",
  "crawler-estimate-credit-cost subito". Also triggers on "how much would ScrapeDo cost for
  [site]", "estimate ScrapeDo credits for [site]", "what's the minimum ScrapeDo tier for
  [site]", or any request to estimate/calculate ScrapeDo credit usage for a Market Study
  crawler site, whether it currently uses ScrapeDo or not. Also triggers on
  "/crawler-estimate-credit-cost".
---

# crawler-estimate-credit-cost — ScrapeDo Credit Cost Estimator

Estimates the **minimum** ScrapeDo credits a Market Study crawler site would cost per day, by
counting real request volumes per crawl phase from Graylog and live-testing the cheapest
ScrapeDo tier that actually works for each distinct request pattern. Works for sites already on
ScrapeDo (sanity-check) and sites not yet on it (hypothetical cost).

> ⚠️ This makes **real, credit-spending** calls to `api.scrape.do` using the personal
> `SCRAPING_PROVIDER_API_KEY` from `.env`. Stop-at-first-success is mandatory — never survey all
> four tiers once one already passes.
```

- [ ] **Step 2: Verify the directory and file exist**

Run: `ls -la ~/.claude/skills/crawler-estimate-credit-cost/`
Expected: `SKILL.md` present.

- [ ] **Step 3: Commit is not applicable yet (personal skill dir is outside the git repo)** — skip commit for this task, personal skills at `~/.claude/skills/` are not part of the `market-study` repo.

---

### Task 2: Trigger table and phase-boundary reference

**Files:**
- Modify: `~/.claude/skills/crawler-estimate-credit-cost/SKILL.md`

- [ ] **Step 1: Append trigger + phase model sections**

```markdown
## Trigger

| Command | Meaning |
|---|---|
| `crawler-estimate-credit-cost [site]` | Full estimate: Graylog volumes + live ScrapeDo tier tests + total |

`[site]` resolved via `~/Projects/market-study-knowledge/aliases.json` (same convention as `crawler-info`/`crawler-test-flow`).

## Pipeline (one screen)

```
Phase 0   Resolve site slug + service file path                        (read-only)
Phase 1   Pick a full crawl day from Graylog (prod, fallback stage)     (read-only)
Phase 2   Count requests per phase for that day                        (Graylog)
Phase 3   Enumerate distinct request patterns per phase from the code  (read-only)
Phase 4   Live ScrapeDo tier test per pattern, stop at first success    (spends credits)
Phase 5   Compute credits = tier cost x request count, per phase       (math)
Phase 6   Report
```

## Phase 1 — Pick the day and env

Default env: **prod** (`facility:marketstudy`). Query Graylog for the most recent day with any
log line for the site:

```bash
GL=$(grep ^GRAYLOG_API_URL= .env | cut -d= -f2)
TOK=$(grep ^GRAYLOG_AUTH_TOKEN= .env | cut -d= -f2)
SLUG="[slug]"
curl -s -X POST -u "$TOK:token" \
  -H "Content-Type: application/json" -H "X-Requested-By: curl" \
  "$GL/api/views/search/sync?timeout=30000" -d "{
    \"queries\": [{
      \"id\": \"q1\",
      \"timerange\": {\"type\": \"relative\", \"from\": 604800},
      \"query\": {\"type\": \"elasticsearch\", \"query_string\": \"facility:marketstudy AND site:$SLUG\"},
      \"search_types\": [{\"id\": \"st1\", \"type\": \"messages\", \"limit\": 1, \"offset\": 0, \"sort\": [{\"field\": \"timestamp\", \"order\": \"DESC\"}]}]
    }]
  }" | jq -r '.results.q1.search_types.st1.messages[0].message.timestamp'
```

Take the calendar day (UTC) of that timestamp as the estimate window
(`YYYY-MM-DDT00:00:00.000Z` to `YYYY-MM-DDT23:59:59.999Z`). If no message in the last 7 days on
prod, repeat with `facility:marketstudy-stage` and note in the final report that stage data was
used instead of prod.

## Phase 2 — Count requests per phase boundary

Three phases, each with a start/end log-message boundary (see
`~/Projects/market-study-knowledge/graylog-queries.md` for the auth/query-shape conventions):

| Phase | Start boundary | End boundary | Count query (`message:` OR) |
|---|---|---|---|
| B&M | Day start | First `"Prepared listingUrl messages"` (or `"Problem preparing listingUrl messages for site"` if it failed that day) | `"Finished HTTP request"` OR `"Finished browser request"` |
| Listings | Same `"Prepared listingUrl messages"` line | **Last** `"Finished crawling listing url"` line of the day | `"Starting HTTP request"` OR `"Starting browser request"` |
| Details | Right after the last `"Finished crawling listing url"` | Last log line of the day for the site | `"Finished HTTP request"` OR `"Finished browser request"` |

Find each boundary timestamp with a `messages` search (`limit:1`, sorted ascending/descending as
needed — see Phase 1 query shape). Then count requests in the resulting window with a second
`messages`-type query using `total_results`, not `pivot`:

```bash
curl -s -X POST -u "$TOK:token" \
  -H "Content-Type: application/json" -H "X-Requested-By: curl" \
  "$GL/api/views/search/sync?timeout=30000" -d "{
    \"queries\": [{
      \"id\": \"q1\",
      \"timerange\": {\"type\": \"absolute\", \"from\": \"[WINDOW_START]\", \"to\": \"[WINDOW_END]\"},
      \"query\": {\"type\": \"elasticsearch\", \"query_string\": \"facility:marketstudy AND site:$SLUG AND (message:\\\"Finished HTTP request\\\" OR message:\\\"Finished browser request\\\")\"},
      \"search_types\": [{\"id\": \"st1\", \"type\": \"messages\", \"limit\": 1, \"offset\": 0}]
    }]
  }" | jq -r '.results.q1.search_types.st1.total_results'
```

If a boundary message never occurs that day (e.g. site had 0 vehicles, or the producer failed),
report that phase as `0 requests / N/A` rather than guessing.
```

- [ ] **Step 2: Verify the file renders without broken markdown**

Run: `grep -c '^```' ~/.claude/skills/crawler-estimate-credit-cost/SKILL.md`
Expected: an even number (all code fences closed).

---

### Task 3: Tier-detection section (the live-credit-spending core)

**Files:**
- Modify: `~/.claude/skills/crawler-estimate-credit-cost/SKILL.md`

- [ ] **Step 1: Append the tier-detection section**

```markdown
## Phase 3 — Enumerate distinct request patterns

Read `src/crawler/sites/[Site]/[Site].service.ts` (path resolved the same way as
`crawler-test-flow`: `sed 's/-//g; s/^./\U&/'` on the slug). For each of the three phases, list
every **distinct URL pattern** actually requested:

- `getBrandsAndModels()` — may contain more than one pattern (e.g. autoplius: a one-off
  make-list iframe fetch, AND a per-brand `models?make_id=X` API call issued once per brand).
- The listing-page fetch (usually one pattern, `getVehicleListPageResponse` / pagination via
  `getNextPageUrl`).
- The vehicle-detail fetch (usually one pattern, inside `parseVehicleInput`'s caller).

Test **every** distinct pattern found, even ones called only once — a phase's tier is driven by
its single most expensive pattern, and a one-off request can still be the bottleneck.

## Phase 4 — Live ScrapeDo tier test, stop at first success

**Goal: find the minimum viable tier, not survey all four.** Never call more tiers than needed —
the moment one passes, stop for that pattern.

**Step 4a — pick 3 live sample values per pattern**, pulled from the real site (3 different
brand IDs, 3 different listing pages, 3 different vehicle URLs — not synthetic ones).

**Step 4b — pre-validate each sample with a plain curl (no ScrapeDo, no credits spent):**

```bash
curl -s -o /dev/null -w '%{http_code}\n' "[SAMPLE_URL]"
```

ScrapeDo charges a credit on every response including 404 — swap out any sample that doesn't
resolve to a real 2xx page BEFORE spending a credit on it.

**Step 4c — call ScrapeDo starting at REGULAR, escalating only on failure:**

```bash
TOKEN=$(grep -m1 "^SCRAPING_PROVIDER_API_KEY=" .env | cut -d= -f2-)
# REGULAR (1cr nominal)
curl -s -D /tmp/scrapedo_headers.txt -o /tmp/scrapedo_body.html -w '%{http_code}' \
  "https://api.scrape.do/?url=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "[SAMPLE_URL]")&token=$TOKEN&super=false&render=false"
```

Tier ladder (only call the next one if the current tier fails majority — see Step 4e):

| Tier | Extra params | Nominal cost |
|---|---|---|
| REGULAR | `&super=false&render=false` | 1 credit |
| BROWSER | `&super=false&render=true` | 5 credits |
| SUPER | `&super=true&render=false` | 10 credits |
| SUPER_BROWSER | `&super=true&render=true` | 25 credits |

**Step 4d — classify each response** (per the ScrapeDo integration doc:
https://preskok.atlassian.net/wiki/spaces/M/pages/3977576464/ScrapeDo+documentation):

| Response | Meaning | Action |
|---|---|---|
| **401** | ScrapeDo account has no credits / subscription suspended — NOT a per-site signal | **Abort the entire skill run immediately.** Tell the user tier detection can't continue until the ScrapeDo account has credits. Do not interpret as "this tier failed for this site." |
| **400** | Malformed ScrapeDo request (bad param combo) | Log it, do not retry as-is, do not count as "tier too weak." If it recurs across every tier, the skill's param shape is wrong — fix the URL construction, don't blame the site. |
| **2xx + real content** | Success — verify body is the actual target page, not a Cloudflare/Datadome/GDPR challenge (same heuristics as `crawler-security` Step 9: `CF-Ray` header, `datadome` cookie, consent-wall redirect) | Read `scrape.do-request-cost` from `/tmp/scrapedo_headers.txt` (`grep -i 'scrape.do-request-cost' /tmp/scrapedo_headers.txt`) — this is the ACTUAL charged cost, which can exceed the nominal tier price. Record it for this sample. |
| **404** | Still consumes a credit | If caused by a stale sample missed in Step 4b, swap the sample for the next attempt and note the wasted credit in the final report — but don't count this attempt toward the tier verdict. |
| **403 / timeout / challenge page** | Tier too weak for this pattern | Escalate to the next tier. |

**Step 4e — resolve pattern tier:** cheapest tier where **2 of 3** samples succeeded (majority,
not unanimous — one flaky sample shouldn't force a more expensive verdict, one lucky sample
shouldn't under-call it). Use the **average of the measured `scrape.do-request-cost`** values
from the successful samples as that pattern's per-request credit price — not the nominal tier
constant, since ScrapeDo can silently charge more (this is exactly what
`src/request/scrape-do.service.ts`'s `maxRequestCost` check already guards against in
production).

**Step 4f — resolve phase tier:** the most expensive pattern tier within that phase (a phase
can't run cheaper than its worst request type).
```

- [ ] **Step 2: Verify the file renders without broken markdown**

Run: `grep -c '^```' ~/.claude/skills/crawler-estimate-credit-cost/SKILL.md`
Expected: an even number.

---

### Task 4: Cost math, report format, reference table, common pitfalls

**Files:**
- Modify: `~/.claude/skills/crawler-estimate-credit-cost/SKILL.md`

- [ ] **Step 1: Append the remaining sections**

```markdown
## Phase 5 — Cost math

```
phase_credits = phase_tier_measured_cost x phase_request_count   (from the Graylog day, Phase 2)
total_credits = B&M_credits + Listings_credits + Details_credits
```

## Phase 6 — Report

```
# crawler-estimate-credit-cost — [site]

**Estimate day:** [YYYY-MM-DD] ([prod|stage])   |   **Shape:** [HTML/API]

| Phase | Requests (day) | Tier | Measured cost/req | Phase total |
|---|---|---|---|---|
| B&M | N | REGULAR/BROWSER/SUPER/SUPER_BROWSER | X credits | N*X |
| Listings | N | ... | ... | ... |
| Details | N | ... | ... | ... |
| **Total** | | | | **...** |

## Notes
- Distinct patterns tested per phase: [list, e.g. B&M: make-list iframe (1x/day), models API (1x/brand)]
- Wasted credits during testing (stale samples / 404s): [N, or "none"]
- ScrapeDo credits reset monthly on the 24th — this is a per-day estimate, multiply by expected
  crawl days for a monthly projection.
- [If a 401 aborted the run: "Tier detection incomplete — ScrapeDo account out of credits."]
```

## Quick reference

| Question | Where to look |
|---|---|
| Which day's data was used? | Phase 1 — most recent day with any log line, prod-first |
| Why "Finished ..." for B&M/Details but "Starting ..." for Listings? | Matches the boundary semantics directly: B&M/Details windows are bounded by completion events; the Listings window starts right at "Prepared" so counting starts-in-window is equivalent and simpler |
| Why 3 samples, not 1? | One sample can get a lucky/unlucky anti-bot response; 3 with majority-2 avoids both false-cheap and false-expensive verdicts |
| Why stop at first tier success? | Goal is minimum viable cost, not a full survey — every additional tier tested past the first success spends credits for a number you won't report |
| Why use measured `scrape.do-request-cost`, not the nominal tier price? | ScrapeDo can auto-escalate internally and charge more than requested — same reason `scrape-do.service.ts` tracks `maxRequestCost` in production |

## Common mistakes

| Mistake | Fix |
|---|---|
| Spending a ScrapeDo credit on a dead/stale sample URL | Always plain-curl the sample first (Step 4b) |
| Retrying a 401 response | 401 = account out of credits, not a site issue — abort, don't retry |
| Retrying a 400 response | 400 = malformed ScrapeDo request — fix the URL construction, don't retry as-is |
| Testing all 4 tiers even after REGULAR passes | Stop the moment a tier reaches majority success |
| Using the nominal tier price (1/5/10/25) instead of the measured `scrape.do-request-cost` | ScrapeDo can charge more than the requested tier — always read the response header |
| Using the TT/prod ScrapeDo key | Always read `SCRAPING_PROVIDER_API_KEY` from the uncommented line in `.env` (personal key) |
| Picking the newest day's data without checking it's a full day | If the site's crawl is still in progress, the "last log line" boundary for Details will be wrong — prefer a day that's fully in the past |

## Reference files

| File | Purpose |
|---|---|
| `src/crawler/sites/[Site]/[Site].service.ts` | Request patterns per phase |
| `src/request/scrape-do.service.ts` | ScrapeDo request construction, `maxRequestCost` precedent |
| `src/request/consts/scrapeDoConsts.ts` | Nominal tier credit values |
| `~/Projects/market-study-knowledge/graylog-queries.md` | Auth + facility names + sync-API payload shape |
| `~/Projects/market-study-knowledge/aliases.json` | site name -> canonical slug |
| [ScrapeDo integration doc (Confluence)](https://preskok.atlassian.net/wiki/spaces/M/pages/3977576464/ScrapeDo+documentation) | 401/400/404 credit-consumption behavior, centralized handling, credits-lock mechanism |

## Tone

Evidence-first: every credit figure traces to either a Graylog count or a measured
`scrape.do-request-cost` header, never a guess. Stop escalating tiers the moment one works.
```

- [ ] **Step 2: Verify the file renders without broken markdown**

Run: `grep -c '^```' ~/.claude/skills/crawler-estimate-credit-cost/SKILL.md`
Expected: an even number.

- [ ] **Step 3: Word-count check (technique skill, not a getting-started skill — should stay well under 1500 words per the writing-skills token-efficiency guidance since it's not loaded into every conversation)**

Run: `wc -w ~/.claude/skills/crawler-estimate-credit-cost/SKILL.md`
Expected: some number; no action needed unless it's wildly over ~2000 words (this skill is only loaded on explicit trigger, not every conversation, so the strict <500-word budget for frequently-loaded skills doesn't apply — but trim any redundant prose found during self-review in Task 5).

---

### Task 5: Self-review against the design spec

**Files:**
- Read: `docs/superpowers/specs/2026-07-10-crawler-estimate-credit-cost-design.md`
- Read: `~/.claude/skills/crawler-estimate-credit-cost/SKILL.md`

- [ ] **Step 1: Spec coverage check** — for each section of the design spec (Trigger, Phase model, Data source, Tier detection Steps 1-5, Cost math & report, Out of scope), confirm a corresponding section exists in `SKILL.md`. List any gap found and fix it inline in the skill file before moving on.

- [ ] **Step 2: Placeholder scan** — run `grep -inE "TBD|TODO|tbd|to be determined" ~/.claude/skills/crawler-estimate-credit-cost/SKILL.md`. Expected: no matches. Fix any found.

- [ ] **Step 3: Frontmatter validation** — confirm `name:` uses only letters/numbers/hyphens, `description:` starts with "Use when"/"ALWAYS invoke" and does not summarize the workflow (per the writing-skills CSO rule — the description should state triggers only, which the current draft already does).

---

### Task 6: Live test run against autoplius (GREEN verification)

**Files:**
- None modified — this task exercises the finished skill.

- [ ] **Step 1: Invoke the new skill**

Run the skill: `crawler-estimate-credit-cost autoplius`

Follow the skill's own Phase 0-6 exactly as written. Expected observable outcomes:
- Phase 1 finds a recent day of prod Graylog activity for `site:autoplius` (autoplius crawls
  daily per its knowledge file).
- Phase 3 finds at least 2 distinct B&M patterns (the make-list iframe fetch and the per-brand
  `models?make_id=X` call) — this is the exact case the design spec called out.
- Phase 4 spends a small number of real ScrapeDo credits (expect single-digit REGULAR-tier
  calls if autoplius has no heavy anti-bot on b&m/listing endpoints — confirm against its
  Cloudflare history in `~/Projects/market-study-knowledge/sites/autoplius.md`).
- Phase 6 produces a report with a total credit figure and per-phase breakdown.

- [ ] **Step 2: Compare the run against the skill's own pitfall table** — did any Common Mistake in Task 4's table actually get triggered during the run (e.g. a stale sample, a 400)? If so, that's a real gap in the skill instructions — fix `SKILL.md` (e.g. tighten the sample-selection guidance) rather than treating it as a one-off.

- [ ] **Step 3: Record findings** — note in the chat (not in a new file) what worked, what needed a fix, and the final measured total for autoplius. If Task 5's self-review already caught the issue, no further file change is needed; otherwise fix `SKILL.md` now and re-run Step 1 once to confirm the fix holds.

---

## Notes

- Personal skill — lives at `~/.claude/skills/crawler-estimate-credit-cost/SKILL.md`, **not** inside the `market-study` git repo. No `git commit` step applies to the skill file itself.
- The design spec (`docs/superpowers/specs/2026-07-10-crawler-estimate-credit-cost-design.md`) is inside the repo and was already committed during brainstorming — no further repo changes are expected from this plan.

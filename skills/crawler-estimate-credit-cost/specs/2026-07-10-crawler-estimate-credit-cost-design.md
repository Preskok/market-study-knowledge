# crawler-estimate-credit-cost — Design

## Purpose

A new skill, `crawler-estimate-credit-cost [site]`, that estimates what a site would cost in
ScrapeDo credits per day if it were switched to ScrapeDo (or, for sites already on ScrapeDo,
sanity-checks the current cost). It combines:

1. **Real request volumes** per crawl phase, taken from Graylog history of the site's actual
   crawl activity.
2. **Live-measured ScrapeDo tier** needed per distinct request pattern, from real
   `api.scrape.do` test calls against sample URLs.

The end result is the **minimum credit cost required to crawl the site** — not an exhaustive
tier survey. Output: a credit-cost table per phase and a grand total for one crawl day. No EUR
conversion (ScrapeDo credit pricing/plans change; credits are the stable unit).

## Trigger

`crawler-estimate-credit-cost [site]` / `/crawler-estimate-credit-cost [site]`.
`[site]` resolved via `~/Projects/market-study-knowledge/aliases.json` (same convention as
`crawler-info`, `crawler-test-flow`).

## Phase model

Every crawler run has three phases, bounded by known Graylog log messages (see
`~/Projects/market-study-knowledge/graylog-queries.md`):

| Phase | Start boundary | End boundary | Request count query |
|---|---|---|---|
| **B&M** (brands & models) | First log line of the site for the chosen day | First `"Prepared listingUrl messages"` (or `"Problem preparing listingUrl messages for site"` if the producer failed that day) | Count of `"Finished HTTP request"` OR `"Finished browser request"` in this window |
| **Listings** | Same `"Prepared listingUrl messages"` line | The **last** `"Finished crawling listing url"` line of the day | Count of `"Starting HTTP request"` OR `"Starting browser request"` in this window |
| **Details** | Right after the last `"Finished crawling listing url"` | Last log line of the site for that day | Count of `"Finished HTTP request"` OR `"Finished browser request"` in this window |

Rationale for counting "Finished ..." for B&M/Details but "Starting ..." for Listings: matches
the user-specified counting rule directly (avoids re-deriving it from noisier signals); in
practice the two counts are within 1 of each other per window since almost every started
request finishes.

## Data source: Graylog, prod-first

- Default env: **prod** (`facility:marketstudy` per `graylog-queries.md`). Pick the site's most
  recent full calendar day with crawl activity.
- If prod has no recent activity for the site (disabled, broken, or never launched in prod —
  e.g. a brand-new candidate site), fall back to **stage** and say so explicitly in the report.
- One `POST /api/views/search/sync` query per phase boundary lookup (message search, `limit`
  large enough to find the first/last matching line — not `pivot`, which is unreliable on this
  endpoint per existing convention).
- Note in the report which day's data was used (crawl volume varies day to day).

## Tier detection: live ScrapeDo calls

### Step 1 — enumerate distinct request patterns per phase

Read `[Site].service.ts` (path resolved the same way `crawler-test-flow` does) to find every
**distinct URL pattern** used within each phase — not just "one representative URL". A phase
can have more than one pattern (example: autoplius B&M phase has both a one-off make-list
iframe fetch AND a per-brand `models?make_id=X` API call). Test every distinct pattern found,
even ones called only once — the phase's tier is driven by its most expensive pattern.

### Step 2 — pick 3 live sample URLs per pattern

Pull 3 real, varied sample values (e.g. 3 different brand IDs, 3 different listing pages, 3
different vehicle detail URLs) from the site directly (via a plain, non-ScrapeDo `curl`/existing
S3 cache) — not synthetic URLs.

### Step 3 — pre-validate each sample with a plain curl (no ScrapeDo)

ScrapeDo charges a credit on every response, including 404. Confirm each sample URL resolves
(plain `curl -o /dev/null -w '%{http_code}'`) before spending a ScrapeDo credit on it. If a
sample is dead, swap it for another before testing — never spend a ScrapeDo credit to discover
a stale sample URL.

### Step 4 — escalate tiers cheapest → most expensive per pattern, stop at first success

**Goal: find the minimum viable tier, not survey all four.** For each pattern, call ScrapeDo
starting at REGULAR. The moment a tier passes (majority of samples succeed — see Step 5), **stop
immediately** — do not go on to test more expensive tiers "for completeness." Only escalate to
the next tier when the current one fails to reach majority success. If REGULAR already reaches
majority, BROWSER/SUPER/SUPER_BROWSER are never called for that pattern at all.

| Tier | Params | Nominal cost |
|---|---|---|
| REGULAR | `super=false&render=false` | 1 credit |
| BROWSER | `super=false&render=true` | 5 credits |
| SUPER | `super=true&render=false` | 10 credits |
| SUPER_BROWSER | `super=true&render=true` | 25 credits |

Use `$SCRAPING_PROVIDER_API_KEY` read fresh from `.env` each run (personal key only — never the
commented-out TT/prod key; see `feedback_scrapedo_key` memory). Endpoint and param shape follow
`src/request/scrape-do.service.ts::generateScrapeDoUrl`.

Per response, from the **ScrapeDo integration doc**
(https://preskok.atlassian.net/wiki/spaces/M/pages/3977576464/ScrapeDo+documentation):

- **HTTP 401** → ScrapeDo-specific "no credits / subscription suspended" — **not** a per-site
  signal. Abort the entire skill run immediately, tell the user tier detection can't continue
  until the account has credits. Do not interpret as "this tier failed for this site."
- **HTTP 400** → malformed ScrapeDo request (bad param combination) — log it, do not retry
  as-is, do not count it as "tier too weak"; if it recurs across tiers, flag as a skill bug
  (wrong param shape) rather than a site-cost finding.
- **2xx and body looks like real target content** (not a Cloudflare/Datadome/GDPR challenge
  page — same heuristics as `crawler-security`'s Step 9 provider table) → success. Record the
  **actual charged cost** from the `scrape.do-request-cost` response header, not the nominal
  tier price — ScrapeDo can silently escalate internally and charge more than requested (this is
  exactly what the existing `maxRequestCost` check in `scrape-do.service.ts` guards against).
- **404** → still consumes a credit; if it happens because the sample URL wasn't actually live
  (missed at Step 3), swap the sample and don't count this attempt in the tier verdict — but
  note the wasted credit in the report.
- Anything else (403, timeout, challenge page) → escalate to the next tier.

### Step 5 — resolve pattern tier and phase tier

- Pattern tier = cheapest tier where **2 of 3** samples succeeded (majority, not unanimous —
  avoids one flaky sample forcing an unnecessarily expensive tier verdict, and avoids one lucky
  sample under-calling it).
- Phase tier = the **most expensive** pattern tier within that phase (a phase can't run cheaper
  than its worst request type).
- Use the **measured** `scrape.do-request-cost` (averaged across the successful samples for that
  pattern) as the per-request credit price in the final math, not the nominal tier constant.

## Cost math & report

```
phase_credits = phase_tier_measured_cost × phase_request_count   (from Graylog day)
total_credits = B&M_credits + Listings_credits + Details_credits
```

Report table:

| Phase | Request count (day) | Tier | Measured cost/req | Phase total |
|---|---|---|---|---|
| B&M | ... | ... | ... | ... |
| Listings | ... | ... | ... | ... |
| Details | ... | ... | ... | ... |
| **Total** | | | | **...** |

Also surface, as context (no calculation impact):
- Which day's Graylog data was used, and whether prod or stage.
- Any wasted credits from Step 3/404 misses during testing.
- Note that ScrapeDo credits reset monthly on the 24th (relevant if someone extrapolates this
  daily estimate into a monthly budget).

## Explicitly out of scope

- Centralized ScrapeDo error handling, credits-lock mechanism, transparentResponse mode — these
  are existing architecture decisions (see the linked Confluence doc), not something this skill
  configures or touches.
- EUR cost conversion.
- Actually switching a site onto ScrapeDo (this skill only estimates hypothetical/current cost).

## Test plan

Run `crawler-estimate-credit-cost autoplius` once built. Autoplius is currently NOT on
ScrapeDo (uses browser+proxy), making it a clean hypothetical-cost test case, and its
B&M phase has the two-distinct-pattern shape (iframe + per-brand API) that exercises the
"test every distinct pattern" rule.

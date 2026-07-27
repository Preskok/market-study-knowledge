# autoplius (LT)

## Current status
⚠️ **2026-07-15 PENDING DECISION** — Filip concluded the Cloudflare-bypass research (MAR-2110) with no way found to make requests more successful; team must choose between (a) accepting 60-75% vehicle coverage (25-30k of ~40k) with no extra effort, or (b) routing only requests that retry 3+ times through ScrapeDo, estimated ~185k credits/month. Full writeup in the MAR-2110 Jira board. Decision not yet made as of this sync.

## Test brand+model
- brand: -kita-
- model: -kita-
- verified: 2026-05-09
- notes: First brand alphabetically from autoplius API. Strategy A (break-on-first-push), no brand filter needed. Uses `MS_BROWSER_CRAWLERS_LISTING_URLS_TO_FETCH`. parseDealer confirmed (4 dealers in raw-dealers index).

## History & quirks (newest first where known)
- **2026-07-15** — Concluded the Cloudflare-bypass research: no way found to meaningfully improve on the current 60-75% (25-30k/40k) capture rate. Proposed two options: (1) accept current coverage as-is with no extra effort, or (2) route only requests that retry more than 3 times through ScrapeDo, estimated ~185,000 credits/month (would use otherwise-unused monthly credit allowance). Full research in the [MAR-2110 Jira board](https://preskok.atlassian.net/jira/software/c/projects/MAR/boards/28?assignee=63b53138f3e7004f77fe842b&selectedIssue=MAR-2110). [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784096868690469)
- **2026-07-14 (credit-estimate session)** — Live-tested all 4 crawl-stage request patterns (B&M make-list iframe, per-brand models API, listings, detail page) through ScrapeDo for a hypothetical cost estimate. `render=false` (REGULAR/SUPER, no browser) returned 502 for every single pattern with no exception. `render=true` (BROWSER tier) succeeded immediately on all 4, measured cost 5cr/request. Confirms in code: `fetchRequest()` always routes through `BrowserService.startBrowserAndStaticVisitUrl`, never plain HTTP — this site cannot be crawled at REGULAR/SUPER tier at all, BROWSER (or SUPER_BROWSER) is the floor for any future ScrapeDo migration estimate.
- **2026-07-06** — With the mini test fix (top user agents + 8 retries) in place, success rate hasn't increased, but 40k vehicles were crawled on Sunday (2026-07-05) — first good day in a long time. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1783311314203489)
- **2026-06-22** — Really low numbers for the last 4 days; almost half of vehicles not crawled. Saturday midnight run failed due to strong security; rerun at 6am was successful. Site is dancing on the edge of being auto-locked. MAR-2110 still open. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782105347592299)
- **2026-06-08** — 24k/39k vehicles. Ongoing instability since late May. MAR-2110 still open. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
- **2026-05-29** — Intermittent 403 Cloudflare blocks: 20% fewer vehicles one day (recovered next), then 23% fewer again. 403s not retrying successfully on listings (unusual — retries normally work). Single curl on listings page 5 returned Cloudflare. Autoplius has always had Cloudflare but retries used to handle it. MAR-2110 ticket opened. Monitoring. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1779682055148269)
- **2026-05-09** — Flow test passed: all phases ✅. Strategy A picks `-kita-`/`-kita-` as first brand+model.
- 2025-03 long-term-rental vehicles bug (monthly prices as full price) — some ads are leasing masquerading as buy price.
- Cloudflare wave — 6.5k 403s vs normal <100. Hourly blocking pattern observed Sept 2023 (Cloudflare blocks requests in bursts, not continuously).
- **Year-in-URL duplicates**: URL contains year component (e.g. `volkswagen-caddy-2-0-l-komercinis-2024-dyzelinas-23994129.html`). As year changes, URL changes → DB considers it a new unique vehicle → 40k+ duplicates. Fix: strip year from URL for storage (URL still works without it).
- **Price concat bug (Dec 2023)**: Site added legal tooltip ("payments over 5000 EUR must be by transfer") inside the price HTML element. `normalizeNumericValue()` extracted all digits → prices became e.g. `108005000` instead of `10800`. Started Dec 6, 2023, 60k+ vehicles affected before fix. Fix: narrow the CSS selector to exclude tooltip text nodes. Side effect while the bug was live: for discounted vehicles the inflated price made `discount` compute as a huge negative number (~-1M), which failed new-search-index validation — those vehicles saved to the old index but not the new one until the underlying price bug was fixed.
- **Auction vehicles** removed from counts (Oct 2023 fix). If vehicle count drops ~56% after auction fix, check that non-auction vehicles are still being captured.
- **`-kita-` brand** (Oct 2023): Brand or model field contains `-kita-` meaning "other" in Lithuanian. Decision: save these vehicles, map `-kita-` → `"others"` to match Autoscout's convention (~30k ads on Autoscout with model "others" are saved). 27-reply thread.
- **Multiple dealer locations** (Sept 2023): Same dealer at multiple branches → "Partial dealer does not match with full dealer in S3 mapping" warnings. Dealer location storage for this site may need special handling.
- **"Response rate was limited"** messages: ~6.5k/day in Sept 2023 — site was throttling crawl requests. Monitor ratio of throttled vs successful.
- **Engine data**: Only engine capacity (ccm) + horsepower available, no engine model/version string. These fields should be null, not empty string.
- **Owner**: Owned by Diginet (Lithuania) — same company owns `auto24.ee`.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

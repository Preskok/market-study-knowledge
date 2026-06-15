# autoplius (LT)

## Current status
🔴 **2026-06-08 OPEN** — Ongoing instability: 24k/39k vehicles on 2026-06-08. MAR-2110 open. Intermittent 403 Cloudflare blocks persisting from week of 2026-05-26.

## Test brand+model
- brand: -kita-
- model: -kita-
- verified: 2026-05-09
- notes: First brand alphabetically from autoplius API. Strategy A (break-on-first-push), no brand filter needed. Uses `MS_BROWSER_CRAWLERS_LISTING_URLS_TO_FETCH`. parseDealer confirmed (4 dealers in raw-dealers index).

## History & quirks (newest first where known)
- **2026-06-08** — 24k/39k vehicles. Ongoing instability since late May. MAR-2110 still open. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
- **2026-05-29** — Intermittent 403 Cloudflare blocks: 20% fewer vehicles one day (recovered next), then 23% fewer again. 403s not retrying successfully on listings (unusual — retries normally work). Single curl on listings page 5 returned Cloudflare. Autoplius has always had Cloudflare but retries used to handle it. MAR-2110 ticket opened. Monitoring. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1779682055148269)
- **2026-05-09** — Flow test passed: all phases ✅. Strategy A picks `-kita-`/`-kita-` as first brand+model.
- 2025-03 long-term-rental vehicles bug (monthly prices as full price) — some ads are leasing masquerading as buy price.
- Cloudflare wave — 6.5k 403s vs normal <100. Hourly blocking pattern observed Sept 2023 (Cloudflare blocks requests in bursts, not continuously).
- **Year-in-URL duplicates**: URL contains year component (e.g. `volkswagen-caddy-2-0-l-komercinis-2024-dyzelinas-23994129.html`). As year changes, URL changes → DB considers it a new unique vehicle → 40k+ duplicates. Fix: strip year from URL for storage (URL still works without it).
- **Price concat bug (Dec 2023)**: Site added legal tooltip ("payments over 5000 EUR must be by transfer") inside the price HTML element. `normalizeNumericValue()` extracted all digits → prices became e.g. `108005000` instead of `10800`. Started Dec 6, 2023, 60k+ vehicles affected before fix. Fix: narrow the CSS selector to exclude tooltip text nodes.
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

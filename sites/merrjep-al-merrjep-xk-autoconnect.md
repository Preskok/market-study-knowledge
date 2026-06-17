# merrjep-al / merrjep-xk / autoconnect (AL/XK)

## Current status
✅ **2026-06-12 RESOLVED** — Crawling smoothly for 3+ consecutive days after ScrapeDo 502 episode mid-week. No intervention needed; self-recovered. PRESKOK_SET_2 still blocked — site is crawling via alternative path.

## Test brand+model
- brand: Volkswagen
- model: Golf
- verified: 2026-05-09
- notes: First-alphabetical brand returned 0 listings; must filter to Volkswagen AND Golf explicitly. VPN required (PRESKOK_SET_2 proxy). Equipment N/A (not extracted). parseDealer overridden but VW Golf are private sellers — verify via market-study-raw-dealers index (72 all-time entries confirm parseDealer works). SVL check always fails on first local crawl (LocalStack S3 NoSuchKey). Site key for API trigger is `auto-connect`, NOT the alias `merrjep-al-merrjep-xk-autoconnect`.

## History & quirks (newest first where known)
- **2026-06-12** — Crawling smoothly for 3+ consecutive days with no intervention. Filip had investigated HTML vs API access during the block: models can only be fetched via API (client-side rendered; HTML gives brands but not models), listings can be fetched via HTML browser requests. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
- **2026-06-09** — New ScrapeDo 502 episode: `Problem preparing listingUrl messages for site!`. Looked different from the 526 episode (503 locally still returning 403s). Filip waited one day — self-resolved next crawl. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
- **2026-06-01** — Cloudflare 526 (invalid SSL cert) blocking all requests since ~2026-05-29. 0 vehicles/day on prod. 526 gets cached → retries read old cloudflare response (526 not in isServerError 500-507 range so no automatic retry). ~3000 error emails on Saturday from listing-level failures. PRESKOK_SET_2 (Slo mobile proxies) also blocked. ScrapeDo 10-credit and 25-credit requests failing too. No quick fix found. Gregor asked about mobile proxy subscription issues; defining priority. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780289229371249)
- **2026-04-01** — MAR-2039: workingUrl fix (commit `a50f6d57`) restored `url` (with `?type=car`) in `vehicleListItems.push`, replacing the broken `url: workingUrl` (without `?type=car`) introduced March 24 (commit `dc3ab59c7`). The March 24 deploy caused the April 1st morning spike (6,000+ vehicles re-indexed — bulk saver saw different URL key). The April 1st fix caused a follow-on re-index spike April 2nd–3rd (~3,800 more) as the URL key flipped back. Total: ~9,800 vehicles re-indexed over 3 days. Not a data loss — expected bulk-saver re-index pattern from URL key change.
- **2026-05-09** — Flow test passed (VPN required): getBrandsAndModels ✅, 188+ Volkswagen Golf rows ✅, equipment N/A, parseDealer not triggered for VW Golf (private sellers only; 72 all-time raw-dealers confirms it works). `IsListingValidatedVehicle: false` (first local crawl — LocalStack S3 NoSuchKey error). Strategy A applied with brand+model filter (first-alphabetical brand had 0 listings; first VW model not Golf). API site key = `auto-connect`. PRESKOK_SET_2 proxy; VPN required.
- **auto-connect quirks:** 403 from Cloudflare if multipart boundary missing. 402 not handled by default — must add to `isResponseNotFound()`. Site counter inaccurate. `"Diskutohet"` = "to discuss" in Albanian → treat as null price.
- Site `merrjep-al` has ~666k vehicles due to massive duplicate URLs per vehicle (10+ unique URLs for same car) — Gregor chose `autoconnect.al` instead.
- autoconnect crawler: ~60% success rate with browser requests only, ~67% with ScraperAPI premium — decision to not use premium (not worth 7%).
- "all" model listings (supermodel) must be parsed — some models not mapped to their own listing on site. Expect SVL fails for model changes; mitigated by Uroš confirming supermodels map correctly via DataAPI.
- driveTrain `"Dy goma aktive (2WD)"` (Albanian) → map to FWD.
- ~25% without price → save with `null` price (market representation).

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

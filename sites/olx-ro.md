# olx-ro (RO)

## Current status
✅ **2026-06-19 RESOLVED** — Hotfix deployed: detect "browser outdated" CloudFront response, force newer UA on first HTML request, removed all axios requests (browser-only now). Exceptions reduced by ~50%; `could not complete` errors dropped from 15-30+/day to 2/day. Deactivation lock removed.

## History & quirks (newest first where known)
- **2026-06-19** — Didn't crawl. First request response was cached in S3 from prior crawl - a 200 status "your browser is outdated" page (CloudFront block). Fix (Matea): detect this banner in `isResponseForbidden()`, force newer UA on first HTML request. Also confirmed DataDome is gone - site now uses CloudFront (bot detection = 403, not 302). Also moved to 100% browser requests (axios requests were ALL resulting in 403 - none ever successful, only exposing proxies). Fix validated: exceptions down ~50%, "could not complete" from 15-30+/day → 2/day. Model changes (a4 → a4 limuzina) validated - legit site change. Deactivation lock removed. Note: `$.load(json)` adds circular-dependency props to the JSON causing `JSON.stringify` errors - explicit comment added in code. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1781508175413899)
- **2026-06-16** — Slight drop from ~126k to ~119k. Monitoring for next Thursday's check.
- 403 blocks → 85% browser requests (MAR-1846).
- Covers autovit-ro vehicles too — `previousPrice` field lets us compute discount. `site` field distinguishes olx-ro vs autovit-ro vehicles on olx-ro (URL is always olx-ro).
- Crumbler max 25 pages (~1000 vehicles/listing) — without it big brands (5000+ Golfs) only reached 1000. `currency=EUR` query param filters lei/ron issues.
- `branchName` added to dealer for uniqueness (site+name alone was insufficient).
- `isUsed` parsing removed — site gives missing/false → 4k+ high-mileage "new" vehicles appeared. Now calculated in backend from mileage.
- `engineCapacity > 9000` = commercial vehicle byproduct (filter or accept as known).
- Promoted ads: 12-14 per page, 2078 pages — code handles dedup.
- Shares `MS_LIMITED_CONSUMERS_LISTING_URLS_TO_FETCH` queue with otomoto (CloudFront) and blocket (CloudFront). When otomoto AND olx-ro both get 403 same day, suspect queue-level/proxy-level issue rather than per-site anti-bot change.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

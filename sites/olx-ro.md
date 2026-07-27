# olx-ro (RO)

## Current status
🟡 **2026-07-27 WATCH — investigated, follow-up pending** — Deep dive concluded the site is very likely NOT losing ~20% of vehicles as earlier suspected: the current crawl count (~98k) is back to matching the count from 2 weeks ago, but the site's own summed-per-brand counter has also dropped over the same period (120k → 106k), so the apparent "recovery" is really the two counts converging. Contributing factors confirmed: (1) vehicles without a price are still skipped and unlogged — a manual price-filter test found at least ~1,000 such vehicles (capped by the site's 25-page filtered view, likely more); (2) promoted/duplicate ads share the same URL as their normal counterpart, so they aren't a double-count risk and don't explain the gap. Filip's conclusion: any current under-crawl is a few percent at most, not 20%. Matea asked follow-up questions (exact no-price count, duplicate mechanism) that remained unanswered as of 07-27 — needs follow-up.

## History & quirks (newest first where known)
- **2026-07-27** — Extensive re-investigation (see status above): current ~98k count matches 2 weeks ago; site's own summed counter dropped 120k→106k over the same period; no-price vehicles (skipped, unlogged) estimated at 1,000+ via a manual price-filter test; concluded any real loss is a few % at most, not the originally-suspected 20%. Matea's follow-up questions on the exact no-price count and duplicate mechanism remain open. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1785135066231289)
- **2026-07-22** — Reviewed as part of a deactivation-lock audit: still locked since 07-14, still at ~99k, not yet researched further at that point. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784710418604459)
- **2026-07-23** — Filip: still hasn't managed to check the 07-14 drop. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784789108279789)
- **2026-07-14→2026-07-15** — 20% fewer vehicles both days (grouped report alongside njuskalo/auto-elite/activ-automobiles). Site now hides its vehicle counter, so the drop can't be confirmed directly against the site; summing per-brand counts on 07-15 gave ~119,294 vehicles across 87 brands still present. No follow-up message found confirming recovery — needs human review. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784089890060479)
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

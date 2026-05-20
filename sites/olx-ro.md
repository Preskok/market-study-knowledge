# olx-ro (RO)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
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

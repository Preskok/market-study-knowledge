# autoscout (DE, HUGE — ~2M vehicles)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- GraphQL endpoint moved to `listing-search.api.autoscout24.com/graphql`. Brands from HTML, models from REST `/as24-home/api/taxonomy/cars/makes/{id}/models`.
- 2025-02 listing HTML restructure → mass SVL fail (`name` null for 2M). "Friday troublemaker".
- URL slug duplicates: titles with multiple consecutive `-`.
- CO2 decimal parsing bug.
- Own queue `MS_AUTOSCOUT_LISTING_URLS_TO_FETCH`.
- 2025-01-31 URL format change: Matea prepared a hotfix to crawl NEW listing URL format while preserving LEGACY URL in S3 (matching existing keys) and working URL in ES Data Index. Crumbling also handled. Locked deactivation for autoscout that night (hotfix deployment pattern for mid-day URL changes).
- **Sept 19, 2023 URL path change:** URL path changed from `/angebote/` → `/offers/` (note: also seen as `/angebote/` → `/offer/` in thread). Happened after 5 AM. Since URLs are used as unique identifiers, updating them would create ~2M duplicates and require full reindex over multiple days. Decision: preserve old URL format for S3 key matching (legacyUrl approach), fix workingUrl later. Gregor caught this before the crawler fully broke — an example of URL stability monitoring saving a massive duplicate crisis. Lesson: URL path changes on 2M-vehicle sites must use legacyUrl+workingUrl immediately, not a one-step swap.
- **May 2023 bug:** URL saved to DB included `source=listpage_search-results` parameter (listing search URL instead of vehicle detail URL). Found by filtering on horsepower=0 — a useful diagnostic filter.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

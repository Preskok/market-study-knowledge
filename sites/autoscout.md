# autoscout (DE, HUGE — ~2M vehicles)

## Current status
🟢 **2026-07-31 RESOLVED** — brand dropdown + listing-card selectors fixed after AutoScout24 restructured both independently (MAR-2039). See history entry below.

## History & quirks (newest first where known)
- **2026-07-30→2026-07-31** — AutoScout24 restructured markup in two unrelated places, breaking the crawler completely (0 vehicles/day from 2026-07-30 22:02 UTC): (1) homepage dropped the `<select id="make">` brand dropdown entirely — `getBrandsAndModels()` silently returned 0 brands (no exception, HTML itself was non-empty). Fix: brand id/name pairs now regex-extracted from the `window.__INITIAL_STATE__` JSON script's `otherMakes` array (site's `topMakes` "quick pick" bucket is a duplicated subset — not needed). (2) Listing cards independently renamed/moved several selectors: `rawFuelType`'s testid moved from a `<span>` to a wrapping `<div>` with the text nested deeper; `rawVersion`'s CSS class was renamed (`ListItem_version_` → `ListItemTitle_subtitle__`); `rawTransmission`'s pill is no longer rendered on listing cards **at all** (confirmed 0 occurrences even for vehicles with real transmission data) — only recoverable via the already-parsed listing JSON (`vehicle.transmission`). Also found and fixed 3 more dead-but-masked selectors (`rawPrice` had the wrong tag, `p` instead of `span`; `rawMileage`/`rawDateOfFirstRegistration`'s DOM fallback was unreachable, sitting behind a still-working `data-*` attr). Verified via `crawler-test-flow` incl. a rerun (no SVL fails/duplicates) and a dedicated pagination check (Aixam/Crossline, 76 vehicles / 4 real pages, matched live site exactly).
- GraphQL endpoint moved to `listing-search.api.autoscout24.com/graphql`. Brands from `window.__INITIAL_STATE__` JSON on the homepage (since 2026-07-31, was `<select id="make">` before), models from REST `/as24-home/api/taxonomy/cars/makes/{id}/models`.
- 2025-02 listing HTML restructure → mass SVL fail (`name` null for 2M). "Friday troublemaker".
- URL slug duplicates: titles with multiple consecutive `-`.
- CO2 decimal parsing bug.
- Own queue `MS_AUTOSCOUT_LISTING_URLS_TO_FETCH`.
- 2025-01-31 URL format change: Matea prepared a hotfix to crawl NEW listing URL format while preserving LEGACY URL in S3 (matching existing keys) and working URL in ES Data Index. Crumbling also handled. Locked deactivation for autoscout that night (hotfix deployment pattern for mid-day URL changes).
- **Sept 19, 2023 URL path change:** URL path changed from `/angebote/` → `/offers/` (note: also seen as `/angebote/` → `/offer/` in thread). Happened after 5 AM. Since URLs are used as unique identifiers, updating them would create ~2M duplicates and require full reindex over multiple days. Decision: preserve old URL format for S3 key matching (legacyUrl approach), fix workingUrl later. Gregor caught this before the crawler fully broke — an example of URL stability monitoring saving a massive duplicate crisis. Lesson: URL path changes on 2M-vehicle sites must use legacyUrl+workingUrl immediately, not a one-step swap.
- **May 2023 bug:** URL saved to DB included `source=listpage_search-results` parameter (listing search URL instead of vehicle detail URL). Found by filtering on horsepower=0 — a useful diagnostic filter.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

## Test brand+model
- brand: Aixam
- model: 400
- verified: 2026-07-31

**For `--paginate` specifically:** use Aixam/Crossline instead (76 results / 4 real pages all-countries, verified 2026-07-31) — Aixam/400 is single-page. Do NOT pick a flagship brand+model (e.g. Volkswagen/Golf) for pagination testing — its all-countries count (265k+) triggers the crumbler into 1000+ sub-queries; always verify the real all-countries result count first (see `crawler-test-flow` skill's `--paginate` guidance).

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

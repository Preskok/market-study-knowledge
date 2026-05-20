# otomoto (PL)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- URL: `brand-model-trim-ID.html` → `brand-model-ID.html`.
- `__NEXT_DATA__` truncation.
- Cloudflare escalation — retries to 9, `host` header added.
- Selector: `p:contains()` needs quotes; `.siblings('p')`.
- GraphQL `filters` moved out of `searchTerms`.
- Stale S3 cache crash-loop incident: Sep 2024 — first request succeeded (not forbidden) but subsequent reads from S3 detected as "Response was forbidden". Means forbidden-check must match on the live response, not on the cached copy that was originally not-forbidden. Check `isResponseRateLimited()` carefully — it reads from response body not from HTTP status alone.
- Commercial vehicles URL path also blocks more aggressively — rerun pattern.
- **Sept 10, 2025 URL change:** listing URL format changed (again). Similar to the `brand-model-trim-ID.html` → `brand-model-ID.html` earlier change. Check legacyUrl vs workingUrl handling and apply the standard pattern if URLs don't redirect cleanly.


<!-- merged from second source section -->

- GraphQL endpoints: `https://www.otomoto.pl/graphql` (main) and `https://search-filters-provider.a.otomoto.pl/graphql` (brand/model counts).
- Special brand mapping: Lublin brand listing URL must be `/dostawcze/marka_lublin` (not `/dostawcze/lublin` which returns ALL LCVs).
- `beforeCrawlListingUrl()` method added to abstract class for post-getBrandsAndModels enrichment per listingUrl.
- getBrandsAndModels makes 1000-1700 GraphQL requests — slow and gets blocked on prod. First run: mostly forbidden, only ~320 successful in 1h. Uses S3 caching for subsequent runs.
- CloudFront protection → moved to `MS_LIMITED_CONSUMERS_LISTING_URLS_TO_FETCH` (10 consumers, Sept 2024).
- ~250k vehicles/day expected (actual), ~270k theoretical. LCV ("dostawcze") category slightly under-counted.
- ~1000 duplicates/day: same ad listed in multiple cities with different URLs.
- Description selector changed mid-2024 — description not stored.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

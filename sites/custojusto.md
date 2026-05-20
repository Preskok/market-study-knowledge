# custojusto (PT)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- **Next.js API crawler** (`_next/data/{buildId}/...`). BuildId is a deploy timestamp (e.g. `20240220111101`) — changes on each site deployment, must be extracted from HTML at crawl start.
- Drops correlate with 307 redirects.
- Site redesigned Feb 20, 2024 overnight → listings went from HTML to Next.js API, details also moved to API. Old crawler caused **infinite loop in general queue** (pagination kept looping). Fix: disable crawler immediately when this happens, open ticket for refactor.
- Uses `HtmlAdVehicleCrawlerAbstract` (not `ApiAdVehicleCrawlerAbstract`) even though it uses API — needed for `shouldValidateListingVehicle`. Marko/Gregor rule: always use HTML abstract + SVL for high-volume sites.
- ~35k vehicles (PT). Cloudflare but basic requests work (no browser requests needed).
- **Key pattern**: Next.js `_next/data/{buildId}/...` URL can be grabbed by looking for `__NEXT_DATA__` in the HTML to find the buildId. Pattern reused for flexicar.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

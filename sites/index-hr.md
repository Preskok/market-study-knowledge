# index-hr (HR)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- `ad` → `aditem` URL (real change).
- Dealers API shape change.


<!-- merged from second source section -->

- Cloudflare. Croatian IPs work; other IPs (Italian, Slovenian) get blocked with timeouts.
- Requires `dpc` cookie for API access. Cookie refresh logic stores per-IP in Redis (like Datadome).
- API: `https://www.index.hr/oglasi/api/listings/indexitem?category=car&module=vehicles&includeMakeIds={uuid}&selectedCategory=osobni-automobili&page={n}&sortOption=4&itemPerPage=24`
- Location API (1 call/crawl): `https://www.index.hr/oglasi/api/listings/configuration/datasource/location` — maps city IDs to names for dealer.
- Dealer entity check (1 extra call/dealer): `/api/user/{userId}` → `legalEntity: 1` = private, `2` = business. Skip private sellers.
- Commercial vehicles (`gospodarska-vozila`): no brand/model info → skip them (Gregor decision).
- Vehicle count: had 37k Jan 2024, dropped to 17k by June 2024 (site issue, not crawler).
- Confluence: `/spaces/M/pages/3585998849/Index.hr`

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

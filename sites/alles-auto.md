# alles-auto (DE, buyer-stock)

## Current status
**LEGACY — retired.** Site is down / no longer active.

## History & quirks (newest first where known)
- GraphQL API: `https://www.alles.auto/graphql` (POST). Host header must be `www.alles.auto` (NOT the internal gateway host). Content-length calculated dynamically.
- Also serves bob-automobile: dealers whose name contains "bob automobile" (regex) get `site: "bob-automobile"` assigned on both vehicle and dealer object.
- Vehicle IDs extracted from listing URL (not from `id` field which conflicts with S3 id). Use `beforeParseVehicle()` for per-vehicle API enrichment.
- `vehicleDetail` field in GraphQL listings query always returns null — not usable.
- bodyType: must request all brand/model/bodyType combos (~9 body types). Many return empty but all must be requested.
- BULK_SAVE_DL: same vehicle appears in multiple listings (e.g. Mini Cooper across multiple listings) → duplicate messages → one discarded. Expected, not a bug.
- `foundOn` gets set to GraphQL endpoint URL instead of HTML URL — known, informational only.
- Some URLs lead to 404 detail pages (vehicle exists on listing but ad deleted). Known pattern.
- Confluence page: `/spaces/M/pages/...` (ask Filip/Matea)

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

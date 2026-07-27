# autoscout-ch (CH)

## Current status
✅ **2026-07-02 RESOLVED** — Back to 159k vehicles. ScrapeDo 502 errors self-resolved (or credits replenished). No code change deployed.

## History & quirks (newest first where known)
- **2026-07-21** — Cross-referenced from a `mobile` drift-detection investigation: `autoscout-ch` similarly has a lot of vehicles missing `engineType`, `driveTrain`, `engineCapacity`, `numberSeats`, `numberDoors` (site launched 2025-08-29, so it wasn't covered by the older reference dataset used for drift comparisons). Not confirmed as a crawler bug — just noted as a data-completeness gap worth checking separately. [Slack](https://preskok.slack.com/archives/C04K2LP3AG0/p1784538476356069)
- **2026-06-29→2026-07-02** — All 2,160 listing URLs returned `errorCode: 502` via ScrapeDo (`Service was temporarily unavailable`). Direct curl to autoscout24.ch returned 403. Morning retry (04:00 UTC) also 100% failure. Side-effect: autoscout-ch's 2,160 slow-failing messages (~5 min each) clogged the shared `MS_HUNGARY_LISTING_URLS_TO_FETCH` queue for ~30 hours → promo-neuve ↓86% same day (1,478 vs 11k normal). Filip purged the queue; promo-neuve recovered next day. autoscout-ch self-resolved by 2026-07-02 (159k vehicles). Root cause: autoscout24.ch temporarily blocking ScrapeDo IPs. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782709643021479)
- **2026-05-14** — ScrapeDo returned a Turkish pet-shop JSON response for `mo-s3/mk-audi?pagination[page]=10` (different URL, same cross-user contamination pattern as the Spanish billing API below). "Empty sub-selector" thrown by cheerio (body starts with `{`, treated as CSS selector). Recurring from week to week per Filip. Monitoring. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1778485086288569)
- **2026-05-14** — scrape.do returned a Spanish billing API JSON response (`{"success":true,"title_response":"consulta de factura"...}`) for `mo-a-200/mk-mercedes-benz?pagination[page]=4`. Body started with `{` → `$(html).find(...)` threw `Error: Empty sub-selector` (cheerio treated non-`<` body as CSS selector). Single RMQ message affected; rest of crawl continued. S3 key poisoned: `20260515/8cd9da929f09516ecc4651c3d4e412fa` (note next-day date — CEST timezone). Fix: delete S3 key; code fix pending to detect non-HTML 200 responses.
- Scrape.do. Details persistently blocked — `skipDetailsUrlValidation: true`.
- JSON script format variants.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

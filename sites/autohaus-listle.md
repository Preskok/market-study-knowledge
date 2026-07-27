# autohaus-listle

## Current status
✅ **2026-07-03 FIXED** — WPCarSync redesigned its pagination widget; `getNextPageUrl()` selectors were stale, silently capping every brand/model at its first 20 vehicles. Fixed in `bugfix/MAR-2039-autohaus-listle-pagination-selector-change` (commit `f4062287`). Local test: 210 → 353 vehicles.

## History & quirks (newest first where known)
- **2026-07-06** — Confirmed in prod: the pagination fix (`bugfix/MAR-2039-autohaus-listle-pagination-selector-change`) works. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1783311314203489)
- **2026-07-01→2026-07-03** — Persistent undercounting (210 vs 300+ visible live), 2 days straight, zero errors in Graylog (`getBrandsAndModels` healthy, 36 listing messages prepared both days — matches live brand/model API enumeration exactly). Root cause: WPCarSync changed its pagination markup from `.dxim_pagination a.page-numbers.next` / `.page-numbers:not(.next)` to `<nav class="wpcs-pagination">` with `.wpcs-pagination__btn` / `.wpcs-pagination__arrow` classes and a `data-wpcsp` attribute carrying the target page number directly (the "next" arrow gets `class="...disabled"` and drops `data-wpcsp` on the last page — that's the authoritative "no more pages" signal, more reliable than the old `currentPage + 1` + separate last-page cross-check). Old selectors matched nothing → `getNextPageUrl()` always returned `undefined` after page 1, so any brand/model with >20 vehicles (e.g. Hyundai Tucson, 4 pages / ~80 vehicles) silently lost everything past page 1. Fix: read `data-wpcsp` off `nav.wpcs-pagination a.wpcs-pagination__arrow[aria-label="Gehe zur nächsten Seite"]:not(.disabled)`. Confirmed via direct `curl` to the live `wp-admin/admin-ajax.php` API (brand/model enumeration) and live listing page fetches (pagination markup) — no browser/proxy needed, this crawler is plain HTTP. Local full-crawl test after the fix: 353 vehicles (Hyundai alone contributed 282, matching the Tucson multi-page theory).
- **2026-06-10** — Site listings working again; deactivation lock deleted by Filip. Root cause unclear (no getBrandsAndModels emails fired - failure was on listings phase, not B&M). [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
- **2026-06-07/08** — 100% vehicles would get deactivated (threshold 50%). Vehicles locked from deactivation. Issue is on listings phase (no emails/reruns fired — failure after `getBrandsAndModels()`). Site appears to not have working listings again. Filip monitoring in the following days. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
- **~2026-05-28** — Weekly thread reports "autohaus-listle is back, their site works normally 🎉" after the WPCarSync issue below. Exact date uncertain (within week 25–29 May). [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1779682055148269) **Needs human review** — confirm vehicle count on site matches crawled vehicles.
- **2026-05-27** — 0 vehicles. `article.vehicle-on-archive` selector dead. Site migrated to WPCarSync v3.6.2: inventory is now JS-rendered. `wpcs_fetchResults` AJAX POST to `/wp-admin/admin-ajax.php` returns JSON `{vehicle_list_html, count, pagination, active_filters}` but `vehicle_list_html` contains only template placeholders (`[WPCS_get make]`, `[WPCS_archive_price]` etc.) — DMS sync broken on their side. `count: 251` (vehicles in DB), `max_pages: 13`, `posts_per_page: 20`. No vehicle sitemap exposed. Visiting listing pages in browser also shows no vehicles — site is broken independently of our crawler. Wait for them to fix WPCarSync sync before attempting any code change.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

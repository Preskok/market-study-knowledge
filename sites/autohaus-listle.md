# autohaus-listle

## Current status
🔴 **2026-05-27 BROKEN** — Site reskinned to WPCarSync v3.6.2 JS-rendered inventory. Crawler gets 0 vehicles. DMS sync is failing on their side — not fixable from our crawler. Recommend `isDisabled: true` until they fix it.

## History & quirks (newest first where known)
- **2026-05-27** — 0 vehicles. `article.vehicle-on-archive` selector dead. Site migrated to WPCarSync v3.6.2: inventory is now JS-rendered. `wpcs_fetchResults` AJAX POST to `/wp-admin/admin-ajax.php` returns JSON `{vehicle_list_html, count, pagination, active_filters}` but `vehicle_list_html` contains only template placeholders (`[WPCS_get make]`, `[WPCS_archive_price]` etc.) — DMS sync broken on their side. `count: 251` (vehicles in DB), `max_pages: 13`, `posts_per_page: 20`. No vehicle sitemap exposed. Visiting listing pages in browser also shows no vehicles — site is broken independently of our crawler. Wait for them to fix WPCarSync sync before attempting any code change.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

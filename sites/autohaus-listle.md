# autohaus-listle

## Current status
🔴 **2026-06-08 OPEN** — No working listings again since ~2026-06-07. 100% deactivation threshold triggered; vehicles locked from deactivation. Not a `getBrandsAndModels()` issue (no emails/reruns fired) — failure is on listings phase. Ticket not yet opened; on backlog.

## History & quirks (newest first where known)
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

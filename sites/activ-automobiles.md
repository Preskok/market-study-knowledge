# activ-automobiles

## Current status
🟡 **2026-05-27 WATCH** — 0 vehicles due to ECONNRESET proxy failure during 6 AM rerun. Code confirmed healthy. Site architecture dependent on proxy + Redis cookie.

## History & quirks (newest first where known)
- **2026-05-27** — 0 vehicles. ECONNRESET proxy failure during 6 AM rerun. `visitBrandsListMainPage()` uses `useProxy: true` — if proxy is unreachable at crawl time, cookie is never fetched/stored in Redis (`CacheKeysEnum.ACTIV_AUTOMOBILES`). All subsequent AJAX listing calls (`/xhr_ws.php?xhr_func=svositec_aj002` POST with form data) return empty → "Listing url is empty". Code confirmed healthy: direct curl with valid cookie returns 20 vehicles from AJAX endpoint. Manual trigger should recover.
- **2026-05-20** — Numbers increased 2.6k→2.9k. Site momentarily unreachable for verification, then confirmed 3000 vehicles — increase is legitimate ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1779107075945509)
- Generic/duplicate listings inflating stock.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

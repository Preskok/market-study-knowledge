# oxylio (FR, small)

## Current status
🟢 **2026-07-08 FIX PUSHED** — branch `bugfix/MAR-2039-oxylio-www-migration`. Site migrated `oxylio.com` → `www.oxylio.com`; API POST calls were silently returning 0 vehicles due to 301 redirect + POST→GET conversion. Fix: `CrawlingSites.ts` url updated to `www.oxylio.com`; `buildLegacyUrl()` hardcodes the old domain so storeId = md5(`oxylio.com/achat/vehicule/vehicle-id-{id}`) stays stable.

## History & quirks (newest first where known)
- **2026-07-24** — New-URLs-detection signal fired (6 new URLs); confirmed all good — stock simply increased from 34 to 40. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784877712361629)
- **2026-07-14** — 6AM rerun successful, confirming the site remains healthy since the 07-08 `www.oxylio.com` migration fix. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784002411096819)
- **2026-07-08** — `oxylio.com` domain 301-redirected to `www.oxylio.com`. `/api/search` metadata was S3-cached (no error), but per-page POST to `/api/search/vehicles` followed 301 and converted to GET, returning HTML instead of JSON → `responseData?.vehicles ?? []` silently returned empty → 0 listing URLs since Jul 7 22:02 (4 consecutive runs). Fix: baseUrl changed to www; legacy URL hardcoded in `buildLegacyUrl()`. API returns 31 vehicles (26-27/day after price/type filters). Normal count: 26-27.
- URL restructured, encoded titles (`%2520`).

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

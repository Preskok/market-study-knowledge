# njuskalo (HR)

## Current status
✅ **2026-06-05 RESOLVED** — Mileage SVL fix deployed and rerun successful; 52k unique vehicles before 2AM. Also: Imperva bot detection (302 redirect to `validate.perfdrive.com`) hit at midnight 2026-06-04, but auto-retry handled it.

## Test brand+model
- brand: Abarth
- model: 500
- verified: 2026-05-09
- notes: Strategy A (break-on-first-push) works in ~60s and reliably yields rows. Site lists brands alphabetically; first-brand-first-model gives Abarth/500 with ~14 vehicles. Equipment field fully populated (Croatian terms). DealerId absent on Abarth sample (likely all private sellers — retest with a larger brand if dealer parsing needs verification). Strategy B would walk all brands first — slow on this site.

## History & quirks (newest first where known)
- **2026-06-08/12** — 302 Imperva captcha again at midnight; rerun at 6am successful. Crawler completing very early (6-8AM) in the last 5 days - suggests faster run or early exit without error. Filip checked: no sign of a property change like the June 3 mileage case. Monitoring. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
- **2026-06-04** — Imperva bot detection at midnight: 302 redirect to `validate.perfdrive.com` (status treated as rate-limit). Auto-retry succeeded; no action needed. Also `eurostocks` discussion was mis-posted in this thread (see eurostocks.md).
- **2026-06-03** — Almost all vehicles failing SVL due to `mileage=0` on listings. Root cause: site added thousands separator (dot) to mileage (e.g. `"1.234 km"`) — regex failed for mileage > 1000km. Fix deployed by Matea. Queue (13k messages) purged and crawler rerun to avoid rate-limit exposure. Second crawl finished in ~30min with 52k unique vehicles ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780493647767079)
- **2026-05-09** — Flow test passed (VPN required): getBrandsAndModels ✅, 70 Abarth 500 vehicles ✅, 1 dealer ✅ ("AUTO SALON DENI"). `IsListingValidatedVehicle: true` (S3 cache, no detail fetch). Equipment 3/70 (expected low — private sellers). Without VPN: ShieldSquare blocks all HTTP+browser, never completes.
- **ShieldSquare** anti-bot (also branded as "DataDome for SEE"). Hardcoded brands list as fallback when ShieldSquare blocks brand/model API. Fallback triggers if API returns 0 brands — uses static list in code. Check brands list stays up to date when ShieldSquare starts blocking.
- **URL reuse**: Site reuses expired ad URLs for new vehicles of different brand. A VW may appear on a URL that previously had an Opel. Can cause brand mismatch in ES if vehicle is matched by storeId to old URL. Awareness only — not fixable at crawler level.
- 503 floods during maintenance.
- Partial model list → backup brand list fallback.
- Two URL paths: `/` and `/novi-auti/`.
- Highest proxy-end errors.
- 302/500 oscillation, no stable follow-redirect config.
- Private/dealer parser bug (MAR-1793), CO2 decimal.
- retryNr-not-reset → whole-brand loss.
- Covers HR market for us — `auti-hr` is not needed (product decision).

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

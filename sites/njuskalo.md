# njuskalo (HR)

## Current status
🟡 **2026-07-27 WATCH — intermittent instability continuing** — The every-other-day pattern persists: some days come in ~10%+ under (e.g. 42k vs 50k), self-recovering the next day via automatic rerun (confirmed 07-22 and 07-27). Not yet root-caused; consistent with the 302-until-7AM pattern noted 07-17.

✅ **2026-07-17 RESOLVED (past incident)** — Recovered from the 07-14→07-15 12%-down dip (back to normal by 07-16). Separately, midnight crawl got 302-redirected on `njuskalo.hr/auti` until a 7AM rerun succeeded on 07-17 — Matea flagged this 302 as likely a captcha-triggered block, not a plain rate-limit. Watch if the 302-until-7AM pattern recurs.

## Test brand+model
- brand: Abarth
- model: 500
- verified: 2026-05-09
- notes: Strategy A (break-on-first-push) works in ~60s and reliably yields rows. Site lists brands alphabetically; first-brand-first-model gives Abarth/500 with ~14 vehicles. Equipment field fully populated (Croatian terms). DealerId absent on Abarth sample (likely all private sellers — retest with a larger brand if dealer parsing needs verification). Strategy B would walk all brands first — slow on this site.

## History & quirks (newest first where known)
- **2026-07-27** — 42k vehicles yesterday, back to 50k today (self-recovered). [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1785131713654149)
- **2026-07-22** — Automatic rerun at 06:00 succeeded, got all vehicles. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784703042404639)
- **2026-07-21** — Noted as unstable for at least the last week: every other day ~10% fewer vehicles, alternating with full days. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784632831309249)
- **2026-07-17** — Re-run at 7AM succeeded; midnight run had been getting 302 redirects on `njuskalo.hr/auti` until then. Matea: the 302 is likely a captcha-triggered redirect rather than a plain rate-limit block — worth checking if it recurs on future midnight runs. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784271235584359)
- **2026-07-16** — Back to normal vehicle numbers. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784178894689599)
- **2026-07-14→2026-07-15** — 12% down both days (grouped report alongside olx-ro/auto-elite/activ-automobiles); not individually investigated since these short dips usually self-recover by the next day. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784009316986679)
- **2026-06-30** — 46400 vehicles vs. 44400 the day before, still below the ~50k baseline. More "forbidden" and "could not complete" responses observed on detail-page fetches for not-so-small listings. Worth tracking in following days. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782709643021479)
- **2026-06-29** — 10% fewer vehicles than the day before (49450 → 44379). Will check numbers the following day. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782709643021479)
- **2026-06-26** — Reruns at 6am on Thursday and Friday were both successful. Pattern emerging: midnight crawl may be regularly blocked, with 6am rerun succeeding. Filip tracking next week to see if this becomes consistent. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782105347592299)
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

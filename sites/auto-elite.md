# auto-elite (IT)

## Current status
🔴 **2026-07-27 OPEN** — Recurring weekly drop continues (usual ~4.4k vehicles down to ~1.6-1.75k); now partially root-caused to `ERR_CANCELED` responses (5x) from `elite-auto.fr/api/search`. Ticket [MAR-2135](https://preskok.atlassian.net/browse/MAR-2135) tracks it; considering an alternate data source but avoiding a full crawler refactor for now. Separately flagged: as a buyer-stock/CIS (Club Solution SAS) site, these recurring drops have been inflating "fake" stock in the widget and losing DOFR/numberSeats/equipment/emissions data on affected days since at least 2026-04-29 (~3 months) — not yet separately fixed, deprioritized behind MAR-2057. Deactivation-locked since 07-18 due to the drops.

## History & quirks (newest first where known)
- **2026-07-27** — 6AM rerun succeeded (1.65k vehicles, still down from the usual 4.4k). Root cause partially identified: `ERR_CANCELED` response (5x) from `elite-auto.fr/api/search`. Filip will look at alternate data sources given the API's instability, but won't force a full refactor. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1785129859949079)
- **2026-07-24** — Automatic rerun succeeded but again returned only ~1,590 vehicles (same recurring drop, ticket already open). [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784877832858019)
- **2026-07-23** — Ticket MAR-2135 confirmed opened for the recurring drop + property-loss issue, but Matea reprioritized it behind [MAR-2057](https://preskok.atlassian.net/browse/MAR-2057) (higher value/priority) given Filip's upcoming vacation. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784789108279789) / [reprioritization](https://preskok.slack.com/archives/C0859KQ45B2/p1784789479833379)
- **2026-07-22** — Automatic rerun at 06:00 succeeded but only returned 1,749 vehicles (same recurring pattern). [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784703079622679)
- **2026-07-22** — Reviewing deactivation-locked sites: `auto-elite` locked since 07-18 due to the recurring drops. Flagged as causing "fake" stock inflation in the CIS/buyer-stock widget (Club Solution SAS) — first reported 2026-04-29 — and losing DOFR, numberSeats, equipment, and emissions data on affected days. Been happening for ~3 months at this point; needs a proper ticket given it's buyer stock. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784710418604459)
- **2026-07-21** — Drop recurred today and on Saturday (07-18): usual ~4.4k vehicles, got only ~1.6k both days. Ticket opened same day to investigate why this keeps recurring weekly instead of just being kicked down the road. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784632950056339) / [ticket note](https://preskok.slack.com/archives/C0859KQ45B2/p1784634664237989)
- **2026-07-15** — Recovered from the 07-14 dip same day. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784089890060479)
- **2026-07-14** — 82% down (grouped report alongside njuskalo/olx-ro/activ-automobiles); not individually investigated since these short dips usually self-recover. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784009316986679)
- **2026-07-03** — 4592 vehicles vs previous day's 3482 (up from the low end of the 06-29 dip); unlocked from deactivation prevention same day. Filip will track stability into the following week. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782709643021479)
- **2026-07-01** — 4446 vehicles crawled vs 4249 shown on site. Matea: if the crawled count stays static while site count keeps moving, or if drops recur, worth checking whether the internal API endpoint we call still reflects true live stock vs. the site's own Algolia-backed search (browser network tab now shows an Algolia query where the previous ES-style API call used to be) — flagged as an open question, not yet investigated. Also noted: a hardcoded Algolia app id/key can remain valid for very long periods, useful if we ever need to switch endpoints and they aren't exposed in page HTML. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782709643021479)
- **2026-06-30** — 3rd consecutive day at ~1755/4455 vehicles (39%). Matea tested locally: `getBrandsAndModels()` returned 4446 total while the live site showed only 3483 — raised the Algolia-vs-internal-API discrepancy (see 07-01 entry) as a possible root cause, not yet confirmed. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782709643021479)
- **2026-06-29** — Rerun at 6am successful but only ~1500 vehicles (a third of normal ~4500). Deactivation locked by system. Filip will wait a few days since the site's ES query response has been unstable before and can self-recover. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782709643021479)
- **2026-06-23→2026-06-24** — 62% drop: only 1665 listing URLs prepared instead of regular 4385. Midnight run failed; multiple reruns gave same 1665 result. Suspected cause: stale S3 responses (API crawler loops all vehicles together - can't delete individual keys). Waited for next day. 2026-06-24: back to ~4500 vehicles, deactivation lock deleted ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782105347592299)
- **2026-05-20→2026-05-22** — 77% volume drop (1k vs 4.3k normal). Many 500 errors overnight. Back to normal 4277 vehicles 2 days later ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1779107075945509)
- **2026-04-28→2026-04-29** — `etape1` API endpoint (`/api/devis/etape1/<id>`) intermittently 500 → losing `numberSeats` and `equipment` data. `recap` endpoint also sometimes 500 → losing `dofr` and `emissions`. `etape3` and `navbar` endpoints fine. Only 3987 vehicles instead of 4200 (site query difference, not due to "destockage"). Recovered fully next day: 4200 vehicles, query back to normal ✅. 500s appeared to be transient server-side issues. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1777349596109229)
- **2026-04-24→2026-04-25** — 15% volume drop one day, recovered to usual numbers next day ✅. Discrepancy remains: site shows 4.2k vehicles, crawler got 3.5k (~17% gap). Matea flagged for follow-up next week. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1777349596109229)
- Stock fluctuations. `used` query returns `new`.
- 503 on large listings.
- `UNABLE_TO_VERIFY_LEAF_SIGNATURE`.
- Safeguards removed from `getBrandsAndModels()` to allow auto-rerun.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

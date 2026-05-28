# leboncoin (FR, HUGE)

## Current status
🟡 **2026-05-15 WATCH** — Volume recovered to 757k after dip to ~680k (2026-05-12). 2 ongoing MS_DL messages with ScrapeDo wrong-response (ARO_Forester + INNOCENTI_Turbo → Amazon.com). Monitoring.

## History & quirks (newest first where known)
- **2026-05-11→2026-05-15** — Volume drop: 760k (pre-May 3) → 680k (May 12) → 706k (May 14) → recovered to 757k (May 15). Root cause: Renault Clio listing URL failed (broken script parsing) → ~35k missing vehicles. 2 MS_DL messages with ScrapeDo cross-user contamination (ARO_Forester + INNOCENTI_Turbo URLs leading to Amazon.com pages). [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1778485086288569)
- **2026-05-04** — 5 MS_DL messages from Apr 27 and Apr 30; Matea confirmed those listings are now working. Queue purged ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1777879864126089)
- **2026-04-24** — ~60k duplicates in one day's crawl. Unique vehicle count OK at 740k; total crawled 797k. Duplicates are a known artefact of the crawl strategy — unique count is the real metric to watch. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1777349596109229)
- Only `ultra_premium` (30-credit) ScraperAPI works.
- 1-credit <50%, retry#4 ultra_premium sometimes still 400.
- Deactivated multiple times (credit burn).
- Big deactivation nights: 2M+ vehicles.
- `retry_404` ScraperAPI option (added Jul 2025) — recovers dead 404s at no extra credit cost. Keep enabled.
- `rawIsDamaged` log removed — leave only errMessage log with new value when array of possible values is incomplete.
- Request latency spikes (>15s avg) when ScraperAPI has backend issues — pattern usually clears at ~12:30 the same day (observed repeatedly). If day stays bad through 13:00, disable for the day.
- Return-from-pause pattern (e.g. 2025-07-29): one good day (~750k vehicles) followed by renewed blocks → wait a full week before declaring "fixed".
- 2025-01-08: site went from Datadome to Datadome+Akamai → 1-credit requests all failed, ultra_premium needed. Cost jumped $150 → $660-750/month for 7.5M credits. After a few days the protection eased, then recurring weekly pattern.
- `x-consumer-timeout` raised 30min → 2h on `MS_LEBONCOIN_LISTING_URLS_TO_FETCH` (one listing could consume 1000 ScraperAPI credits via retries). Changing x-consumer-timeout requires queue delete + recreate (Stas shovels messages to tmp queue, adds config, shovels back). See fix-playbook.
- Dealers: 17k pro dealers (2 types — one exposes siteUrl in listings, one does not); dealer name always available. Crawler visits only listings (skipDetails implementation — see "Skip Visiting Listing Details" confluence doc).

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

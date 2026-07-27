# leboncoin (FR, HUGE)

## Current status
🟡 **2026-07-23 WATCH** — Volume still below normal (715k vs the usual 730k+; had dropped to 665k on 07-20). No errors found in the crawl; root cause of the drop not pinned down — two site-side quirks were spotted along the way (promoted "in the spotlight" ads duplicated across every listing page but counted in the site's own totals; a large-listing crumbling undercount on Renault Clio, 35,870 stated vs 28,026 summed) but neither was confirmed as the cause of this specific dip. Not alarming; monitoring continues. Unrelated to the 2026-06-01 SVL fix below, which remains resolved.

## History & quirks (newest first where known)
- **2026-07-23** — Crawled 715k vehicles, better than the 660k of the previous crawl but still below the ~730k baseline. Not alarming; root cause still not pinned down (partly because pre-07-20 PROD logs were lost in the Graylog outage, so no clean before/after comparison was possible). Monitoring continues. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784804623093019)
- **2026-07-21→2026-07-23** — Investigated ~20 vehicles with `dateOfFirstRegistration` before 1900 (out of ~5.4k across the whole ES index with DOFR < 1900, ~90% of which are on leboncoin). Confirmed the dates are genuinely what's stated as DOFR on the ad — not a parsing bug. Decided against adding extra DOFR validation on top of what already exists: DataAPI preprocessing already filters saved DOFRs to the range `(1970, current_year + 1)`, which both Matea and Uroš agreed is a sensible cutoff (anything before 1970 is unreliable anyway). [Slack](https://preskok.slack.com/archives/C04K2LP3AG0/p1784621579814809)
- **2026-07-20** — Crawled 665k vehicles vs the usual 730k+. No errors found, and logs confirm every listing's pages (including next-page) were visited. Investigation turned up: (1) the site's own "in the spotlight" promoted ads duplicate across every page of a large listing (~2/page) yet ARE counted in the site's displayed total — confirmed via an Opel Crossland example (734 stated vs 692 unique across 21 pages) — a general source of site-vs-crawl mismatch, not confirmed as this drop's cause; (2) crumbling a large Renault Clio listing: site states 35,870 vehicles, but the crumbled pages summed only to 28,026 — flagged as worth checking whether crumbling of very large listings works correctly, not yet confirmed; (3) ES Old index showed ~87k fewer Peugeot vehicles vs the previous crawl (134k → 87k) against ~105k currently stated on site — also unexplained. Couldn't compare against pre-outage logs since all PROD logs before this date were lost in the LJ server/Graylog outage. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784545512680039)
- **2026-06-01** — vehicleListUrl validated for all active vehicles in ES Data index ✅. SVL re-enabled and deployed to prod before Monday crawl. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780300843376719)
- **2026-05-29** — SVL disabled on leboncoin (reason not stated in Slack). Reminder scheduled for 10AM 2026-06-01: validate vehicleListUrl in Data index, re-enable SVL on crawler, deploy to prod before Monday crawl. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780060974387359)
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

# autobazar (SK)

## Current status
✅ **2026-06-15 RESOLVED** — Fix deployed (MAR-2101). Matea confirmed fix working in week-15 thread. `getBrandsAndModels()` now uses advanced search page per brand numeric ID — stable listing URL count.

## History & quirks (newest first where known)
- **2026-07-15** — Almost all brands/models were showing as "Ferrari" the day before (2026-07-14) and were back to correct values by 07-15 (validation logs: MODEL 100%, BRAND 100% match after the correction). Called a transient error on the site's own side, self-fixed — not a crawler bug. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784097942820949)
- **2026-06-24→2026-06-26** — Transient data null issue: validation progressive logs showed 3.5k vehicles changed from `value` to `null` on 2026-06-24, then 3.3k changed back from `null` to `value` on 2026-06-25. By 2026-06-26 Filip confirmed all 10 checked vehicles had correct values matching the Monday state. Self-resolved. Matea noted to monitor if it recurs. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782105347592299)
- **2026-06-15** — Fix deployed and confirmed working by Filip. Matea also confirmed in week-15 thread ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1781508175413899)
- **2026-06-15** — Fix implemented for MAR-2101. Root cause: per-brand subdomain (`audi.autobazar.sk`) returns random/incomplete model list each SSR response; S3 cache persists this for the whole day. Fix: get brand numeric ID from homepage `#brand option[value]`, fetch `/rozsirene-vyhladavanie/osobne-auta/?p[categories][0][]=1&p[categories][1][][]={id}`, select `option[data-brand-id="{id}"]` — SSR always includes all models. Produces stable ~1200 listing URLs.
- **2026-06-12** — 35k/50k vehicles. Root cause identified: `getBrandsAndModels()` prepares inconsistent listing URL count each run (1185, 1206, 1225 in 3 runs minutes apart). Some brands (e.g. Audi) entirely absent from a given day's B&M response even though locally they appear. Investigating `autobazar.sk/rozsirene-vyhladavanie/` (advanced search) as more stable source. MAR-2101 ticket open. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
- **2026-05-25** — 19% fewer vehicles on Saturday 2026-05-17, stable at 52k for last 2 days. MAR-2101 open for instability investigation. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1779682055148269)
- **2026-05-11** — Back to usual numbers after prior dip ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1778485086288569)
- **2026-04-21→2026-04-25** — Volume dropped, recovered to 54k on Tuesday 2026-04-22, then slowly dropped again to ~46k by end of week. MAR-2101 opened for chronic instability investigation. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1777349596109229)
- 20-40% fluctuation self-recovers.
- `hongqi-ehs9`/`leapmotor` subdomains returned ALL ads → wrong brand.
- davo-car-s-r-o dealer: CZK-as-EUR bug.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

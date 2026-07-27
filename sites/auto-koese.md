# auto-koese (NL)

## Current status
✅ **2026-07-21 CONFIRMED OK** — Slight drop noted (ongoing ~4 days) but the number matches what's currently shown on site — legitimate stock change, not a bug. The 07-07 domain-404 outage below has since cleared.

## History & quirks (newest first where known)
- **2026-07-21** — Slight drop in numbers over the last 4 days; confirmed to match the number currently on the site — no action needed. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784633146606349)
- **2026-07-07** — Entire domain (`www.auto-koese.nl/`, `/voorraad`, all paths) returning HTTP 404. Graylog: `Page not found` at `url: https://www.auto-koese.nl/voorraad` at 04:00 and again at 22:02 on Jul 6. No code change needed — cartel.nl API (`prod.caw5.cartel.nl`) returns 200 OK. 2nd occurrence; same pattern as Jun 29. Expected recovery by Jul 8.
- **2026-06-29** — Same pattern: domain-wide 404. Recovered by Jun 30 (147 vehicles). No intervention needed.

## Architecture
- `getBrandsAndModels()` fetches `${baseUrl}/voorraad` to scrape brand/model filter elements (`li.filter-make-model input.filter-make`)
- For each brand, calls `https://prod.caw5.cartel.nl/cawclient/models.json?ccid=768&makes=${brandSlug}` — this is stable (200 OK even when the main site is down)
- Normal count: ~300 vehicles/day (small single-dealer NL site)

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

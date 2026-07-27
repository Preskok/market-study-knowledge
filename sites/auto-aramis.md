# auto-aramis (FR)

## Current status
✅ **2026-07-24 RESOLVED** — Discovered the site serves two different detail-page HTML templates (surfaced via a drift-detection null-value increase). Fix tested locally on a full crawl and deployed to prod same day.

## History & quirks (newest first where known)
- **2026-07-24** — Found (via Uroš's drift-detection null-value flag) that `auto-aramis` apparently serves 2 different HTML templates for detail pages. Fix tested locally on a full crawl, deployed to prod same day. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784892844544109)
- **2026-05-18** — Slight drop 2.75k→~2.5k. Site confirmed 2533 vehicles; drop is legitimate. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1779107075945509)
- `rawIsUsed.includes('occasion')` no safeguard.
- bodyType footer removed.


<!-- merged from second source section -->

- `PRIX EN BAISSE` = "falling price" banner on site → NOT a regular discount. Decision: save only the current displayed price, do not treat PRIX EN BAISSE as discount.
- Site occasionally removes original price (shows only reduced price without context). Next day when discount data reappears → PVL "too much change" fires for ~100 vehicles. Expected pattern, not a bug.
- URL format: `aramisauto.com/voitures/{brand}/{model}/{version}/{vehicle-id}`
- Stakeholder: Jan Mrhar (receives DL alerts for aramis vehicles).

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

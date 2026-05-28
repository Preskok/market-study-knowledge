# ahm / schmidt-automobile

## Current status
🟡 **2026-05-27 WATCH** — Recurring ECONNRESET proxy failures during 6 AM reruns for both sites. Code healthy — confirmed locally.

## History & quirks (newest first where known)
- **2026-05-27** — schmidt: 0 vehicles; ahm: 30 vehicles (partial run before proxy died). Both confirmed ECONNRESET proxy failures during 6 AM rerun. Code healthy: schmidt got 10 vehicles locally, ahm got 14 vehicles locally. Manual trigger on prod should recover. Pattern: proxy intermittently unreachable at rerun time → partial or zero crawl.
- **2026-05-25** — Problem preparing listingUrl messages at midnight for both ahm and schmidt-automobile (also rastetter). 6AM auto-rerun succeeded for all but schmidt-automobile only yielded 200 vs expected 300 vehicles; site still shows 300. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1779682055148269)
- **2026-05-14** — ahm: 18% drop, back to normal same day ✅. schmidt-automobile: 85% drop, back to normal same day ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1778485086288569)
- "Prepared 0" intermittent — 6/7/8 AM auto-rerun fixes.
- Schmidt: query in `elastic-search.service.ts:3513` returns nothing when no vehicle updated in 3 days — expected.
- AHM href oscillation: site alternates between full URL (`https://ahm.gmbh/...`) and relative URL in href attribute. Fix uses `startsWith(baseUrl)` check: if href already starts with base URL, don't prepend it. Happened every ~14 days.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

# ahm / schmidt-automobile

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
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

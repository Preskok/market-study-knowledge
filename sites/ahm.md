# ahm

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- AHM href oscillation: site alternates between full URL (`https://ahm.gmbh/...`) and relative URL in href attribute. Fix uses `startsWith(baseUrl)` check: if href already starts with base URL, don't prepend it. Happened every ~14 days.
- "Prepared 0" intermittent — 6/7/8 AM auto-rerun fixes.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance: newest-first, YYYY-MM-DD format -->

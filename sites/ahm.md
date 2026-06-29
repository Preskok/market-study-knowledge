# ahm

## Current status
✅ **2026-06-16 RESOLVED** — Chrome UA < 140 rejection fixed by updating user-agents library. Decision: update user-agents manually every ~3 months (reminder set in #tt-market-study-checklist for every 15 weeks).

## History & quirks (newest first where known)
- **2026-06-15/16** — 50% drop in crawled vehicles over 3 days. Root cause: ahm (and schmidt-automobile) are hosted on the same server; it rejects requests with Chrome UA < 140. Fix: updated user-agents library (new patch version has Chrome 140+ UAs). Since package-lock.json locks the patch version, user-agents doesn't auto-update. Deactivation was NOT locked (drop wasn't sudden enough to trigger automatic lock). Decision: manual update every ~3 months (reminder set for every 15 weeks in Slack). [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1781508175413899)
- AHM href oscillation: site alternates between full URL (`https://ahm.gmbh/...`) and relative URL in href attribute. Fix uses `startsWith(baseUrl)` check: if href already starts with base URL, don't prepend it. Happened every ~14 days.
- "Prepared 0" intermittent — 6/7/8 AM auto-rerun fixes.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance: newest-first, YYYY-MM-DD format -->

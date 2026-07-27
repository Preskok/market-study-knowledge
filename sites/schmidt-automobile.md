# schmidt-automobile

## Current status
✅ **2026-06-16 RESOLVED** — Chrome UA < 140 rejection fixed by updating user-agents library. Same root cause and fix as ahm (hosted same server). Deactivation was locked during the incident; now unlocked.

## History & quirks (newest first where known)
- **2026-06-15/16** — Really unstable: ~100 vehicles/day avg for 3 days vs normal ~327. Deactivation locked automatically; site auto-rerunning. Root cause: server (shared with ahm) rejects Chrome UA < 140. Fixed by updating user-agents library. See [[ahm]] for full context - same incident. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1781508175413899)
- Query in `elastic-search.service.ts:3513` returns nothing when no vehicle updated in 3 days — expected behaviour, not a bug.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance: newest-first, YYYY-MM-DD format -->

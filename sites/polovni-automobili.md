# polovni-automobili (RS)

## Current status
🟡 **2026-05-22 WATCH** — Unstable graph: 78k→72k→>78k (even 84k some days). Monitoring — may be organic stock increase.

## History & quirks (newest first where known)
- **2026-05-18→2026-05-22** — Numbers dropped from 78k to 72k since 2026-05-18. Recovered to >78k (84k on 2 days) by May 22. Graph unstable — further tracking needed next week. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1779107075945509)
- Supermodel vs model duplicates.
- Empty brand → cheerio error.
- `+` in model names → `%2B`.
- Oct 2024: ~1.3k SVL logs/day for `name` prop — listing vs details title has different whitespace (2 spaces vs 1). Normalize multi-spaces at parse time on both listings and details. Quick fix, big win in reduced details-revisit requests.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

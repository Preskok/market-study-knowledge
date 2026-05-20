# polovni-automobili (RS)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
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

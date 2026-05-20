# blocket (SE)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- CloudFront protection — shared `MS_LIMITED_CONSUMERS_LISTING_URLS_TO_FETCH` with otomoto.
- Details URLs + IDs changed; JWT API gone — required URL/ID-format adjustments to keep details parsing alive.
- Shares crawler logic with finn (NO) historically; see `finn.md` for related context.
- driveTrain null for ~86k vehicles at launch. SVL disabled for 1 day to back-fill details for all. Re-enabled after.
- Version field changes (PVL): Swedish dealers add/remove words from version string — ~1200 logs/day is normal, not a bug.
- Sept 2024: details script removed from page (see known-sites.md history). Price moved to listing + fee component.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

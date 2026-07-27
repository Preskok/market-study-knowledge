# blocket (SE)

## Current status
ℹ️ **2026-06-29 INFO** — Model enrichment from Schibsted: scenic e-tech, megane iv replacing older model names. Ongoing genuine site change, not a crawler bug. Monitoring.

## History & quirks (newest first where known)
- **2026-07-17** — DOFR quirk observed: the site appears to use the date the vehicle was first registered *in Sweden* as DOFR, not the actual production year, for imported/re-registered vehicles. Two examples flagged: a vehicle previously registered under the Swedish military, only registered as a personal vehicle in 2026; and a vehicle imported from the US and registered in Sweden in 2021 (both show a much smaller production year than their DOFR). Frequency across the full dataset not yet quantified — awareness note, not a parsing bug. [Slack](https://preskok.slack.com/archives/C04K2LP3AG0/p1784296993161769)
- **2026-06-26→2026-06-29** — 19% validation logs (MODEL 66%, VERSION 27%). Genuine model enrichment by Schibsted: scenic -> scenic e-tech, megane -> megane iv. Did not fully revert by 2026-06-29 - new cases appeared (transit versions, electric models). Confirmed genuine site-side update, not SVL fails or listings/details mismatch. Filip confirmed Schibsted owns both blocket (SE) and finn (NO) - changes synchronized across both. Monitoring. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782105347592299)
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

# ouestfrance-auto (FR)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- Redirected to **zoomcar.fr** (disabled as of early 2026). The domain `ouestfrance-auto.fr` now fully redirects to zoomcar.fr. This is a completely different site requiring a ground-up refactor — different URL structure, different HTML, different API. Do NOT attempt to patch the existing crawler; it must be rewritten if zoomcar.fr crawling is prioritized.
- Incapsula 200-fake responses (body contains challenge iframe, HTTP 200 status).
- **Retry strategy evolved:** retries 5 → 7 → 9 across multiple fixes. Timeout between retries 5s → 10s → 7s (found 7s more effective than 10s). High Incapsula block rate means many retries required.
- ~133k–162k vehicles/day when healthy. Significant variation based on Incapsula block rate that day.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

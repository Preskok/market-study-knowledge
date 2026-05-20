# bynco (NL)

## Current status
**LEGACY — retired.** Site no longer sells vehicles through their platform.

## History & quirks (newest first where known)
- Removed — clean related config or reporting crashes. Site stopped selling vehicles through their platform (Jul 2025 disclaimer); 0 vehicles on site then. When the code-side config was removed, reporting scripts that iterate ES vehicles by site key crashed on bynco entries (Pattern #89). Guard: add null-check for `adSiteConfig` wherever sites are iterated from ES results.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

# willhaben (AT)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- Static proxy `proxy.b2b-carmarket.eu:8030`. Scheduled 8 AM rerun failed once due to ECS downscale.
- Whitelisted IP `3.75.69.226` occasionally gets de-whitelisted by willhaben → all requests 403 Forbidden (they block AWS IPs). Local IP gets 400 Bad Request (different response = API change also possible). When this happens contact Jan Mrhar to re-whitelist. Observed Mar 2025.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

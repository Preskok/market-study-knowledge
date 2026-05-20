# auto-zeilinger (AT)

## Current status
**2026-04-23 FIX DEPLOYED, cleanup pending** — Details URL legacyUrl change (trailing `-` removed from name segment). Fix merged to master. Vehicles from 2026-04-23 and 2026-04-24 need to be deleted (crawler was not rerun on those days to avoid doubling stock).

## History & quirks (newest first where known)
- **2026-04-23** — Details URL change: legacyUrl name-segment previously ended with `-`, now does not. Result: same workingUrl could exist in Data index with two different storeIds (different activeFrom/activeTo). Fix: hardcode trailing `-` in legacyUrl name builder. Matea tested locally with raw S3 responses. Fix merged directly to master (hotfix). Crawler NOT rerun on 2026-04-23/24 to avoid stock doubling — vehicles with `activeFrom` on those two dates must be deleted. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1777349596109229)
- `buildVehicleWorkingUrl` no fallback when details API fails.
- 200-with-empty-body pattern (needs `isServerError()` extension).

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

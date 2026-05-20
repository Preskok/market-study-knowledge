# eurostocks (DE)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- Sends RMQ directly from `getBrandsAndModels()` (legacy).
- Excluded from no-vehicles alert.
- 405 on listings endpoint (MAR-1774).
- 12k duplicates from worker restart.
- Auth key extracted via regex from a script on their site; saved to **Redis** (NOT S3, because `useS3Cache: false` — user-agent must stay in sync with `xPlatformToken`). When site changes the script's encoding/key format → fix regex (prefer `/[a-z]/` over a specific char for future-proofing). Testing: delete Redis entry (Another Redis Desktop Manager) to force refresh on next request. Matea 2025-03: MAR-1760 era fix.
- **Oct 6, 2023 — catastrophic regex hang** (Pattern #85): One Jaguar listing had extremely long title/equipment text. A regex backtracked exponentially → JS event loop blocked → health check stopped responding → 100+ failed ECS redeploys overnight → 0 consumers → ~4M vehicles not crawled. Fix: crop all text fields to max length before regex operations.
- **Missing body types by day** (Jul 2023): Some days SUVs, coupes, hatchbacks missing from results. Related to how they paginate by body type — if an API call for one body type fails silently, that entire category is skipped. No DL messages generated (listing phase error, not detail phase).
- **VIN location**: Sometimes in description text (not parsed), sometimes in `specifications.chassisNumber` field (is parsed). No fix needed — just awareness that VIN coverage is partial.
- **July 2023 problems**: e-motors-france-troyes and eurostocks both had problems same day — not always related.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

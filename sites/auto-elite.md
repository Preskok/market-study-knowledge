# auto-elite (IT)

## Current status
✅ **2026-05-22 RESOLVED** — Back to 4277 vehicles after 2-day recovery from 500 errors. Transient server-side issue.

## History & quirks (newest first where known)
- **2026-05-20→2026-05-22** — 77% volume drop (1k vs 4.3k normal). Many 500 errors overnight. Back to normal 4277 vehicles 2 days later ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1779107075945509)
- **2026-04-28→2026-04-29** — `etape1` API endpoint (`/api/devis/etape1/<id>`) intermittently 500 → losing `numberSeats` and `equipment` data. `recap` endpoint also sometimes 500 → losing `dofr` and `emissions`. `etape3` and `navbar` endpoints fine. Only 3987 vehicles instead of 4200 (site query difference, not due to "destockage"). Recovered fully next day: 4200 vehicles, query back to normal ✅. 500s appeared to be transient server-side issues. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1777349596109229)
- **2026-04-24→2026-04-25** — 15% volume drop one day, recovered to usual numbers next day ✅. Discrepancy remains: site shows 4.2k vehicles, crawler got 3.5k (~17% gap). Matea flagged for follow-up next week. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1777349596109229)
- Stock fluctuations. `used` query returns `new`.
- 503 on large listings.
- `UNABLE_TO_VERIFY_LEAF_SIGNATURE`.
- Safeguards removed from `getBrandsAndModels()` to allow auto-rerun.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

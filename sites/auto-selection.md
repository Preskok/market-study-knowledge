# auto-selection (FR)

## Current status
**2026-04-22 BROKEN** — Site fully redesigned. Cloudflare added. Details URL format completely changed (IDs don't map to old ones). Crawler prepared 0 listings. Full refactor needed — ticket opened.

## History & quirks (newest first where known)
- **2026-04-22** — Crawler prepared 0 listings, no error thrown, no auto-rerun triggered. Investigation: site fully redesigned with Cloudflare protection. Details URL format changed entirely — old: `/voiture-occasion/renault-clio/26631095.html`, new: `/voiture-occasion/renault/clio/a-283003` (`a-` prefix + new ID scheme, old IDs don't match). Title slug in URL can also change. Ticket opened for full refactor. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1776853130738149)
- Site fully changed April 2026. Cloudflare. IDs don't map. Full refactor.
- `UNABLE_TO_VERIFY_LEAF_SIGNATURE` via proxy.


<!-- merged from second source section -->

- SSL certificate verification failure → Axios throws cert error on homepage. Fix: per-request `httpsAgent: new https.Agent({ rejectUnauthorized: false })`. Global config option did NOT work.
- Site intermittently has SSL issues. Rerun usually resolves if site has recovered. If cached response exists, delete it and rerun.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

# biltorvet (DK)

## Current status
✅ **2026-06-08 STABLE** — Crawling stable since Friday 2026-06-06. No MS_DL messages from biltorvet in week of 08.06. Prior 5xx overnight errors appear to have been transient host-side maintenance.

## History & quirks (newest first where known)
- **2026-06-08** — Matea confirmed crawling stable since Friday 2026-06-06. No MS_DL messages from biltorvet in week of 08.06 (only promo-neuve). Prior 5xx overnight errors resolved. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
- **2026-06-05** — 4 listings returned status `525` (Cloudflare SSL handshake failure with host). Not covered by `isServerError()` retry → HTML passed forward → exception in code. Negligible vehicle drop. Matea suggests waiting to see if recurring before fixing. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780304827309509)
- **2026-06-04** — 6 DL messages (all from biltorvet). Root cause: status 500 at ~02:00 CEST — likely host-side maintenance. Drop ~100 vehicles vs prior day. Resolved by next crawl. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780304827309509)
- **2026-05-07** — Cloudflare 521 cached as "valid" → `null[1]` crash in `getModelCountAndUrlPath` at `Biltorvet.service.ts:515` (deployed 521). Proxy IPs blocked at Cloudflare; 3 unique Create-endpoint cache keys all stored 521 HTML bodies because `CrawlerAbstract.isServerError` caps at statusCode 507. Two crash modes: `undefined.match` (~02:18–02:21 CEST, proxy retries exhausted, no cache write) and `null[1]` (~01:00 + 02:47 CEST, reading the poisoned cache). Fix path: extend `isServerError` to cover 520–530 + delete bad keys (or wait 7 days for natural S3 expiry). See failure-patterns.md #3b and references/cache-investigation.md.
- First-request timeout — drop `useProxy`, add `host` header, POST `/Page`.
- Regex fallback.
- Known to have `fullPrice < discountedPrice` (biltorvet pattern referenced across threads) — discount calc produces negative values; skip saving discount in that case.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

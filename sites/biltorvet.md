# biltorvet (DK)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
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

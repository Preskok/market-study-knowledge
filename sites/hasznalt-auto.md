# hasznalt-auto (HU)

## Current status
🟡 **2026-05-14 WATCH** — ScrapeDo brotli decompression issue: response sent with `brotli` encoding but not decompressed, causing "Empty sub-selector" errors. Monitoring.

## History & quirks (newest first where known)
- **2026-05-14** — "Empty sub-selector" errors from ScrapeDo sending brotli-compressed responses without decompressing (sent `Content-Encoding: br` header but raw compressed bytes). Not the same cross-user contamination pattern as autoscout-ch — specific to brotli handling. Monitoring. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1778485086288569)
- Scrape.do allowlisted (1-credit works).
- HTML: `#details-vehicle_information` → `#details-vehicle-information`.
- Currency conversion after 30 days forces details re-visits.
- Fake 404 on listings (use `isResponseRateLimited()`).
- Fake 410 on details; real-missing also 410.
- Premium requests sometimes ALL fail while 1-credit succeeds — domain-specific block.
- Shared HUNGARY queue (matchingDay 1).
- URL format evolved to encoded alphanumeric blobs (`/talalatilista/PCOHK…355F/`). Old `/szemelyauto/brand/#model` still works (fallback path) but some counts differ per listing.
- Model names with URL-special chars (`#`, `:`) break `nextPageUrl`: `smart #1` and `honda e:ny1` append `/page2` 1000+ times recursively. Root cause: URL fragment parser. Symptom: one listing message consumes 1000 ScraperAPI credits + 5 retries × 30min RMQ timeout (150+ min wasted per listing). Fix: dedup `/page2` in nextPageUrl. See MAR-1743 era; ~10k-20k credits/month saved.
- ScraperAPI works ONLY for listings, not details (blocked without premium proxies) — Nov 2024 confirmation.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

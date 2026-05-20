# autoscout-ch (CH)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- **2026-05-14** — scrape.do returned a Spanish billing API JSON response (`{"success":true,"title_response":"consulta de factura"...}`) for `mo-a-200/mk-mercedes-benz?pagination[page]=4`. Body started with `{` → `$(html).find(...)` threw `Error: Empty sub-selector` (cheerio treated non-`<` body as CSS selector). Single RMQ message affected; rest of crawl continued. S3 key poisoned: `20260515/8cd9da929f09516ecc4651c3d4e412fa` (note next-day date — CEST timezone). Fix: delete S3 key; code fix pending to detect non-HTML 200 responses.
- Scrape.do. Details persistently blocked — `skipDetailsUrlValidation: true`.
- JSON script format variants.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

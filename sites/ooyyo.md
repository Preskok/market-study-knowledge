# ooyyo (multi-country aggregator)

## Current status
**LEGACY — retired.** Removed due to duplicates and price anomalies vs other sources.

## History & quirks (newest first where known)
- **Currency comparison for SVL:** ooyyo lists vehicles from multiple countries with prices in original currency. Exchange rates update every 2 days. If SVL compares converted EUR prices (default), all vehicles fail SVL every 2 days (exchange rate shift looks like a price change).
- **Fix:** Compare original-currency price for SVL (not EUR). Save both original currency and converted EUR. See Gregor decision: "compare original currency so exchange rate changes don't trigger SVL".
- Vehicles from many countries — do not limit to a single currency in the crawler.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

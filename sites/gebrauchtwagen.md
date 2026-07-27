# gebrauchtwagen (DE)

## Current status
**LEGACY — retired.** Exact duplicates already on autoscout (autoscout24.com AT country); site is owned by AutoScout24.

## History & quirks (newest first where known)
- Migrated to autoscout24 backend. Disabled.
- Fake 503.
- Tinyproxy stub 200 responses broke cheerio.
- Fake 404: status 404 must RETRY (real 404s go through 10 retries before we declare "not found") → override `isResponseRateLimited()`. True not-found = 200 response + specific HTML string ("Fahrzeug nicht gefunden" / `.ellipsis` text) → override `isResponseNotFound()`.
- `isResponseNotFound()` executes BEFORE `isResponseRateLimited()` — order matters; if you match rate-limit on a genuine 404 you'll retry 10x and burn credits.
- Daily cache gotcha: responses matching `isResponseNotFound()=true` are NOT saved to S3. Can't cross-check "today's blocked response" from S3 on the same day.
- "Bitte die Seite neu laden" / `SEITE NEU LADEN` is the reload-required hint for fake-404 detection. Avoid matching on `Upppss` — too unreliable.
- `fuelConsumption` listing parsing removed → SVL fails dropped 55k → 1.8k.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

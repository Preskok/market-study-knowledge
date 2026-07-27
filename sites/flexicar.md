# flexicar (ES, PT)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- **Next.js data API** crawler (not HTML scraping). Fetches from internal Next.js `/_next/data/{buildId}/es/coches-segunda-mano/{brand}/{model}.json` endpoints.
- `307` redirect encoded in JSON body while HTTP status is `200` — must detect via body content and treat as `isResponseNotFound()` (ad gone/redirected). Not a real redirect.
- `reserved` status in listing → set `isOnStock: false`. `isToOrder` is **always false** for flexicar (used car dealer, never order-only).
- bodyType: loop all body type combinations (`getBrandsAndModels()` pattern — similar to alles-auto). Each body type adds a dimension to the listing URL.
- S3 cache key bug: response key was `md5(url_undefined)` — if buildId extraction failed, URL became `url_undefined` → all responses cached under same wrong key. Fixed by ensuring buildId always present.
- Bodytype selectors change periodically (affects HTML fallback path if API fails).
- `engineCapacity` int-vs-float logic.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

# mobile-bg (BG)

## Current status
🟢 **2026-05-08 OK** — Full flow test passed. parseVehicleInput, parseEquipment, and parseDealer all confirmed working. Dealers: "NIRAT AUTO", "AUTO P&K", "Автопарк Венко", "МИНЕВ АУТО" extracted from Audi A3 vehicles.

## Test brand+model
- brand: Audi
- model: A3
- verified: 2026-05-08
- notes: Strategy A (brandPath filter + break-on-first) targets Audi A3. VW = 'vw' (Latin) and is a popular brand (excluded by `.not('[data-popular]')` production selector — do NOT use VW for testing). `dealerId` not in old index (`marketstudy_search_rollover`) — verify dealer extraction via `market-study-raw-dealers` index with `site.keyword: "mobile-bg"` range query. Hungary queue may have thousands of backlogged messages from production scheduler; purge `MS_HUNGARY_LISTING_URLS_TO_FETCH` before triggering to avoid long waits.

## History & quirks (newest first where known)
- **2026-03-17** — MAR-2039: added `encoding: 'windows-1251'` for HTML responses and Cyrillic→Latin brand mapping (`победа→pobeda`, `чайка→chayka`). Before this, Cyrillic brand names were decoded as garbled UTF-8 → different `StringHelper.slugify()` output → different listing URL slugs → different storeIds. Deploy caused re-index spike for all Cyrillic-named brands.
- **2025-08-xx** — MAR-1806: brand/model HTML changed. Rebuilt model URL construction: was pure-API (`model.link` directly), now hybrid API+HTML. Also changed `brandName.replaceAll('.', '-')` before slugify to plain `brandName` — any brand with `.` in name got a different URL slug → re-index spike for those brands on deploy.
- **2025-01-17** — MAR-1762: crawler first created. Initial prod deploy indexed entire inventory (~120k vehicles) — natural first-index spike, not a bug.
- **2026-05-08** — Flow test passed: getBrandsAndModels ✅, parseVehicleInput ✅, parseEquipment ✅, parseDealer ✅ (4 dealers from Audi A3 listing). Key findings: VW is 'vw' (Latin slugify), popular brand (excluded by `.not('[data-popular]')`); `dealerId` absent from old ES index (vehicleToEsVehicle doesn't map it); Hungary queue heavily backlogged by production scheduler.
- Brand/model HTML changed (Aug 2025).
- Currency bug: EUR decimals alongside BGN → wrong prices.
- Fake site counter (180k vs real 121k per-model sum).
- `AC` model undefined `modelPath` — skip with log.
- Shared HUNGARY queue (matchingDay 0).
- Listings-without-model fix: use latin-only URL from API response (Cyrillic chars break second request).
- Supermodel/submodel (e.g. `G-class` vs `G`) duplicates — site counter buggy, actual URL counts match.
- Fake 404 on details: body `{status: "error", status_code: "404"}` with HTTP 200. Override `isResponseNotFound()`:
  ```typescript
  public isResponseNotFound({ response, responseBody }): boolean {
    return DataHelper.normalizeNumericValue(responseBody.status_code) === HttpStatusCode.NOT_FOUND
      || super.isResponseNotFound({ response, responseBody });
  }
  ```
- Only Bulgaria — `/namira-se-v-balgariya` endpoint filters out foreign-country ads (otherwise we'd scale up to other markets unintentionally).
- Bulgarian used cars (>6000km, >6mo) may legally skip VAT → treat all prices as brutto to avoid SVL price-flip spam (VAT toggle changes price ~20%).
- 5k SVL / 120k = ~4% price changes per 3-day crawl — acceptable baseline for BG market.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

# rastetter (DE, buyer-stock)

## Current status
✅ **2026-07-21 TRANSIENT BLIP RESOLVED** — Automatic reruns didn't go through at all today; Matea reran manually on prod after confirming it worked locally, recovered, and removed the deactivation lock same day. Unrelated to the MAR-2113 rewrite below.

🟢 **2026-07-06 FIXED (2nd pass)** — Full rewrite shipped (MAR-2113), PR #77 merged to develop 2026-07-03. A `bodyType: null` regression (100% of vehicles, found during a post-deploy `crawler-data-validation prod` pass) was fixed and shipped separately 2026-07-06 on a rebuilt branch (original branch/PR was already merged+deleted). 266/266+ vehicles have `BodyType` populated after the fix. See quirks below.

## History & quirks (newest first where known)
- **2026-07-21** — Automatic rerun did not go through at all today. Matea confirmed it worked locally, reran manually on prod, recovered successfully, and removed the deactivation lock same day. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784620149166029) / [fix](https://preskok.slack.com/archives/C0859KQ45B2/p1784633204197279)
- **2026-07-07** — 22% fewer vehicles than the day before; back to normal the following day. Minor, self-recovered fluctuation, unrelated to the rewrite/URL-change event below. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1783311314203489)
- **2026-07-06** — CRITICAL "potential URL change" alert (265/265 vehicles = 100% newly active). Root cause: expected side effect of the MAR-2113 full rewrite (audaris API crawler → `/shop/` HTML crawler) — `legacyUrl`/storeId format changed entirely, so no old vehicle can map to a new one; Filip confirmed post-hoc this wasn't considered during the rewrite but the vehicles genuinely cannot be mapped given how different the URL structure is. Concurrently, the site's own real stock also dropped from ~1400 to ~250 around the same time as the rewrite. One-time re-baseline artifact of the rewrite — no further fix planned. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1783311314203489)
- **2026-07-06** — On the `.e-loop-item` listing card, the taxonomy classes (`vehicle_design-*`, `fuel_type-*`, `gear_box-*`, `vehicle_type-*`, `brand-*`, `product`, etc.) are ALL on the card element itself — there is no separate nested `.product` wrapper. `vehicleEl.find('.product').first()` (searches descendants only) therefore always returns an empty selection, making `classes = ''` and every class-derived field null. This shipped in the original rewrite and stayed hidden because `fuelType`/`transmission`/`mileage`/`horsePower` all have a detail-page label fallback (`detailsDict['Kraftstoff'] || partialVehicle?.rawFuelType`) that masked it; `rawBodyType` has no such detail-page source and was the only field to fully expose the bug — 100% null in prod for 3 days post-launch. **Fix:** read `vehicleEl.attr('class')` directly (no `.find()` needed — the card element carries its own classes).
- **2026-07-01** — Site's own Elementor Loop Grid pagination is broken: the "weiter" (next) link and the `data-next-page` attribute on `.e-load-more-anchor` both drop the current path segment (e.g. `/shop/?e-page-a26cbc4=2` instead of `/shop/brands-vw/?e-page-a26cbc4=2`) — confirmed by inline site JS that itself patches this bug client-side before a real browser click uses it (`nav.querySelector('a.page-numbers:not(.prev):not(.next))')` to recover the correct root). Numbered page-number `<a>` links (`?e-page-a26cbc4=2`, `=3`...) DO have the correct path, but that hash is Elementor-widget-specific and regenerates on template re-save, so don't rely on it either way. **Fix:** construct `/page/N/` (native WordPress pagination, verified to serve identical content to the query-param form) using `data-max-page` on `.e-load-more-anchor` as the reliable "how many pages" signal — that div is absent entirely when there's only one page.
- **2026-07-01** — A single listing card can carry multiple `vehicle_design-*` taxonomy classes at once (e.g. a Ford Transit Connect tagged with both `vehicle_design-vanupto7500` AND `vehicle_design-boxtypedeliveryvan`). Deriving `rawBodyType` from "which fahrzeugtyp filter page discovered this brand+model" (the outer discovery loop) causes SVL to flip-flop between the two values depending on crawl/queue timing, since the vehicle gets discovered via both filter loops. **Fix:** derive `rawBodyType` from the card's own `vehicle_design-*` classes with a fixed pick-priority list, and drop the outer bodytype-filter loop from `getBrandsAndModels()` entirely — it finds the exact same 17 brands as reading `/shop/` once (verified), so it was pure redundant overhead once bodyType stopped depending on it.
- **2026-07-01** — Current price and MSRP (strike-through) selectors need to exclude the "Weitere Vorschläge" (related products) `.e-loop-item` carousel rendered further down every detail page — `.woocommerce-Price-amount.first()` and `.reg_price-text .strike.first()` both intermittently matched a *related* vehicle's price instead of the main one. **Fix:** current price from `.sticky-bottom-bar .woocommerce-Price-amount` (single occurrence, main-vehicle-only); MSRP from `.reg_price-text .strike` filtered to exclude anything inside `.e-loop-item`. Listing cards don't have this contamination risk (no related-products widget on listing pages), but MUST use the same final price/MSRP values as the detail page or SVL fails on `price` for every discounted vehicle.
- **2026-06-08** — Matea noted deactivation prevention did not lock on Friday when site was disabled. Root cause: `shouldSiteRunToday()` check returns false for disabled sites, so deactivation check is skipped entirely. Filip confirmed this is a known gap; no ticket yet. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
- **2026-06-05** — Full site rewrite discovered: `rastetter.de` homepage now redirects to `/shop/`. No trace of `audaris` API or client IDs in browser network tab. Was an API crawler visiting `api.audaris.de`. Full rewrite of crawler needed — ticket MAR-2113 created (unassigned, Medium priority). Also: deactivation prevention check missed this site because it was disabled before the check ran (`shouldSiteRunToday()` logic). [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780304827309509)
- **2026-06-05** — First 302 status exception not caught by any `isResponse*()` → 302 HTML saved to S3 as valid → all subsequent reruns read poisoned cache and fail. Matea investigated and deleted S3 key for rerun — but then discovered full site rewrite (above). [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780304827309509)
- **2026-05-25** — Problem preparing listingUrl messages (alongside ahm and schmidt-automobile). 6AM auto-rerun succeeded ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1779682055148269)
- **2026-05-14** — Problem preparing listingUrls at midnight; automatic rerun at 6AM succeeded ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1778485086288569)
- **2026-04-21** — Automatic rerun triggered and completed successfully ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1777349596109229)
- Site-side duplicates (~700).
- Wrong API URL → 400-600 dupes/day.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

## Test brand+model
- brand: Seat
- model: (per-vehicle - no model loop)
- verified: 2026-06-19

## Test pagination
- brand: Nissan, model: Qashqai — 43 vehicles across 4 pages (12+12+12+7), confirmed zero duplicate URLs, all correctly scoped to `brands-nissan/model-qashqai/page/N/`
- verified: 2026-07-01

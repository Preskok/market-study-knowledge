# star-terre (FR, buyer-stock)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- Negative discount: `prixConstructeur` (manufacturer/catalog) sometimes LOWER than `prixClient` (seller) → discount < 0, our calc logs `"Something went wrong with discounted price calculation"` then skips saving discount/discountedPrice.
- API response fields: `virtuel: 0` + `publishedMarketplace: 0` = discount visible on site (always positive). `virtuel: 1` + `publishedMarketplace: 1` = discount hidden (can be pos or neg). Use these flags to decide whether discount is "real" before saving.
- Decision (with cardoen): save `prixClient` as `price`, don't save discount. Awaiting broader catalog-price decision from product.
- API page limit: 1000 vehicles (50 pages) — site has ~2.5k, so we miss ~60%. Refactor `getBrandsAndModels()` to crawl per brand (Renault/Peugeot/Citroen each <1k).
- Buyer-stock site, stock reporting unreliable until API pagination is fixed.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

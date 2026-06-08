# gaspedaal

## Current status
_Newly added to SiteKeys. No incidents on file yet — check Slack._

## History & quirks (newest first where known)
_Nothing recorded yet._

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance: newest-first, YYYY-MM-DD format -->

## Source analysis (2026-06-01)

**Type** — Pure aggregator. No own vehicle detail pages. Owned by AutoScout24 (via Automotive MediaVentions). AutoTrack (same owner) is the direct listing platform gaspedaal aggregates from among others.

**WAF** — DPG Media Akamai WAF. Blocks all datacenter IPs (AWS, GCP, Azure) with HTTP 403. Puppeteer stealth + residential proxy (`useProxy: true`) bypasses it cleanly. ScrapeDo works but not needed. No captcha.

**Data format** — Next.js SSR. Full vehicle data in JSON-LD (`application/ld+json`, schema.org `ItemList`). No JS rendering required.

**Fields from JSON-LD** — brand, model, name (contains version), productionDate (year only), price, mileageFromOdometer, fuelType, vehicleTransmission, bodyType, color, numberOfDoors (99%), vehicleConfiguration (comma-separated string with cc + kW when present).

**vehicleConfiguration parsing** — `"Benzine, 999cc, 92kW, Automaat, Hatchback, Zwart, 5-deuren"`. Extract with `/(\d+)cc/i` for displacement, `/(\d+)kW/i` for power. Electric vehicles omit cc and kW entries.

**Dealer from JSON-LD** — `offers.seller`: name (56% named / 44% "Onbekende dealer" → null), city, region. No phone/email. No dealer page URL (gaspedaal page is not a real dealer URL — it's just gaspedaal's aggregated view).

**Detail URLs** — `api.gaspedaal.nl/redirect/vehicle/{occImportNr}`. One physical car has a different occImportNr per portal. AutoTrack URL (`autotrack.nl/a/{brand}-{model}-{fuel}-{year}-{advertentieId}`) is always in the page JS state but unreliable — generated synthetically by gaspedaal even when the vehicle isn't on AutoTrack (verified: Renault 11 with AutoTrack in portalen still returns HTTP 404 on AutoTrack).

**URL used as dedup key** — `https://www.gaspedaal.nl/zoeken#{advertentieId}`. No real listing page exists; this is a stable synthetic key only.

**Counter reliability** — Inflated. Same physical car can appear twice with different advertentieIds when imported from different portals with conflicting data (e.g. different year). Happens when no license plate (kenteken) is available to dedup. ~80% of vehicles have kenteken in page state (not JSON-LD).

**337k vs 220k (AutoTrack)** — AutoTrack is a direct listing platform (dealers pay to list); gaspedaal aggregates from AutoTrack + ANWB + lease portals + dealer sites + more. The gap is not purely lease vehicles — AutoTrack itself has ~85k financial/lease listings. Difference is likely market segment + counting methodology.

**getBrandsAndModels** — fetches homepage → 225 brand slugs from embedded Next.js state. Per brand: fetches `/{brand}` page → extracts model slugs where `groupId == brand.id` (filters out transmission/fuel/body-type options that appear in the same dropdown). URL pattern: `/{brand-slug}/{model-slug}`, e.g. `/volkswagen/golf`.

**Pagination** — `pagina=N` on `/{brand}/{model}`. 100 vehicles/page. Stop when page < 100 items.

**Portal data (not in JSON-LD)** — embedded JS state has `portalen` array per vehicle: `siteNr`, `portaalBeschrijving`, `occImportNr`, `klikUrl`, `tip` (primary portal flag), `portaalType` (dealer/other/financial). AutoTrack is siteNr=2, 99/101 vehicles have it; Dealersite is siteNr=19. Both are `tip: true`.

**Source:** session 2026-06-01.

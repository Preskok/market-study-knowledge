# auto-ici (FR)

## Current status
✅ **2026-06-17 RESOLVED** — MAR-2016: browser requests removed (plain axios confirmed working), equipment null crash fixed, rawVersion selector fixed, SVL stabilised (8 residual fails = dual-colour variants, won't fix). Branch `bugfix/MAR-2016-fix-auto-ici-crawler-french-proxies` pending commit.

## Angular data structure (critical for parsing)

The detail page embeds all price/equipment/color data in a single `div[ng-controller="OfferController"]` `ng-init` attribute. The attribute is multi-line — split on `\n`, trim, filter blank:

| Line index | Content | Notes |
|---|---|---|
| `lines[0]` | `init([{color objects}])` | parse: `match(/^init\((\[.*\])/s)?.[1]` |
| `lines[1]` | `[]` (empty) | skip |
| `lines[2]` | `{serial_equipment_obj}` OR `null` | `JSON.parse(line) ?? {}` — MUST guard null |
| `lines[3]` | `{optional_equipment_prices}` | optional |

`JSON.parse(lines[2])` returns JS `null` for vehicles with no serial equipment. **Always add `?? {}` guard** or `Object.values()` will throw.

## Selectors

- **rawVersion (detail):** `h1 .car-version` — then split on ` · ` and take `[0]` to strip `· Ref. XXXXXX`. Do NOT use `h1 span` — matches empty `span.car-used` and picks up dates from used cars instead.
- **price (detail):** `meta[itemprop="price"]` content attribute.
- **catalog price (detail):** extracted from ng-init color data `frenchpriceTtc` + color/options prices summed.

## Listing vs detail field compatibility

Fields that match between listing API and detail page (safe for SVL):
- `price` — `sellingpricepart_ttc` (listing) == `meta[itemprop="price"]` (detail)
- `catalogPrice` — `totalFrCatPrice` (listing) == computed from ng-init colors (detail)
- `fuelType` — `carburationtype_title` (listing) == `Carburant` label (detail), exact French match
- `mileage`, `isUsed`, `numberSeats`, `rawBodyType`, `coverImageUrl`, `rawVersion` (listing primary)

Fields that do NOT match — exclude from listing push to avoid SVL churn:
- `rawTransmission` — listing: French category `"automatique"` / `"manuelle"` ; detail: full technical name `"Automate à fonct. Continu"` / `"Manuelle"`. Different vocabulary, always diverges for CVT/DSG.
- `rawEmissionsCO2` / `emissionsCO2` — listing: plain integer `"90"` (WLTP) ; detail: `"106 g/km"` (NEDC). Different format AND different emission standard.
- `discount` / `rawDiscount` — computed by mapping layer from `price` / `discountedPrice`, never crawled directly.

## Discount metrics — two completely different numbers

- `percentage_part` (listing API) = discount from AutoIci **catalogue price** to selling price. This is what `Percent` in ES stores.
- `.card-num-why` (detail page) = discount from **brand MSRP** to selling price. Different base, always diverges from `percentage_part`. Do NOT use `.card-num-why` — it's never the same number.
- `OriginalPriceBrutto` is NOT used for this site (Euro-priced, no brand MSRP stored).

## Price logic — new vs used

`setVehiclePrice(mileage, isUsed, catalogPrice, sellingPrice)`:
- New car (`!isUsed` and mileage ≤ new threshold): `price = catalogPrice`, `discountedPrice = sellingPrice`
- Used car or no catalogPrice: `price = sellingPrice`, `discountedPrice = null`
Mapping layer derives `discount` / `rawDiscount` from these two fields.

## data-validation quirks

- **[22] `isUsed=false` + `dateOfFirstRegistration`:** EXPECTED. Mandataire cars are pre-allocated and often already licensed before sale. Do not flag.
- **[27] `Percent` without `OriginalPriceBrutto`:** EXPECTED. Euro-priced site, `OriginalPriceBrutto` is N/A. `Percent` is the catalogue discount.
- **Description:** crawler explicitly sets `description: null` — N/A.

## History & quirks (newest first where known)
- **2026-06-17** — MAR-2016: Removed `BrowserService` / `fetchRequest` override. `api.auto-ici.fr` JSON endpoint accepts plain axios (no browser, no anti-bot measures). Confirmed via `crawler-test-flow`: 1 vehicle in ES in <20s, 0 DLQ, 0 errors. **FR proxy not needed.**
- **2026-06-16** — MAR-2016: SVL reduced 244 → 8 (same-URL dual-color variants, won't fix). rawVersion selector fixed (`h1 .car-version` split on ` · `). Equipment null crash fixed (`JSON.parse(equipmentJson) ?? {}`). Removed from listing: rawTransmission, rawEmissionsCO2, emissionsCO2, discount, rawDiscount.
- **2026-05-22** — MAR-2016: Filip working on French proxies fix. Matea had notes + FR proxy handling committed in branch before vacation. Filip asked about which port/proxy set; Matea pointed to branch commit. [Slack](https://preskok.slack.com/archives/C04K2LP3AG0/p1779435417592059)
- `vehicletype_id=4` SUV consistently times out.

## Test brand+model
- brand: Citroen
- model: C3

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

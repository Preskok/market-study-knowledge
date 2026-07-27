# eurostocks (DE)

## Current status
🔴 **2026-06-12 DISABLED** — Site disabled due to persistent 403 blocks causing email spam. Ticket MAR-2114 open for proper fix. brie-des-nations threshold adjusted at same time (sofibrie source now 4k+ vehicles). Reactivation requires MAR-2114 resolution.

## History & quirks (newest first where known)
- **2026-06-12** — Site disabled by Filip due to persistent 403 blocks causing alert email spam. brie-des-nations threshold also adjusted at same time (sofibrie source now 4k+ vehicles). MAR-2114 ticket open for proper fix; will be addressed in own ticket as discussed in grooming. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
- **2026-06-08** — Still blocked. Filip investigating easy solutions. Deactivation locked automatically for this site. Ticket MAR-2114 opened. Planning discussion scheduled. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
- **2026-06-03→2026-06-06** — All retries for `eurostocks.com/en/vehicles/cars` return 403 / security check page (in browser too). VPN, ScrapeDo 10cr, 25cr all failing at times; 25cr with `waitSelector` works intermittently for B&M but not listings/details. Condition appears to change during the day (Filip noted 10cr and 1cr became successful for B&M later). PR #41 prepared for workingUrl SVL fail fix (sold vehicles skip preventing workingUrl updates). [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780304827309509)
- **2026-05-26 — crawler-data-validation findings (post-rewrite, develop `080ac771`):**
  - **Hardcoded constants** (lines 347–348): `isOnStock: true, isToOrder: false`. Also no `isCommercial` assignment → defaults to `false`. Don't flag these as bugs when 100% constant — intentional.
  - **`bodyTypeTranslations` has NO commercial mapping** — Saloon→limousine, Estate→estate, SUV…→suv, Convertible…→cabrio, Small car→hatchback, Sports Car…→coupe, Van…→minivan, Other→other. `IsCommercial=true` is impossible by construction.
  - **`Name` is the raw source title** (e.g. `"BMW 220 Gran Coupé 2-serie | m-sport pro | 19'' | panorama. | …"`) — by design, no trimming. Validate by curling the live ad and comparing `\"Title\"` from the SSR JSON.
  - **Engine field has two forms in two indices.** Old search index: `Engine` = title minus brand+model (still includes equipment dump). Data index: `engine` = synthesized clean string (e.g. `"1.4 TSI 245 FWD DSG"`, `"2.0 T5 247 AWD AT"`). Both are by design; the data-index mapper synthesises.
  - **`isUsed` logic is brittle** — `isUsed = rawIsUsed?.toLowerCase() === 'used'`. Anything else (`demo`, `pre-registered`, `new`) → `false`. Confirmed misclassification: 3-year-old Cupra Formentor with 43k km marked `IsUsed=false`. ~620 docs have `IsUsed=false` AND a `DateOfFirstRegistration`.
  - **`BatteryCapacity` extractable but not extracted.** API attribute name is `"Battery Capacity"` (Tesla Model S vid 3862961: `"Value":"100"` = 100 kWh). Partial coverage — Tesla yes, BYD Atto 3 no. One-liner fix using the existing `getFeatureAttributeValue(detailsData.Attributes, 'Battery Capacity')` pattern. **No `Range` attribute on either page** — skip `batteryRange` extraction.
  - **Description IS populated** — old search index `Description`, ~79.5% coverage (~24k of 30,286). Empty 20% are dealer-side gaps, not parser bugs.
  - **9,815 `"Vehicle has changed too much"` logs / 24h after deploy** — ~85% pure `DRIVETRAIN: (OLD: null, NEW: FWD)`. New service extracts `driveTrain` where the old one didn't. Transient migration spike; will decay after every active vehicle has been re-visited once.
  - **Negative `Price`/`NettoPrice` (8 docs)** — Ferrari 488, Bentley Continental GTC, Mercedes GLC 43 AMG/GLC 250, Land Rover Velar, Audi A1/A5, Renault Grand Scenic. NettoPrice/Price ratio = 1/1.21 (Dutch VAT) → magnitudes correct, sign flipped. All 8 caught by progressive validation (G2=9 in Graylog) → correctly blocked from data index, but they still appear in old search index. **User has a fix prepared.**
  - **HP outlier — single Ford S-Max showing 87,882 HP** — code uses `CrawlerHelper.kwToHp()` so kW gets converted. Tesla Plaid 1004-1006 HP / Porsche Cayenne Turbo Electric 1140 / Lamborghini Revuelto 1002 are all legitimate. Only the Ford S-Max is bogus — parser picked up the wrong numeric.
  - **`NumberDoors` outliers** — max 255 (byte-overflow signature), 96 docs > 5. Mini Clubman 6 may be legit (split rear doors); > 6 are parser bugs.
  - **workingUrl wiring verified end-to-end** — same vehicle has legacy URL in old index `URL` (e.g. `…/vehicles/cars/saloon/vehicle/3862961/…`) and working URL in data index `url` (`…/en/vehicle/3862961/…`). `md5(legacy URL) == data-index _id` ✅. Active subset (`activeTo` missing): 30,276/30,276 working pattern (100% ✅). W1-W5 invariants from crawler-data-validation skill all pass.
  - **URL-change-detection email fired CRITICAL at 54.7% ratio** (16,563 newly-active / 30,272 crawled) — false positive caused by **re-enablement spike**, not a workingUrl bug. Distinguishing signature: 0 paired deactivations in the same window (vs equal-to-newly-active for an actual storeId churn). Old `.nl`-domain docs were deactivated weeks/months ago during the disabled period, not in this crawl. See knowledge base `url-change-alert` for the diagnostic and full signature table.
  - **10,854 `prop:workingUrl` SVL fails over 48h** (9,026 day-1 / 1,828 day-2, decaying) — 100% have `existingValue` field MISSING (stored vehicle's workingUrl is null/undefined). Root cause: **rewrite deployed listing-level + details-level workingUrl assignment in the same commit on a `shouldValidateListingVehicle: true` site**, violating the documented phased rollout (`fix-playbook.md § Implement workingUrl/legacyUrl` explicitly warns: "do details-only first, otherwise mass SVL failures from change detected"). Benign — each fail forces a details re-visit which populates workingUrl. Self-healing within ~3 days. See knowledge base `listing-vehicle-check-diagnostic` for the `existingValue`-shape diagnostic. **Lesson for future rewrites**: when adding workingUrl to a SVL=true site, ship details-only assignment first, wait for coverage, then add listing-level.
- Sends RMQ directly from `getBrandsAndModels()` (legacy).
- Excluded from no-vehicles alert.
- 405 on listings endpoint (MAR-1774).
- 12k duplicates from worker restart.
- Auth key extracted via regex from a script on their site; saved to **Redis** (NOT S3, because `useS3Cache: false` — user-agent must stay in sync with `xPlatformToken`). When site changes the script's encoding/key format → fix regex (prefer `/[a-z]/` over a specific char for future-proofing). Testing: delete Redis entry (Another Redis Desktop Manager) to force refresh on next request. Matea 2025-03: MAR-1760 era fix.
- **Oct 6, 2023 — catastrophic regex hang** (Pattern #85): One Jaguar listing had extremely long title/equipment text. A regex backtracked exponentially → JS event loop blocked → health check stopped responding → 100+ failed ECS redeploys overnight → 0 consumers → ~4M vehicles not crawled. Fix: crop all text fields to max length before regex operations.
- **Missing body types by day** (Jul 2023): Some days SUVs, coupes, hatchbacks missing from results. Related to how they paginate by body type — if an API call for one body type fails silently, that entire category is skipped. No DL messages generated (listing phase error, not detail phase).
- **VIN location**: Sometimes in description text (not parsed), sometimes in `specifications.chassisNumber` field (is parsed). No fix needed — just awareness that VIN coverage is partial.
- **July 2023 problems**: e-motors-france-troyes and eurostocks both had problems same day — not always related.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

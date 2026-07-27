# otomoto (PL)

## Current status
🟡 **2026-07-27 WATCH** — Vehicle count fluctuating: rose from ~230k to ~255k around 07-18 (matched the site's own personal+LCV counter), then fell back to ~235k over the 4 days to 07-27 with no clear cause — the number of listingUrls prepared is unchanged and forbidden/error counts are actually lower than before. Not yet root-caused.

## History & quirks (newest first where known)
- **2026-07-27** — Fell from ~255k to ~235k over the last 4 days; prepared the same number of listingUrls, and forbidden/"could not complete" counts are actually lower than before — no obvious cause found yet. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1785131713654149)
- **2026-07-21** — Vehicle count increased since Saturday (07-18): ~230k → ~255k, matching the site's own personal+LCV counter total. Couldn't confirm root cause since PROD logs weren't checkable that week (Graylog outage). [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784630677432219)
- **2026-06-30** — Filip noticed while browsing the site directly that personal-vehicle stock looked smaller than usual (compared to over a year ago, so not a strict apples-to-apples baseline). No confirmed numbers or root cause posted, no follow-up in the thread. **Needs human review** — anecdotal observation only, not backed by a concrete before/after count. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782709643021479)
- URL: `brand-model-trim-ID.html` → `brand-model-ID.html`.
- `__NEXT_DATA__` truncation.
- Cloudflare escalation — retries to 9, `host` header added.
- Selector: `p:contains()` needs quotes; `.siblings('p')`.
- GraphQL `filters` moved out of `searchTerms`.
- Stale S3 cache crash-loop incident: Sep 2024 — first request succeeded (not forbidden) but subsequent reads from S3 detected as "Response was forbidden". Means forbidden-check must match on the live response, not on the cached copy that was originally not-forbidden. Check `isResponseRateLimited()` carefully — it reads from response body not from HTTP status alone.
- Commercial vehicles URL path also blocks more aggressively — rerun pattern.
- **Sept 10, 2025 URL change:** listing URL format changed (again). Similar to the `brand-model-trim-ID.html` → `brand-model-ID.html` earlier change. Check legacyUrl vs workingUrl handling and apply the standard pattern if URLs don't redirect cleanly.


<!-- merged from second source section -->

- GraphQL endpoints: `https://www.otomoto.pl/graphql` (main) and `https://search-filters-provider.a.otomoto.pl/graphql` (brand/model counts).
- Special brand mapping: Lublin brand listing URL must be `/dostawcze/marka_lublin` (not `/dostawcze/lublin` which returns ALL LCVs).
- `beforeCrawlListingUrl()` method added to abstract class for post-getBrandsAndModels enrichment per listingUrl.
- getBrandsAndModels makes 1000-1700 GraphQL requests — slow and gets blocked on prod. First run: mostly forbidden, only ~320 successful in 1h. Uses S3 caching for subsequent runs.
- CloudFront protection → moved to `MS_LIMITED_CONSUMERS_LISTING_URLS_TO_FETCH` (10 consumers, Sept 2024).
- ~250k vehicles/day expected (actual), ~270k theoretical. LCV ("dostawcze") category slightly under-counted.
- ~1000 duplicates/day: same ad listed in multiple cities with different URLs.
- Description selector changed mid-2024 — description not stored.

## Listing URL formatter (search feature, MAR-2121)
`src/formatter/const/AdSitesForUrlFormatting.ts` builds a filtered `otomoto.pl` listing URL from an AMS search request. All values below verified live 2026-07-01/02 (browser + real prod ES data via local dev).

- **Param convention** — `search[filter_...]` bracket keys (`URLSearchParams` percent-encodes to `%5B %5D %3A`, Otomoto accepts it as-is).
- **fuelType** (`search[filter_enum_fuel_type]`, multi-value via repeated bare key): `gasoline→petrol`, `diesel→diesel`, `electric→electric`, `ethanol→etanol`, `other→hidrogen` (not `hydrogen` — real slug is the Polish/typo spelling, confirmed live: `hydrogen` returns 0 always). **`gas` has no Otomoto mapping at all (final decision 2026-07-02, per PR review from Matea Lencek + Sales requirement)** — Otomoto's `Benzyna+LPG`/`Benzyna+CNG` (`petrol-lpg`/`petrol-cng`) bi-fuel slugs are intentionally unused; a `gas` search on Otomoto produces no fuelType filter. (Earlier iterations tried mapping `gas`'s slugs onto `hybrid` or giving `gas` its own mapping — both were wrong; the final, reviewed answer is: don't map `gas` at all.) **`hybrid` combo logic** (mirrors AutoScout/Mobile/LeBonCoin's `fuelTypeCombinations` pattern): searching `hybrid` alone → `hybrid`+`plugin-hybrid`; searching `hybrid` combined with another fuel type (e.g. `gasoline+hybrid`) → only plain `hybrid`, no plug-in and no gas-hybrid slugs either way. Config: `paramValues.fuelType.HYBRID = ['hybrid', 'plugin-hybrid']` plus `fuelTypeCombinations: { 'gasoline+hybrid': ['petrol', 'hybrid'], 'diesel+hybrid': ['diesel', 'hybrid'] }`.
- **transmission** (`search[filter_enum_gearbox]`): only `automatic`/`manual` exist on-site. `semi_auto`/`cvt`/`sequential` have no Otomoto equivalent — correctly unmapped (dropped silently, not a bug).
- **driveTrain** (`search[filter_enum_transmission]` — yes, drivetrain uses the "transmission" filter key, gearbox uses "gearbox"; don't cross-wire): `FWD→front-wheel`, `RWD→rear-wheel`. AWD is **three** distinct site values, not one: `all-wheel-auto` (4x4 dołączany automatycznie), `all-wheel-lock` (4x4 dołączany ręcznie), `all-wheel-permanent` (4x4 stały) — all three must be sent via `shouldAppend`. Previously mapped to `4x4-permanent`/`4x4-attachable`, which are not real Otomoto values at all (silently return 0 results always, for any query).
- **engineCapacity** (`search[filter_float_engine_capacity:from/to]`) — site expects **CCM**, AMS stores **liters**; `isConversionRequired: true` triggers `Math.floor(liters * 1000)`. Confirmed liters-vs-CCM distinction live: sending `3000` as a CCM value returns a small plausible count for 3.0L variants; sending it as liters would be nonsensical.
- **horsePower** (`search[filter_float_engine_power:from/to]`) — Otomoto stores KM (metric hp), AMS already stores KM for Otomoto specifically — no conversion needed (unlike AutoScout which needs `isMetricConversionRequired`).
- **dateOfFirstRegistration** (`search[filter_float_year:from/to]`, year only) — `:from` is a normal, fully-functional query param; Otomoto's own frontend JS rewrites the address bar to a `/od-{year}` path form **after** the filter already applied server-side (no HTTP redirect, `redirectCount: 0`) — purely cosmetic, don't try to build the path form yourself. `:to` has no equivalent path rewrite, always stays a query param.
- **dealerFilter**: `search[private_business]=business`.
- **sort**: `search[order]=filter_float_price:asc` (only sort Otomoto's config — or any site's config — supports).
- **"Generacja" (generation) ≠ AMS `version`** — Otomoto's Generacja filter is a small closed per-model chassis-code enum (e.g. Audi A4: B5–B9), fundamentally different from AMS's `version` field (free-text trim/edition like "S line", "Design"). Not mapped, and shouldn't be — no data exists to bridge them; `dateOfFirstRegistration`/year is the closest available proxy already in use.
- **Single-country site** — PL only; `country` paramName/paramValues are both `null` in config (same pattern as LeBonCoin).

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

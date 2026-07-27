# auto1 (FI)

## Current status
✅ **2026-07-27 RESOLVED (brand vw/volkswagen flip-flop)** — Progressive validation was oscillating `brand` between `vw` and `volkswagen`; confirmed fixed — brand reverted back to `volkswagen` on Saturday (07-25) and has held since.

✅ **2026-07-23 RESOLVED (driveTrain/transmission null regression)** — A separate regression caused `driveTrain` and `transmission` to flip to null for many vehicles; fix deployed 2026-07-22, confirmed restored to proper values 2026-07-23.

🟢 **2026-07-13 FIX COMMITTED** — branch `bugfix/MAR-2129-fix-auto1-null-detail-fields`, squashed commit `55c4712ce`. Fixes null detail-page fields, equipment parsing, and dealer name/siteUrl/location parsing after the site redesign (all stem from the same event as the 2026-07-07 brands-selector fix below). Not yet merged/deployed to prod as of this commit.

## History & quirks (newest first where known)
- **2026-07-27** — Confirmed no more `vw`↔`volkswagen` brand oscillation; values reverted back to `volkswagen` on Saturday (07-25) and have held since. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1785132635109199)
- **2026-07-24** — New progressive-validation flip-flop noticed: `brand` oscillating between `vw` and `volkswagen`. Monitoring to see if it persists — resolved by 07-27, see above. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784893031120439)
- **2026-07-23** — Confirmed the `driveTrain`/`transmission` null fix (deployed 07-22) restored proper values. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784806339289229)
- **2026-07-22** — `driveTrain` and `transmission` found flipping to null for many vehicles (progressive-validation alert). Fix identified and deployed same day; since `transmission` is also present on listings, affected vehicles were expected to recover the next day once SVLs fail and force a re-visit. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784723837144349) / [fix](https://preskok.slack.com/archives/C0859KQ45B2/p1784728321869439)
- **2026-07-13** — MAR-2129: after the same site redesign that broke brand/model selectors (see 2026-07-07 below), three more things were also broken and fixed in this commit:
  - **Equipment** (`parseVehicleInput`): selector was `.acc i` (0 matches — no `<i>` tags exist in the new markup). Fixed to `.acc li` — equipment now lives as `<span class="acc"><h3>Category</h3><ul><li>item</li>...</ul>...</span>`, grouped by category headers but flattened into `notCategorised` same as before.
  - **parseDealer name/siteUrl**: old code expected `<a><b>Name</b></a>` inside a sibling-selector lookup (`div:contains(Myyjä) + span`); new markup is a bare `<a class="sname">Name</a>` directly under `.mb.ls`. The broken chain silently produced `name: ""` and, since the dealer path lookup then failed too, `siteUrl: "https://www.auto1.fiundefined"` (verified live in prod data from 2026-07-10, before this fix — every sampled dealer that day had this exact garbage). Fixed by selecting `.sname` directly for both text and `href`. **Expect a one-time `dealerId` re-index for every existing auto1 dealer once this deploys** — `DealerHelper.calculateDealerId` hashes `name` too, and it goes from empty to real; this is fixing broken source data, not a regression, but will look like "mass new dealers" if not anticipated.
  - **Location** (new): `.saddr` div holds street + zip as two adjacent text nodes split by a bare `<br>` (no wrapping tags), with city in a sibling `<a>`. Parsed via cheerio `.contents().filter(el.type === 'text')` (see code-standards.md). `mapsUrl` taken directly from the existing Google Maps `<iframe src>` on the page (API-keyed embed URL, same as several other crawlers use their own site-provided map link verbatim).
  - **Phone**: also simplified — old regex-matched `Puh\.` out of a broader block of concatenated text; new code selects `.srow a[href^="tel:"]` directly.
- **2026-07-07** — `getBrandsAndModels()` prepared only 174 listing URLs (normal: ~780). Root cause: `/autot` page added `.mkgrid` section for 32 popular brands (Audi, BMW, VW, Ford, Toyota, Mercedes, etc.). These moved out of `.fbox a` into `.mkgrid .mk a.row1`. Crawler's `#cont .fbox a` selector now only picks up ~71 niche/commercial brands → 174 listing URLs almost all with near-zero inventory → 296 vehicles vs ~48k normal (↓99.4%). Also: `brandName` extraction uses `.find('span').first()` but row1 links use `<b>Brand</b><span>count</span>` structure — would extract the vehicle count ("2 968") not the brand name.
  - **Fix applied (commit `a78aa57e1`):** In `getBrandsAndModels()`: (1) brands selector changed to `#cont .fbox a, #cont .mkgrid .mk a.row1`; (2) brandName extraction changed to `$(brand).find('b').length ? $(brand).find('b').first() : $(brand).find('span').first()`. Verified locally: 294 listing URLs, ES write confirmed.
  - **Brand sub-pages unchanged:** `/volkswagen` etc. still have `.carlist[data-search]` + 90 model links in `.fbox a` — no change needed there.
  - **Motorhome exclusion still works:** `.not('#cont .mbl:contains(Matkailuautomerkit) + .fbox a')` still correctly excludes motorhome brands.
  - **Jun 27–29 zeros** (same issue — site rolled out the new HTML then, recovered Jun 30, likely via S3 cache of old brand list or temporary rollback).
- **2026-07-06** — MAR-2129 opened: details are storing `null` for `bodyType`, `colour`, `numberSeats`, `numberDoors`, `transmission`, `driveTrain`, `engineCapacity`, and `horsePower` — the details (ad) HTML changed. Not yet fixed; priority to be discussed at grooming. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1783311314203489)
- **2026-07-03** — Possible bug flagged (found via Gemini review): crawler may be setting a random "MacIntel" top user agent inconsistently. MAR-2128 opened to investigate when time allows — not yet researched. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782709643021479)
- `niesmann bischoff` 0-vehicles brand → wrong mapping.
- ECONNRESET / curl SSL issues.
- **Site re-uses numeric listing ids for unrelated vehicles over time** (not a storeId bug — confirmed via `the storeId-drift verification method` 2026-07-13). Example: id `149788` was `volkswagen/polo` in Dec 2024, `skoda/enyaq` in Jan 2025, `citroen/e-c3` in Jul 2026 — each a real distinct ad. `storeId = md5(url)` correctly differs since brand/model in the path differ too, even though the trailing numeric id is identical. When comparing prod snapshots across time for this site, always diff the full url path, never just the trailing id (see `the storeId-drift verification method` Common mistakes table).

## Key URLs
- Brands page: `https://www.auto1.fi/autot`
- Brand example: `https://www.auto1.fi/volkswagen` (90 model links in `.fbox a`, `.carlist[data-search]` present)

## Test brand+model
- brand: Volkswagen
- model: Golf

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

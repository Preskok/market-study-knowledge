# pazar3 (MK)

## Current status
🟡 **2026-05-09 FLOW OK, DATA BUGS OPEN** — Flow test passed (83 VW Golf rows, 19 raw-dealers). Known data bugs: `getNextPageUrl()` broken (50 vehicles max), `/wanted/` URL indexing bug, `mileage 0` data corruption. Matea working on combined fix PR. MAR-2098 open.

## Test brand+model
- brand: Volkswagen
- model: Golf
- verified: 2026-05-08
- notes: substring-match needed (`brandName.toLowerCase().includes('volkswagen')`) — site formats brand as "vw volkswagen". Strategy A (break inside loops) is required — Strategy B took 49 min on this site due to ~30 brand × N model walk via browser+proxy. Run yielded 3,621 VW Golf rows; 0 DealerId on any (worth investigating); Equipment field present but all sub-arrays empty.

## History & quirks (newest first where known)
- **Friday peak in Data index (unconfirmed hypothesis)** — On Saturday only ~57k vehicles were crawled (normal ~90k). ~47k were subsequently deactivated with `createdAt = lastVisit = Friday` (standard deactivation pipeline behaviour — `createdAt` is overwritten to the last-seen date). On Sunday those vehicles were reactivated (crawler found them again) — `activeTo` was removed but `createdAt` was NOT updated, so the Data index still shows a spike attributed to Friday. No code fix needed — this is a transient partial-crawl artefact, not a persistent bug. See `ams deactivation-pipeline` for the `createdAt = lastVisit` mechanism. Not confirmed in code.
- **2026-05-09** — Flow test passed: getBrandsAndModels ✅ (brand filter needed: "vw volkswagen"), 83 VW Golf rows in ES ✅, 19 raw-dealers ✅ (parseDealer working), equipment=0 (VW Golf sample has no equipment data). `IsListingValidatedVehicle: false` (first local crawl — no S3). POLAND queue had 9402 pre-existing messages (unrelated backlog). Pipeline slow — browser detail fetches take ~10 min for one listing page.
- **2026-05-03→2026-05-04** — `getNextPageUrl()` broken: only 50 vehicles from all listings (site pagination changed). Also noticed saving `/wanted/` URLs (wanted ads) instead of `/for-sale/` — wrong vehicles being indexed. Separate pre-existing bug found: when `mileage` absent from ad, saving `0` instead of `null` (corrupted data for unknown duration). All three issues being fixed by Matea in one PR; data corruption for `mileage` will persist for previously-crawled vehicles. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1777879864126089)
- **2026-04-28→2026-04-30** — Extremely slow requests (4.3 s/request); only 8k–10k vehicles crawled (expected ~90k). Main problem: even after processing listings, only a small fraction of vehicles was saved. Site removed `mileage` from listing pages → SVL fails spiked: 20k fails day 1, 30k fails day 2. Prepared only 1113 listing messages one day (all vehicles). Ticket MAR-2098 created for the mileage/listing field removal. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1777349596109229)
- **2026-04-20** — 503 errors overnight, site unreachable. Prepared 0 listings. Matea reran crawler, recovered and crawling again ✅. Known 503-burst pattern during site maintenance. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1777349596109229)
- Cloudflare — 50% 403s.
- Switched to browser requests. Stable.
- 503 bursts during maintenance.
- Site counter inaccurate — skipping vehicles without price drops actual count (~38/47 for Jeep Compass).
- bodyType filters unreliable: losing 30-35% vehicles when filtering. Redirects (301) to brand-level listing when bodyType not supported. Decision: skip bodyType parsing, crawl all.
- "other models" supermodel listings → mass duplicates & SVL fails → skip them.
- Pinned ads usually duplicate normals — skip if same storeId on normal listing.
- Vehicles without price saved with `null` + `isCrawlingVehiclesWithoutPrice: true` flag (prevents "Vehicle missing price" log spam). Adria report needs them for market representation.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

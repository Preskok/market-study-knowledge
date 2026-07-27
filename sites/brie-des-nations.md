# brie-des-nations (FR, buyer-stock)

## Current status
✅ **2026-07-13 RESOLVED** — Deactivation endless-lock-loop diagnosed and fixed. Root cause: ~1,219 `vehicle_visit` rows frozen at `lastVisit=2026-06-11` (likely from a vehicle-reactivation run whose `lastVisit` gets backdated to the original `activeTo` — see `market-study-knowledge.md § deactivation-pipeline`), permanently dragging the site's ratio to ~25% against the 20% threshold. Confirmed (not a crawler-coverage bug, not URL/storeId drift — the storeId-drift verification method + live-site browser check) that all sampled frozen vehicles were genuinely sold. Fixed via scoped `POST /active-vehicle/get-and-update-expired-vehicles {"beforeDate":"2026-06-13"}` (note: `beforeDate` must clear `lastVisit + 1 day`, not just match the calendar date — see KB). Ratio dropped 25.05% → 7.12% after the purge. Unrelated to the Alfa Romeo URL issue below, which remains resolved.

✅ **2026-07-08 RESOLVED** — Site fixed the Alfa Romeo URLs; they no longer 404 and the crawler parses them normally again. MAR-2123 fix is no longer needed but ticket left open for a while in case the issue recurs.

## Test brand+model
- brand: Renault
- model: Clio
- verified: 2026-05-09
- notes: First brand+model alphabetically. Strategy A. Uses `crawl.general.#` queue. Single-dealer site — all vehicles have dealer. Equipment sparse (new-car stock). Base URL still `sofibrie.fr` (not `renault-noisiel.briedesnations.fr`).

## History & quirks (newest first where known)
- **2026-07-24** — Automatic rerun successful. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784877832858019)
- **2026-07-23** — Slight drop in numbers (4.6k → 4.5k) over the last few days; matches the ~4,650 currently stated on site. Too small to alert on; will keep an eye if it continues. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784806744157979)
- **2026-07-13** — Resolved the endless deactivation-lock-loop noted earlier the same day. `vehicle_visit` had 1,219 rows stuck at `lastVisit=2026-06-11` (~25% of the site's ratio calc), never advancing even on days with healthy full crawls (confirmed via ES `Site`/`CreatedAt` histogram showing 1.4k-7.9k docs/day the whole time). Ruled out: crawler under-coverage (ES writes were healthy every day), storeId/URL drift (`the storeId-drift verification method`: identical URL shape, `md5(url)` matched stored `storeId` exactly), and the `SiteThresholds` large/small reclassification from 2026-06-12 below (plausible-looking Slack-timeline correlation, but didn't hold up against the actual stuck data). Confirmed root cause by browser-checking 3 sample frozen vehicles directly on `sofibrie.fr` — all showed "VENDU" (sold)/out-of-stock. Purged via `POST /active-vehicle/get-and-update-expired-vehicles {"beforeDate":"2026-06-13"}` (had to use `06-13` not `06-12` — see `market-study-knowledge.md § deactivation-pipeline` for why). Ratio 25.05% → 7.12%, site should hold unlocked through the next nightly cycle.
- **2026-07-13** — Filip noted (self-reminder) that this site's deactivation process is locking in an endless cycle. No cause or fix identified yet - needs follow-up. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1783919282702339)
- **2026-07-08** — Site fixed the two Alfa Romeo listing URLs that were 404ing since 2026-06-12; crawler is parsing them normally again, fix is not needed for now. Ticket MAR-2123 left open for a while in case it recurs. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1783311314203489)
- **2026-06-19** — Alfa Romeo 404 issue persists. Matea confirmed still returning 404 (also in browser). All vehicles for that brand lost. Matea asked Filip/Gregor to address with a proper solution (e.g. skip-and-log problematic brands rather than crashing) if it persists next week. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1781508175413899)
- **2026-06-12** — Vehicle count dropped 4k to 3.5k. Alfa Romeo listing URL returning 404 (browser also shows 404 intermittently - likely their issue). Filip retried and it succeeded once but not consistently. Team decided to wait until Monday. Site threshold also adjusted: sofibrie source grew to 4k+ vehicles, old threshold was set for <2k (no email fired on 15% drop as a result). [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
- **2026-05-09** — Flow test passed: getBrandsAndModels ✅, 11 Renault Clio vehicles ✅, 6 dealers ✅. All `IsListingValidatedVehicle: false` (URLs changed since April 3 run — no SVL hits).
- Moved to `renault-noisiel.briedesnations.fr`.
- Two branches (Val d'Europe, Noisiel).
- **Pricing:** `listPrice` = catalog/factory price, `price` = seller price. Negative discounts are NORMAL here (dealer markup on limited-availability / custom configs) — not a bug.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

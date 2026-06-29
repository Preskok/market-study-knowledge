# brie-des-nations (FR, buyer-stock)

## Current status
🔴 **2026-06-19 OPEN** — Alfa Romeo listing returning 404 persists since 2026-06-12. Matea flagged: if still present next week, address with Gregor to implement handling for such responses (losing all vehicles for that brand). Threshold was adjusted after 2026-06-12 drop.

## Test brand+model
- brand: Renault
- model: Clio
- verified: 2026-05-09
- notes: First brand+model alphabetically. Strategy A. Uses `crawl.general.#` queue. Single-dealer site — all vehicles have dealer. Equipment sparse (new-car stock). Base URL still `sofibrie.fr` (not `renault-noisiel.briedesnations.fr`).

## History & quirks (newest first where known)
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

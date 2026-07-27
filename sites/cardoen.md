# cardoen (BE)

## Current status
✅ **2026-07-27 CONFIRMED OK** — 12% fewer vehicles than a few days prior; the number corresponds to the number on site — legitimate stock change.

## History & quirks (newest first where known)
- **2026-07-27** — 12% fewer vehicles compared to a few days ago; confirmed to correspond to the number on site. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1785130898125499)
- **2026-05-18** — Slight drop 1.2k→1.1k. Site confirmed 1194 vehicles — drop is legitimate. Monitoring. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1779107075945509)
- bodyType filter removed. Later family-cars category narrowed.
- "Cardoen Advantage" = catalogPrice - cardoenPrice. Gregor decision 2025-02: this is NOT a discount and must NOT be saved as `discount`. Save only `catalogPrice` (from details) and `price` (from listing = cardoenPrice). Same pattern as star-terre negative discount.
- Listing has only `discountedPrice` (cardoen price), details have `catalogPrice` — OK to save only price from listing, catalogPrice from details.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

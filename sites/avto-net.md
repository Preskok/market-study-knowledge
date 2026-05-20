# avto-net (SI)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- Mobile proxy `9007` (Stas) — gone down twice.
- Cloudflare on commercial xml — 7AM rerun usually works.
- Browser request timeout bumped from 10s.
- Discount source: `.GO-OglasDataStaraCena` = striked-out full price (only exists when discount); script `adData.cena` = discounted price. Parse `html-price || script-price || null`. Decision: do NOT save `discountedPrice` — most discounts here are leasing/financing-conditional (not a real buy-price discount). MAR-1859 removed script fallback.
- Dealer name parsing sometimes returns doubled value (e.g. `"DealerName DealerName"`) — source for name appears multi-origin; bug reported by Tjaša Feb 2025, not yet root-caused.
- **July 2023: Double protection** — avto-net added Cloudflare on top of DataDome. Required new bypass logic. One day without data during transition.
- **First registration date**: Only year available on listing (`1.1.XXXX`), not month. Marko's workaround: generate `16.1.XXXX` (mid-month synthetic) so data consumers can tell it's year-only. `16` as day signals "synthetic, year-only".
- **April-May 2023**: Site changed security settings → 2 days without data.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

# avto-net (SI)

## Current status
🟡 **2026-05-22 WATCH** — Increased browser timeouts + forbiddens escalating (1→7→50→14/day); 98.5% resolve via retries. Listing crawl finishing ~8:00–8:30 CEST (was 09:20 earlier in week, >12:00 historically). Will confirm stability next week.

## History & quirks (newest first where known)
- **2026-05-29** — Spike in `net::ERR_TUNNEL_CONNECTION_FAILED` from proxy `http://proxy.b2b.aws:9004`. Caused listing crawl delay (334 listings still in queue at peak time). Proxy not fully down — resolved without manual intervention. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1779682055148269)
- **2026-05-18→2026-05-22** — Slower crawling: many more exceptions at night (700+ vs <100 normally). Listings finished at 09:20 on 2026-05-20. Browser timeouts and forbiddens increased from 1/day → 7 → 50 → 14, but 98.5% of requests succeed through retries. Finish times improving: 8:30 Wed → 8:00 Thu. Weekend finishing at 8AM. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1779107075945509)
- **2026-05-25** — Finishing at 8AM through weekend ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1779682055148269)
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

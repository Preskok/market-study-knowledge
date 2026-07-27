# avto-net (SI)

## Current status
✅ **2026-07-20 RESOLVED** — Missing all vehicles in the ES Old index; queue had messages but they weren't producing indexed docs; 302 redirects on listing requests reproduced locally and in a manual browser visit. Diagnosis was initially blocked by a PROD Graylog/Stage ES outage (shared LJ server issue), but Matea found and deployed a fix to prod the same day. Rerun succeeded — ~85% of vehicles crawled by 16:38, fully caught up (last 370 details) by ~21:45. Exact root cause of the 302s not detailed further in Slack.

ℹ️ **2026-07-07 INFO** — Stock increased; new normal is approx. 59k vehicles. Open suggestion pending: consider removing the explicit "no proper response" error throw now that 0-listing-message reruns are retried anyway (not yet actioned). Also: an external Reddit thread (not our own incident) speculates Cloudflare may soon require crawler registration — worth keeping an eye on for this and other Cloudflare-protected sites, but unconfirmed and not yet affecting us.

## History & quirks (newest first where known)
- **2026-07-24** — FYI noted: crawler has been finishing earlier this week (~10-11h) than its usual weekday finish (~14h). Can't confirm whether this relates to the 07-20 fix, since all PROD logs from before 07-20 were permanently lost in the Graylog outage. Needs human review if it becomes a pattern. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784883278492669)
- **2026-07-20** — Missing all vehicles in ES Old index; queue has messages but they aren't producing indexed docs. Matea debugging locally, reproduced 302 redirects on listing requests in both crawler code and manual browser visit — suspects listing generation is broken, not yet confirmed. Can't check PROD logs yet — Graylog and Stage ES both down (LJ server outage). Fix found and deployed to prod same day; rerun succeeded, ~85% crawled by 16:38, fully caught up by night. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784532082666149)
- **2026-07-07** — Stock increased; new normal is approx. 59k vehicles (up from prior baseline). [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1783311314203489)
- **2026-07-06** (event ~07-04 Saturday midnight) — Hit the explicit "no proper response received" forced-error-throw, triggering an automatic rerun; 6am rerun succeeded. Filip suggested reconsidering removal of this explicit throw now that "prepared 0 listing messages" already gets retried anyway — not yet actioned, needs a decision. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1783311314203489)
- **2026-07-06** — External Reddit post (not our own crawler/incident) about a third-party avto-net crawler mentions Cloudflare may soon require stricter crawler registration. Unconfirmed, informational only — worth monitoring for potential future impact on this and other Cloudflare-protected sites. **Needs human review** — no concrete detail, source is an external Reddit thread. [Slack](https://preskok.slack.com/archives/C04K2LP3AG0/p1783356351757329)
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

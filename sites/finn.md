# finn (NO)

## Current status
✅ **2026-06-12 RESOLVED** — Name SVL fix deployed; all vehicles indexing correctly. Series/Class-to-model oscillation calmed (only ~hundreds vs prior thousands per day) and did not reoccur in last 3 days.

## History & quirks (newest first where known)
- **2026-06-12** — Name SVL fix confirmed working; classes/models oscillation did not reoccur in last 3 days. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
- **2026-06-09/12** — Name SVL fix deployed: listings do not include brand+model in name; details do - causing SVL fails. Fix adds brand+model to listing name. Regarding *Series/*Class models: ~6k vehicles changed to specific models; thousands changed back to classes day-after, then calmed (hundreds/day). Oscillation pattern: site serves same vehicle from the same listing under both `*Series`/`*Class` and a specific model - likely a site-side inconsistency. Eventually calmed without code change. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
- "Solgt" (sold) vehicles show no price on listing → skip, don't crawl.
- `mileage` / `rawOriginalPriceBrutto` SVL fails — known fragile fields.
- Both finn and biltorvet have leasing ads requiring explicit skip.
- finn shares some crawler logic with blocket — see `blocket.md` for shared-logic context.
- Price on listing = WITH re-registration fee (Norwegian law: re-registration fee ~1800 kr). Price on details = WITHOUT fee.
- Decision: save listing price (with re-registration fee). This allows SVL to work (prices match between listing and saved). If details price (without fee) were saved, SVL would fail every day since listing shows different price.
- Fee visible as separate field `(re-registration fee)` on details page.
- Sept 2024: details script removed from page — had to parse price from HTML with fee component split.
- MS_DL errors on DL queue for some parse errors — trace via request-id chain.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

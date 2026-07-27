# finn (NO)

## Current status
✅ **2026-06-12 RESOLVED** — Name SVL fix deployed; all vehicles indexing correctly. Series/Class-to-model oscillation calmed (only ~hundreds vs prior thousands per day) and did not reoccur in last 3 days.

## History & quirks (newest first where known)
- **2026-07-16** — Investigated an apparent triplicate/duplicate on ES for one VIN (`JTNACABB90J018034`): the same vehicle turned out to be 3 genuinely separate ads (own ID/URL each), published back-to-back (15.05→21.05, 22.05→11.06, 12.06→ongoing) — not a crawler dedup bug. Also flagged: the oldest ad's stored `rawModel` was `Corolla` while the site currently shows `Corolla Cross` for the same listing. Matea confirmed parsing was correct at the time — once an ad is marked inactive we stop re-checking it for model edits, so a site-side model correction made *after* we deactivated the ad won't be caught; a new ad for the same car appeared again on 07-16 and will show up in ES after the next crawl. Not a parsing bug — a known limitation of skipping re-validation on inactive ads. [Slack](https://preskok.slack.com/archives/C04K2LP3AG0/p1784188728973699)
- **2026-06-26→2026-06-29** — 17% validation logs (MODEL 65%, VERSION 26%). Same Schibsted-driven model enrichment as blocket (SE): scenic e-tech, megane iv, transit versions, electric models. Did not fully revert by 2026-06-29. Confirmed genuine site-side update - both finn and blocket owned by Schibsted, changes synchronized. Not a crawler bug. Monitoring. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782105347592299)
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

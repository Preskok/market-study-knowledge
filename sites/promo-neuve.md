# promo-neuve (FR)

## Current status
🟡 **2026-07-07 WATCH** — Unlocked from deactivation lock, but still under-crawled: ~7500 vehicles vs. the ~11k baseline, days after the autoscout-ch queue-clog root cause (2026-06-29) was resolved. No new root cause identified yet — worth continued tracking. `}` parsing failure (2026-06-22) still not code-fixed.

## History & quirks (newest first where known)
- **2026-07-15** — Hasn't shown up in the `MS_DL` queue for a while — likely because the vehicles that previously hit the parsing problem (the `}` in equipment description bug, see below) have since been sold and delisted. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1784097769796119)
- **2026-07-13** — 6k vehicles vs. the ~7.6k Saturday baseline; recovered to normal by the next day. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1783935841629749)
- **2026-07-07** — Unlocked from deactivation lock so old vehicles can deactivate again, but still only getting ~7500 vehicles instead of the ~11k baseline — recovery from the 06-29 autoscout-ch queue clog is incomplete. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1783311314203489)
- **2026-07-03** — `MS_DL` queue purged for promo-neuve. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782709643021479)
- **2026-07-02** — Recovered to 7460 vehicles (up from 0 the day before), following the autoscout-ch ScrapeDo fix. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782709643021479)
- **2026-06-29** — Severely under-crawled: only ~10% of usual vehicles due to autoscout-ch blocking MS_HUNGARY_LISTING_URLS_TO_FETCH queue (ScrapeDo credits exhausted). Filip purged autoscout-ch from queue to restore normal processing. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782709643021479)
- **2026-06-26** — Ad-recycling behavior investigated: ~7.5% of stock gets deactivated every 3-day crawl cycle. Root cause: dealers re-post the same vehicle under new URLs (same price, engine, name). Example: same Opel Corsa dealer posted multiple overlapping ads with different IDs but identical vehicle data, some co-existing simultaneously. This is genuine site behavior (not a crawler bug). coverImageUrls go stale after deactivation so image-based dedup is not feasible. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782105347592299)
- **2026-06-22** — 7 MS_DL messages (all promo-neuve), purged. Same `}` bug ongoing. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782105347592299)
- **2026-06-09** — Filip purged the MS_DL queue for promo-neuve Transporters during week 08.06. 5 messages in the latest run (down from 6 prior). Same `}` bug, no code fix deployed. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1780895292454469)
- **2026-05-27** — 6 MS_DL messages in fri-mon window (same VW Transporter, same `}` bug). Matches 3-day recurrence from 2026-05-24. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1779682055148269)
- **2026-05-24** — 6 new MS_DL messages; **2026-05-21** — 7 messages; **2026-05-18** — 8 messages. All same VW Transporter vehicle (`E118935952`, offer codes `C059654` / `C060324`). S3 cache from 2026-05-21 confirmed `"rigide (y compris système de stabilisation de la remorque}"` equipment label is present — `}` inside string value is the confirmed trigger. 3-day recurrence matches `runOnNthDays: 3` config: crawler re-discovers the listing each run, queues detail visit, brace-counter fails, NACK → DL. Same vehicle every time = same bug every time.
- **2026-05-15** — 8 new MS_DL messages (same `}` bug). S3 raw responses confirmed as genuine promoneuve.fr pages — no ScrapeDo cross-user contamination. Root cause pinned to `getPromoNeuveVehicleDataScript`: brace-counter hits a `}` inside a description string value (e.g. `"stabilisation de la remorque}"`) and prematurely terminates JSON extraction, producing truncated input to `JSON.parse`. Fix needed: brace-counter must track when it's inside a string value to skip such characters.
- **2026-05-04** — 22 MS_DL messages due to `}` in equipment descriptions; queue purged. Issue ongoing with no code fix deployed. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1777879864126089)
- **2026-04-24** — 5 MS_DL queue messages due to `}` character in equipment descriptions (pre-existing known quirk, see History). Queue purged manually ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1777349596109229)
- DataDome + CloudFront (Oct 2025) — disabled.
- `}` in equipment descriptions → JSON extraction broken.
- `Lynk & Co`: `&` → `%26`.
- 3 transporters stuck in DL (same reason).
- **May 19, 2023: DataDome added** — site had 500 errors one day, then added DataDome protection. This is when it became difficult to crawl and reezocar became the de-facto FR new-car data source.
- **March 28, 2025: `getNextPageUrl()` infinite loop** (Pattern #88): `getNextPageUrl()` returned the same URL → listing task ran for ~19 hours, 38 RMQ redeliveries, 125k+ S3 reads. Queue purge did NOT remove the stuck unacked message. Loop broke naturally after midnight when S3 cache for that day expired, forcing a fresh request. No duplicates were created (listing never finished successfully).

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

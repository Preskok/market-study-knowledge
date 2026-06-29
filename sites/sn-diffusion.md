# sn-diffusion

## Current status
⚠️ **2026-06-20 PENDING** — Fix deployed (hardcoded Algolia API key, updated API request, URLs changed). Auto-locked on Friday at 50% threshold despite getting all vehicles. Suspected cause: URL IDs changed with refactor, triggering deactivation threshold. Investigating why the threshold fired.

## History & quirks (newest first where known)
- **2026-06-20** — Auto-locked on Friday (deactivation threshold 50% triggered) despite seemingly crawling all vehicles on Friday. Suspected cause: refactor changed detail URL IDs, causing old stored vehicles vs new crawled URLs mismatch. Filip confused since vehicles retrieved seemed normal; Matea noted the small site has a 50% threshold and URL ID changes could trigger it. Investigation ongoing. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1782105347592299)
- **2026-06-19** — Crawler stopped working. Root cause: Algolia API key and ID no longer available in page HTML. Fix: hardcoded current working Algolia API key (same pattern as `qarson` which had a hardcoded key for 5 years). API request/response structure also changed. **Details URLs changed** (ads now have new IDs) - cannot link to old legacy URLs efficiently. This is a buyerstock with ~600 vehicles; impact on turnover but not widely used by sales ATM. Filip added to [Site protection list on Confluence](https://preskok.atlassian.net/wiki/spaces/M/pages/3898114050/Site+protection+list) (CloudFront, not Cloudflare). Fix deployed same day. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1781508175413899)

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

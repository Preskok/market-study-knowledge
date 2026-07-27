# auti-hr (HR)

## Current status
🟡 **2026-05-22 WATCH** — 1521 vehicles crawled vs 1791 on site; research pending. Normal range 1.7k–1.8k. Fluctuations throughout May — monitoring ongoing.

## History & quirks (newest first where known)
- **2026-05-22** — Drop to 1521 while site still shows 1791. Research pending. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1779107075945509)
- **2026-05-25** — Back to ~1.8k vehicles ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1779682055148269)
- **2026-05-18** — Slight drop 1.8k→1.7k; site confirmed 1826 vehicles — close enough ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1779107075945509)
- **2026-05-14** — Slight drop, but on-site number confirmed close enough ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1778485086288569)
- Users often leave model blank → filtering by model on site returns 0 results even when brand listing shows them. We lose ~1k vehicles/brand listing. Decided not to fix (njuskalo covers HR better); full rewrite needed otherwise since code is 4+ years old and messy.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

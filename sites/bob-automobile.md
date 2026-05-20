# bob-automobile (DE)

## Current status
🔴 **2026-04-30 OPEN** — CRITICAL newly-active ratio alert triggered (58.4%). Possible second URL change after April's meinfahrzeug.shop migration. Investigation pending.

## History & quirks (newest first where known)
- **2026-04-30** — CRITICAL ratio alert: 2687 vehicles crawled, 1569 newly active (58.4%). Potential URL change after the meinfahrzeug.shop migration. Filip noted to check when capacity allows; no resolution confirmed in Slack. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1777349596109229)
- **2026-04-22→2026-04-24** — `bob-automobile.de` baseUrl changed (redirects to `meinfahrzeug.shop`). Root cause: `adminId` parsed incorrectly → URL contained `/null/`. S3 delete + rerun not sufficient (baseUrl itself changed). Filip prepared URL fix (PR #5 on GitHub). Fix deployed ~2026-04-23. All vehicles crawled successfully 2026-04-24 ✅. Note: site may be rebranding to `bob-automotive` — ticket opened for slug/alias renaming. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1776852517123019)
- April 2026: `bob-automobile.de` → `meinfahrzeug.shop`.
- `adminId` null → URL `/null/`.
- Details trailing `/` → allow 1 redirect on validation.
- Part of "alles-auto" group (design almost identical to autohaus-landherr).
- Some ads show "price without VAT" only → save as `rawNettoPrice` → `nettoPrice` (NOT as rawPrice).
- New vehicles show `-` for DOFR → save `rawDateOfFirstRegistration = "-"` (raw fields aren't sent to DataAPI mapping; safe to persist for debugging).
- Address block has `<br>`-separated address / city / zip — `getTextWithoutChildren()` collapses to single concatenated string. Good enough: save as `fullAddress` only, leave `addressDetails` null (MySQL dealer table stores only `branchAddress` anyway).
- Multiple dealer branches distinguishable by location (not by name after alles-auto migration).
- Mild/full hybrid ads change `fuelType` on details every few minutes (cycles between hybrid/gasoline/electric) → 2/3 of vehicles fail SVL if we read details. Use LISTING fuelType (stable).

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->

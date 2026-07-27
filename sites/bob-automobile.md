# bob-automobile (DE)

## Current status
✅ **2026-07-05 SELF-RESOLVED** — 2026-07-03 CRITICAL ratio alert (98.7%, 2526/2559) confirmed as a company-wide URL slug rename (`bob-automobile-*`/`tcb-automobile-*` → `bob-automotive-*` + branch restructuring). Self-healed via normal deactivation sweep within ~2 days (0 active duplicates as of 07-05). History-continuity repair is optional, not urgent — see entry below for exact fixable/unfixable counts.

## History & quirks (newest first where known)
- **2026-07-14** — Live-verified via `the URL-integrity root-cause method` that branch reassignment kept reshuffling well past the "self-resolved by 07-05" mass-alert stabilization: the file's own cited example vehicle (`b2adf37c-6cdb-4968-b2e5-1d8eff32b30d`) accumulated **5 different storeIds** total, bouncing through `duesseldorf`→`bochum`(historical)→`duesseldorf`(post-rename Jul 3)→`oberhausen` (Jul 8, still active). "Self-resolved" above refers to the mass newly-active/duplicate spike clearing via the deactivation sweep (accurate) - it does NOT mean individual branch-tag assignment had settled by 07-05. Anyone re-verifying this incident should check activity across the actual event window (July 2-5 in ES, not "the last N days from today") - checking only recent days shows a clean baseline and completely misses that this happened, since it already fully played out over a week prior.
- **2026-07-03** — CRITICAL ratio alert: 2559 crawled, 2526 newly active (98.7%). Root cause: BOB extended their April rebrand into the URL slugs themselves — `bob-automobile-<branch>`/`tcb-automobile-<branch>` → `bob-automotive-<branch>`, with several branches also gaining sub-brand tags or legal-entity suffixes (not a pure word-swap). Since `storeId = md5(legacyUrl)` and legacyUrl embeds this branch text, every renamed vehicle got a new storeId → mass "newly active" spike. **No VIN/secondary matching exists anywhere in the persistence pipeline** (confirmed via full code trace) — URL text is the sole identity anchor, so a rename with no code awareness is mechanically indistinguishable from "new vehicle."
  - **Self-heals**: the nightly MySQL `lastVisit`-threshold deactivation sweep (not per-crawl, not immediate) marked all ~2526 old-URL docs inactive within ~2 days with zero manual intervention. Old docs are NOT deleted, just deactivated — still queryable in the Data index.
  - **Full-population diagnostic** (queried all 2526 via ES `_msearch`, not a sample): 1291 (51.1%) are a pure `automobile→automotive` word-swap; another 1206 (47.7%) kept identical vehicle-ID+UUID but changed branch text more than that one word (sub-brand/suffix added); only 9 (0.4%) were genuine unrelated re-listings; 20 (0.8%) had no prior record.
  - **Branch lookup table** (derived from crawl history, validated against same-vID+UUID pairs only — do NOT trust the public `bob-automotive.com/standorte-oeffnungszeiten/` marketing page, it's a different backend/system and its wording doesn't match listing-URL slugs):
    ```
    bob-automobile-bochum              -> bob-automotive-bochum            (UNRELIABLE — see Bochum note below)
    bob-automobile-duesseldorf         -> bob-automotive-duesseldorf
    bob-automobile-essen-bochold       -> bob-automotive-essen-bochold
    bob-automobile-essen-frillendorf   -> bob-automotive-essen-frillendorf
    bob-automobile-essen-werden        -> bob-automotive-essen-werden
    bob-automobile-hagen               -> bob-automotive-hagen
    bob-automobile-herne               -> bob-automotive-herne
    bob-automobile-leverkusen          -> bob-automotive-leverkusen
    bob-automobile-witten              -> bob-automotive-witten
    bob-automobile-wuppertal           -> bob-automotive-wuppertal
    tcb-automobile-bochum              -> bob-automotive-toyota-bochum
    tcb-automobile-gelsenkirchen       -> bob-automotive-gelsenkirchen
    tcb-automobile-haltern             -> bob-automotive-haltern
    tcb-automobile-kamen               -> bob-automotive-kamen
    tcb-automobile-marl                -> bob-automotive-toyota-marl
    tcb-automobile-muelheim            -> bob-automotive-gmbh-muelheim
    tcb-automobile-oberhausen          -> bob-automotive-oberhausen
    tcb-automobile-recklinghausen      -> bob-automotive-recklinghausen
    ```
  - **Bochum is a trap, do not treat it as a clean mapping**: historically `bob-automobile-bochum` held ~40% of all bob-automobile vehicles (1022/2526) — looks like it was used as a default/catch-all tag rather than a real branch. After the rename only 45% of those (465) actually stayed at Bochum; the rest scattered across Hagen/Wuppertal/Essen/etc with no distinguishing signal (relocation vs. mislabel look identical in our data). Any dedup/migration logic must exclude Bochum-tagged vehicles — merging them via the table would be a coin-flip, not a verified fix.
  - **Diagnostic technique that made this fast**: batch `_msearch` against `market-study-vehicle-data_rollover` — for every "newly active" vehicle, query by `vin` (term, exact match — **`vin` is already `type: keyword`, there is no `.keyword` subfield; querying `vin.keyword` silently returns 0 instead of erroring**) with `activeFrom < event date` sorted desc, size 1, to find the immediate predecessor. Then extract the numeric listing ID (`v\d+-\w+`) and UUID from both URLs via regex — if both match, it's a pure rename; if either differs, it's a genuine re-listing (BOB does this independently of any rename, ~50% of all-time churn events per broader VIN sampling — a "stable" UUID-based storeId would fix rename events but NOT this class).
  - **No crawler code change needed for future crawls** — `htmlLegacyUrl` is built live from the API's `vehicleDetailsPageUrl` on every crawl, so post-rename crawls are already internally consistent. A code change is only relevant if you want to survive a *future* rename without re-triggering this (would need `legacyUrl` keyed on `adminId+vehicleId` instead of branch text, but that itself requires a one-time storeId migration for ALL existing vehicles — see MAR-1975 `remove-sid-from-s3-fix` pattern in market-study-knowledge.md).
- **2026-05-18** — Progressive validation logs for mileage and a few for horsePower all confirmed legit — sellers updated mileage values on their ads ✅. [Slack](https://preskok.slack.com/archives/C0859KQ45B2/p1779107075945509)
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

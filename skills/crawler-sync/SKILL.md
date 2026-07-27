---
name: crawler-sync
description: >
  ALWAYS invoke this skill when the user's message starts with "crawler-sync" — e.g.
  "crawler-sync", "crawler-sync 14" (custom day lookback), "crawler-sync 30",
  "crawler-sync all" (full Slack history), "crawler-sync confluence" (include Confluence),
  "crawler-sync all confluence" (full history + Confluence).
  This manually triggers the Market Study knowledge base sync: rebuilds aliases from
  SiteKeys.ts, harvests Slack incidents from #tt-market-study and #tt-market-study-checklist,
  optionally syncs all Confluence pages from the M space, updates per-site knowledge files,
  commits and pushes updated knowledge files to Preskok/market-study-knowledge on GitHub.
  Do NOT confuse with superpowers:systematic-debugging or any codebase operation.
  "crawler-sync" is always a knowledge-base maintenance command.
---

# ms-rebuild — Manual Knowledge Base Sync

Manually runs the same sync the weekly scheduler does. Use this when:
- You want to pull in today's Slack activity without waiting for Monday
- The weekly sync was missed (computer was off)
- You just added incidents in Slack and want the knowledge base current now
- You want to pull in all historical Slack data or Confluence docs

## How to invoke

```
crawler-sync                   → 7-day Slack lookback (default)
crawler-sync 14                → 14-day Slack lookback
crawler-sync 30                → 30-day Slack lookback
crawler-sync all               → full Slack history (no day limit)
crawler-sync confluence        → 7-day Slack + full Confluence M space sync
crawler-sync all confluence    → full Slack history + full Confluence M space sync
crawler-sync confluence all    → same as above (param order doesn't matter)
```

Params are composable — `all` controls the Slack window, `confluence` adds the Confluence step.

---

## Step 1 — Parse params and determine mode

Parse the words after `crawler-sync`:
- If `all` is present → **Slack mode: full history** (no day cap; read until no more messages)
- If a number is present → **Slack mode: N-day lookback**
- Otherwise → **Slack mode: 7-day lookback** (default)
- If `confluence` is present → **Confluence sync: enabled**

Check the last sync timestamp for reference:
```bash
cat /Users/filipozbolt/Projects/market-study-knowledge/.last-sync 2>/dev/null || echo "never"
```

---

## Step 2 — Rebuild aliases from SiteKeys.ts

```bash
cd /Users/filipozbolt/Projects/market-study-knowledge
python3 scripts/build-aliases.py
```

This reads `SiteKeys.ts`, auto-generates aliases, merges `aliases-manual.json` on top (manual entries win), and writes the result to `aliases.json`. It also prints a coverage report.

Read the coverage report. If there are new SiteKeys entries WITHOUT a `sites/<slug>.md`,
create a stub for each:

```markdown
# <slug>

## Current status
_Newly added to SiteKeys. No incidents on file yet — check Slack._

## History & quirks (newest first where known)
_Nothing recorded yet._

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance: newest-first, YYYY-MM-DD format -->
```

If you created stubs, re-check aliases.json to ensure the new slugs are present before proceeding.

---

## Step 3 — Harvest Slack incidents

### Channels
- `#tt-market-study` (C04K2LP3AG0)
- `#tt-market-study-checklist` (C0859KQ45B2)

### Process

1. Read messages from both channels:
   - **Full history mode** (`all`): paginate through the entire channel history until no
     more messages are returned. Don't stop at an arbitrary date — keep reading until the
     channel start is reached.
   - **Day-window mode**: read messages covering the lookback window only.
   For any message with replies, read the full thread — threads contain resolutions.

2. Load `/Users/filipozbolt/Projects/market-study-knowledge/aliases.json` to map site names
   to canonical slugs.

3. For each site with relevant findings (incidents, disables, URL changes, anti-bot
   blocks, crawl errors, re-enables — not "+1", "ok", "thanks"):
   a. Read current `sites/<slug>.md`
   b. **Do not duplicate** entries already in the file for the same event
   c. Prepend new entries at TOP of `## History & quirks`:
      ```
      - **YYYY-MM-DD** — [what happened + outcome/resolution]. [Slack permalink]
      ```
   d. If status changed (disabled, re-enabled, ongoing issue), update `## Current status`
   e. Write the updated file

4. Skip: pure chatter, off-topic, infrastructure not tied to a specific crawler.

### Rules
- Newest first. New entries go at TOP of History & quirks.
- Date format: YYYY-MM-DD
- Don't fabricate. Flag ambiguous threads as "needs human review".
- Do NOT touch `aliases-manual.json`.
- Do NOT run `scripts/split-sites.py`.

---

## Step 3b — Confluence sync (only when `confluence` param is present)

Skip this step entirely if `confluence` was NOT in the user's command.

### Space
- Space key: `M`
- Home page ID: `573997151`
- URL: `https://preskok.atlassian.net/wiki/spaces/M/overview`

### Process

1. Fetch all pages in the M space using `getPagesInConfluenceSpace` (space key `M`).
   Paginate until all pages are retrieved.

2. For each page, fetch full content via `getConfluencePage`.

3. Classify the content and route it to the right destination:
   - **Site-specific** (mentions a crawler site, incidents, quirks, anti-bot notes,
     historical data for a specific market): read and update `sites/<slug>.md`.
     Use aliases.json to resolve the site name to a slug. Prepend entries under
     `## History & quirks`, same format as Slack entries, with source noted as `[Confluence]`.
   - **Architecture / pipeline / infrastructure** (ES indices, RMQ, S3, DataAPI, SVL,
     queue structure, deployment flow): merge non-duplicate content into
     `~/Projects/market-study-knowledge/foundational.md`.
   - **Operational fixes / runbooks** (step-by-step recovery procedures, known fix
     sequences, incident playbooks): merge into `~/Projects/market-study-knowledge/fix-playbook.md`.
   - **Failure patterns** (recurring failure modes across multiple sites): merge into
     `~/Projects/market-study-knowledge/failure-patterns.md`.
   - **Graylog queries / monitoring**: merge into `~/Projects/market-study-knowledge/graylog-queries.md`.

4. **Deduplication rule**: before writing, check whether the key fact/fix/incident is
   already present in the target file. Only add genuinely new information.

5. If a Confluence page contains content that spans multiple categories, split it and
   write each part to its respective destination.

6. Skip: pages that are empty, purely administrative (meeting notes with no technical
   content), or duplicates of what's already in the knowledge base.

### Confluence harvest rules
- Source label: append `[Confluence: <page-title>]` to each entry so it's traceable.
- Date: use the Confluence page's last-modified date as the entry date where relevant.
- Don't fabricate. If a page is ambiguous, flag it under "Needs human review".

---

## Step 4 — Push to GitHub, timestamp, report

1. Commit and push all knowledge updates to GitHub:
```bash
cd /Users/filipozbolt/Projects/market-study-knowledge
git add -A
git commit -m "crawler-sync: $(date +%Y-%m-%d) knowledge update" || true
git push origin main
```

2. Write today's date:
```bash
date +%Y-%m-%d > /Users/filipozbolt/Projects/market-study-knowledge/.last-sync
```

3. Report using this exact format:

---
**ms-rebuild complete — YYYY-MM-DD**
Lookback: `all` / N days (YYYY-MM-DD → today) | Confluence: ✅ synced / ⏭️ skipped
Aliases: N | Site files: N | New stubs: N

**Sites updated from Slack:**

| Site | Status | Summary |
|---|---|---|
| **slug** | 🔴 OPEN / 🟡 WATCH / ⚠️ PENDING / ✅ RESOLVED / ℹ️ INFO | One-line summary |

**Knowledge base files updated from Confluence:** (list files touched, or "None / skipped")

**Needs human review:** (list threads/pages, or "None")

Knowledge repo pushed: ✅
---

Status icons:
- 🔴 OPEN — active unresolved incident
- 🟡 WATCH / DEGRADED — recovering or needs monitoring
- ⚠️ PENDING — fix deployed but follow-up action required
- ✅ RESOLVED — fixed and confirmed working
- ℹ️ INFO — informational, no action needed

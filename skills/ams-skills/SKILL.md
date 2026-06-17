---
name: ams-skills
description: ALWAYS invoke this skill when the user's message is "ams-skills" or "ams-skills update", or asks "what skills do we have", "list skills", "show available skills". Default behavior — return the formatted reference of all Market Study project skills. With `update` subcommand — scan ~/.claude/skills/ for new AMS-project skills (names starting with `ams`, `ams-`, or `crawler-`) and add any missing ones to the tables in this file.
---

# ams-skills — Project Skills Reference

Quick reference for all skills available in this Market Study project.

## AMS Domain Skills

| Skill | Trigger | Params | Purpose |
|---|---|---|---|
| `ams` | `ams <topic>` | topic: any AMS concept | General AMS architecture, pipelines, queues, proxies, ScrapeDo, SVL, deploys |
| `ams-health` | `ams-health [env]` | env: `prod`\|`stage`\|`local` (default: prod) | RabbitMQ healthcheck — queue traffic-light table, DL drill-down, alert summary |
| `ams-on-call` | `ams-on-call [N] [--threshold=T] [--site=S]` | N: days to check (1–7, default: 1=today); T: drop threshold % (default: 5); S: filter to one site | Daily crawl anomaly detector — sites with 0 vehicles or >threshold% drop vs prev/avg7/med7 baselines |
| `ams-s3` | `ams-s3 <input> [env] [flags]` | input: URL or 32-char storeId; env: `prod`\|`stage`\|`local` (default: prod); flags: `--write=<file>`, `--delete`, `--rent`, `--dealer`, `--deleted`, `--general`, `--date=YYYYMMDD`, `--body='{...}'`, `--yes`, `--yes-general` | Fetch raw HTTP response (daily cache) or stored vehicle/dealer JSON from S3. Replaces the legacy s3-file-fetcher-gui. Write/delete on stage and local only — HARD REFUSED on prod. |
| `ams-save` | `ams-save` | — | End-of-session harvest of new facts, corrected assumptions, workflows — saves to market-study-knowledge.md / memory feedback files / skills |
| `ams-skills` | `ams-skills` \| `ams-skills update` | `update` subcommand: scan installed skills, auto-add new ones | This reference — lists all available skills. `update` rebuilds the tables from `~/.claude/skills/` |
| `ams-address-pr` | `ams-address-pr <PR-URL-or-number> [--fix]` | PR URL or number; `--fix` to apply fixes directly | Fetches open reviewer comments from a PR, cross-references code-standards.md, suggests fixes or implements them |
| `ams-export-chat` | `ams-export-chat [-briefly\|-full]` | `-briefly` (default): structured summary; `-full`: verbatim dump | Saves the current conversation to two locations: `market-study/chat-exports/` (gitignored) and `~/Projects/market-study-chat-exports/` (backup) |

## Crawler Skills

| Skill | Trigger | Params | Purpose |
|---|---|---|---|
| `crawler-info` | `crawler-info <site>` | site: any site key (e.g. `otomoto`, `autoscout-nl`) | Per-site on-call briefing — architecture, quirks, known issues |
| `crawler-debug` | `crawler-debug <site>` | site: site key | End-to-end failure investigation — alerts, queues, S3/ES mismatch, zombie vehicles |
| `crawler-data-validation` | `crawler-data-validation <site> [env] [--sample=N]` | site: site key; env: `local`\|`stage`\|`prod`; sample: 1–20 | Data quality audit — URL, enum, numeric, flag, price checks |
| `crawler-test-flow` | `crawler-test-flow <site> [--paginate]` | site: site key; `--paginate` optional | Local-only end-to-end crawler flow test — green/red per pipeline phase (getBrandsAndModels → listing → parseVehicleInput → parseEquipment → parseDealer). Refuses to run against stage/prod. Does NOT validate data quality. |
| `crawler-fix` | `crawler-fix <site>` | site: site key | Full repair loop — gather problem (or call crawler-debug if unknown) → match failure-patterns → implement fix per playbook → commit → verify with crawler-test-flow |
| `crawler-create` | `crawler-create` (invoked before implementing a new crawler) | — | Step-by-step guide for adding a new crawler site — site recon, WAF/proxy decision, listings-only vs detail, file checklist, SiteKey/CrawlingSites/module registration, pagination patterns |
| `crawler-security` | `crawler-security <site>` | site: site URL or key | Security assessment for a new crawl candidate — robots.txt, curl, proxy, Postman, cookies, Puppeteer, ScrapeDo tiers, provider detection; produces a validation table row |
| `crawler-sync` | `crawler-sync [days\|all] [confluence]` | days: lookback window (default: 7); `all` for full history; `confluence` to also sync M space | Rebuild knowledge base from Slack (and optionally Confluence) — sync incidents, reinstall crawler-info/debug skills |

### crawler-data-validation sub-commands

```
crawler-data-validation <site> [env] [--sample=N]   # vehicle ads
crawler-data-validation dealers <site> [env]         # dealer data
crawler-data-validation workingurl <site> [env]      # workingUrl field
```

### ams-s3 quick examples

```
ams-s3                                                       # help
ams-s3 https://www.example.com                               # READ raw response (prod, today)
ams-s3 ee315ac12567a2b44ae03fc30b093334                      # READ vehicle from prod store
ams-s3 stage <storeId> --dealer                              # READ dealer JSON from stage
ams-s3 stage <url> --write=./response.html --yes             # WRITE (stage only — prod refused)
ams-s3 local <storeId> --delete --rent                       # DELETE from local rent bucket
ams-s3 prod <url> --date=20260518                            # READ past-day daily cache
```

## When to Use Which

```
User asks about a concept (queues, ScrapeDo, deactivation)?     → ams <topic>
User asks about queue health or DL alerts?                      → ams-health [env]
Daily on-call check — which sites crawled 0 or dropped?         → ams-on-call [N]
User wants raw S3 response or stored vehicle JSON?              → ams-s3 <input>
User at end of session — capture new findings?                  → ams-save
User wants a briefing before touching a site?                   → crawler-info <site>
Site didn't crawl / prepared 0 / DL queue spike?                → crawler-debug <site>
Post-crawl data quality check or field-level issue?             → crawler-data-validation <site>
Verify a single crawler runs end-to-end locally?                → crawler-test-flow <site>
Crawler broken and need a full fix (diagnosis → code → verify)? → crawler-fix <site>
Adding a brand-new crawler for a new site/source?               → crawler-create
Assessing security / bot protection of a new candidate site?    → crawler-security <site>
Knowledge base outdated / new Slack incidents?                  → crawler-sync [days]
Added a new skill and want it listed here?                      → ams-skills update
PR has reviewer comments to address?                            → ams-address-pr <PR-URL> [--fix]
Export / save / share this conversation?                        → ams-export-chat [-briefly|-full]
```

## ams-health Details

| Command | Env |
|---|---|
| `ams-health` | prod |
| `ams-health stage` | stage |
| `ams-health local` | local |
| `ams-health sync` | Sync cron snapshots from Slack into history baselines |

## `ams-skills update` — runbook

When invoked as `ams-skills update`, **do NOT print the reference above**. Instead, follow these steps:

### Step 1 — List installed AMS-project skills

```bash
for d in ~/.claude/skills/*/; do
    name=$(basename "$d")
    case "$name" in
        ams|ams-*|crawler-*) echo "$name" ;;
    esac
done | sort
```

### Step 2 — Diff against the current tables

Extract skill names already present in the "AMS Domain Skills" and "Crawler Skills" tables of this SKILL.md (the rows where the first column is a backticked skill name). Compare with the list from Step 1. Build two sets:

- **NEW** — skill exists under `~/.claude/skills/` but is not in any table
- **STALE** — skill is in a table but no longer exists under `~/.claude/skills/` (skill was uninstalled)

### Step 3 — For each NEW skill, infer table row fields

Read the SKILL.md frontmatter and body of the new skill:

```bash
SKILL_FILE=~/.claude/skills/<new-skill>/SKILL.md
```

- **Group**: starts with `ams`/`ams-` → AMS Domain table. Starts with `crawler-` → Crawler table.
- **Trigger pattern**: scan the frontmatter `description:` for the canonical invocation form (look for patterns like `"<name>"`, `"<name> <arg>"`, `"<name> [arg]"`, often in quoted examples or "trigger" phrasing).
- **Params**: extract from the trigger pattern + any `## Params`, `## Invocation forms`, or argument table in the body.
- **Purpose**: a one-line summary derived from the first paragraph after the heading. Keep it ≤ 1 line in the table.

If any field is genuinely unclear from the SKILL.md, surface that field as `<TBD — fill in>` rather than guessing. The user can refine after.

### Step 4 — Apply edits

For each NEW skill, use the `Edit` tool to insert the new row at the bottom of the appropriate table (just before the table's closing line). For each STALE skill, remove its row.

If both copies exist (canonical at `~/.claude/skills/ams-skills/SKILL.md` and, if the repo convention is followed, `~/Projects/market-study-knowledge/skills/ams-skills/SKILL.md`), update **both** in the same flow so they stay in sync.

### Step 5 — Update the "When to Use Which" cheat-sheet

For each NEW skill, add a line to the cheat-sheet block. For each STALE skill, remove its line. Phrase it as a user-facing trigger question, e.g. `"User wants X? → <skill> <args>"`.

### Step 6 — Report

Print:

- list of NEW skills added with their rendered table rows
- list of STALE skills removed
- final count: `ams-skills now tracks N skills (M AMS Domain, K Crawler)`
- if nothing changed: `ams-skills reference is already up to date (N skills tracked)`

Never report any secrets or values from `.env` while running this update — the scan is purely over filenames and frontmatter `description:` fields.

## Notes

- `crawler-info` and `crawler-debug` are NOT interchangeable — info is a briefing, debug is an investigation.
- `ams` is for general questions; for site-specific issues always prefer `crawler-info` or `crawler-debug`.
- `crawler-test-flow` validates pipeline execution; `crawler-data-validation` validates data quality — they answer different questions.
- `ams-s3` is read-only on prod. Use stage or local for any write/delete operations.
- Superpowers skills (TDD, brainstorming, debugging, etc.) are also available but not listed here — they are general-purpose, not AMS-specific.

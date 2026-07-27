---
name: ams-skills
description: ALWAYS invoke this skill when the user's message is "ams-skills" or "ams-skills update", or asks "what skills do we have", "list skills", "show available skills". Default behavior — return the formatted reference of all Market Study project skills. With `update` subcommand — scan ~/.claude/skills/ for new AMS-project skills (names starting with `ams`, `ams-`, or `crawler-`) and add any missing ones to the tables in this file.
---

# ams-skills — Project Skills Reference

Quick reference for the skills checked into this repo.

## AMS Domain Skills

| Skill | Trigger | Params | Purpose |
|---|---|---|---|
| `ams` | `ams <topic>` | topic: any AMS concept | General AMS architecture, pipelines, queues, proxies, ScrapeDo, SVL, deploys |
| `ams-save` | `ams-save` | — | End-of-session harvest of new facts, corrected assumptions, workflows — saves to market-study-knowledge.md / memory feedback files / skills |
| `ams-skills` | `ams-skills` \| `ams-skills update` | `update` subcommand: scan installed skills, auto-add new ones | This reference — lists all available skills. `update` rebuilds the tables from `~/.claude/skills/` |
| `ams-address-pr` | `ams-address-pr <PR-URL-or-number> [--fix]` | PR URL or number; `--fix` to apply fixes directly | Fetches open reviewer comments from a PR, cross-references code-standards.md, suggests fixes or implements them |
| `ams-export-chat` | `ams-export-chat [-briefly\|-full]` | `-briefly` (default): structured summary; `-full`: verbatim dump | Saves the current conversation to two locations: `market-study/chat-exports/` (gitignored) and `~/Projects/market-study-chat-exports/` (backup) |
| `ams-find-vehicle` | `ams-find-vehicle <url-or-storeId> [site]` | url or storeId; site key optional | 5-phase trace for a missing vehicle across ES/S3/Graylog. Stage/local only — prod explicitly forbidden. |
| `ams-open-ticket` | `ams-open-ticket` | — | Creates a Jira ticket in the `MAR` project following house style — bold+code inline, ad examples, screenshots, Slack refs, acceptance criteria checklist |

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
| `crawler-estimate-credit-cost` | `crawler-estimate-credit-cost <site>` | site: site key | Estimates the minimum ScrapeDo credits a Market Study crawler site would cost per day, whether it currently uses ScrapeDo or not |

### crawler-data-validation sub-commands

```
crawler-data-validation <site> [env] [--sample=N]   # vehicle ads
crawler-data-validation dealers <site> [env]         # dealer data
crawler-data-validation workingurl <site> [env]      # workingUrl field
```

## When to Use Which

```
User asks about a concept (queues, ScrapeDo, deactivation)?     → ams <topic>
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
Vehicle missing from search results?                             → ams-find-vehicle <url-or-storeId>
Need to open a Jira ticket?                                     → ams-open-ticket
Estimate ScrapeDo cost for a candidate site?                    → crawler-estimate-credit-cost <site>
```

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

Before treating a NEW skill as belonging in **this** repo's table, confirm its directory is physically present under this repo's own `skills/` folder — a skill installed locally at `~/.claude/skills/` is not automatically checked into this repo.

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

For each NEW skill that is physically checked into this repo's `skills/` folder, use the `Edit` tool to insert the new row at the bottom of the appropriate table (just before the table's closing line). For each STALE skill, remove its row.

The canonical, full-scope reference lives at `~/.claude/skills/ams-skills/SKILL.md` — it lists every locally-installed AMS/crawler skill regardless of which repo (or no repo) backs it. This repo's copy is scoped only to skills physically present under `market-study-knowledge/skills/`; do not blindly mirror the canonical file's full table here — filter first.

### Step 5 — Update the "When to Use Which" cheat-sheet

For each NEW skill added to the table, add a matching line to the cheat-sheet block. For each STALE skill, remove its line. Phrase it as a user-facing trigger question, e.g. `"User wants X? → <skill> <args>"`.

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
- Superpowers skills (TDD, brainstorming, debugging, etc.) are also available but not listed here — they are general-purpose, not AMS-specific.

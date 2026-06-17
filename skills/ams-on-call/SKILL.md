---
name: ams-on-call
description: ALWAYS invoke when user message starts with "ams-on-call" — e.g. "ams-on-call", "ams-on-call 3", "ams-on-call 7 --threshold=10", "ams-on-call --site=otomoto". Checks daily crawl counts in Elasticsearch and reports sites that got 0 vehicles or dropped more than a threshold percent. Also triggers on "/ams-on-call".
---

# ams-on-call — Daily Crawl Anomaly Detector

## Trigger

| Command | Behavior |
|---|---|
| `ams-on-call` | Check today, 5% threshold |
| `ams-on-call N` | Check last N days merged report (max 7), 5% threshold |
| `ams-on-call N --threshold=T` | Check N days, T% threshold |
| `ams-on-call --site=<site>` | Filter to one site |
| `ams-on-call N --site=<site> --threshold=T` | All combined |

## Steps

### 1. Run the check script

```bash
python3 ~/.claude/skills/ams-on-call/check.py [DAYS] [--threshold PCT] [--site NAME]
```

Pass through all args from the user's command. Examples:
- `ams-on-call` → `python3 ~/.claude/skills/ams-on-call/check.py`
- `ams-on-call 3` → `python3 ~/.claude/skills/ams-on-call/check.py 3`
- `ams-on-call 7 --threshold=10` → `python3 ~/.claude/skills/ams-on-call/check.py 7 --threshold=10`
- `ams-on-call --site=otomoto` → `python3 ~/.claude/skills/ams-on-call/check.py --site=otomoto`

### 2. Print the output

Print the report exactly as returned by the script. No reformatting needed.

### 3. Handle errors

| Error message | Action |
|---|---|
| `Are you on VPN?` | Stop. Tell user to connect VPN and retry. |
| `ES credentials not found` | Stop. Tell user the `.env` line is missing. |
| `Site "X" not found` | Stop. Print the known sites list from the error. |

### 4. If 🔴 issues found

After printing the report, offer two actions per flagged site:

> "Want me to investigate any of these? For each site I can run:
> - `crawler-debug <site>` — full failure investigation (logs, queues, S3/ES mismatch)
> - `crawler-test-flow <site>` — quick local end-to-end run to confirm if crawler still works"

List each 🔴 flagged site with both options so the user can pick.

## What the script checks

- **0 vehicles**: site should have crawled that day (per `CrawlingSites.ts` schedule) but ES shows 0
- **Drop >threshold%**: count vs three baselines — last eligible run, avg of last 7 eligible runs, median of last 7
- Sites that are `isDisabled` or not scheduled for the checked day are silently skipped

## Requirements

- VPN required (ES is on AWS)
- Credentials auto-read from commented `ELASTIC_SEARCH_URL` line in `/Users/filipozbolt/Projects/market-study/.env`
- Schedule data from `src/shared/const/CrawlingSites.ts` — no manual maintenance needed
- Pure stdlib Python 3 — no pip installs
- **Need an ES query not in the script?** Check [Useful ElasticSearch queries](https://preskok.atlassian.net/wiki/spaces/M/pages/2677997569/Useful+ElasticSearch+queries) on Confluence, `src/database/elastic-search/elastic-search.service.ts` for patterns, or ask the user for their Kibana saved-queries export

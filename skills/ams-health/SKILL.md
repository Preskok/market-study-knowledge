---
name: ams-health
description: ALWAYS invoke when user message is "ams-health" optionally followed by "prod", "stage", or "local". Default env is prod. Performs a MarketStudy RabbitMQ healthcheck — traffic-light queue table, DL queue drill-down, Outlook alert summary if MCP configured, verdict paragraph, and feedback improvement prompt. Also triggers on "/ams-health".
---

# ams-health — MarketStudy RMQ Healthcheck

## Trigger

| Command | Environment |
|---|---|
| `ams-health` | prod (default) |
| `ams-health prod` | prod |
| `ams-health stage` | stage |
| `ams-health local` | local |
| `ams-health sync` | Sync cron snapshots from Slack into history canvas baselines |

## Sync command (`ams-health sync`)

When user types `ams-health sync`:
1. Read `~/.claude/skills/ams-health/config.json` → get `historyCanvas` ID and `slackBotToken`.
2. Download canvas HTML (see Canvas API helpers below) → parse all `<p class="prettyprint line">` entries after the `## Raw Data` h2.
3. Deduplicate: for each (date, slot), keep only the **last** entry by timestamp. Slot = `"0700"` if hour < 8, else `"1000"`.
4. Compute slot-based baselines per `~/Projects/market-study-knowledge/anomaly-rules.md` (Baseline computation section). Use `/tmp/compute_baselines_slotted.py` if available, otherwise run inline Python.
5. Update Baselines section via canvas replace (see Canvas API helpers below).
6. Trim Raw Data to last 60 lines if >60 (count raw lines only, not the baselines line).
7. Print: "✅ Sync complete — N unique runs (0700: A, 1000: B), baselines updated."
Stop after sync — do not run the full healthcheck.

## Steps — follow in order every run

### 1. Load config

Read `~/.claude/skills/ams-health/config.json`. Extract `envs[ENV]` for the requested env.

If file missing or env block missing:
```
❌ Config not found at ~/.claude/skills/ams-health/config.json
Create it with blocks for prod / stage / local — see SKILL.md header for schema.
```
Stop.

### 2. Auth check

```bash
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -u "USER:PASS" "URL/overview")
echo $STATUS
```

Replace USER, PASS, URL with values from config. If not `200`: print
```
❌ Cannot reach ENV RMQ (URL). HTTP STATUS. Check VPN / credentials.
```
Stop.

### 3. Fetch queues

```bash
curl -s -u "USER:PASS" "URL/queues" | jq '[
  .[] | select(.name | startswith("MS_")) |
  {
    name,
    vhost,
    messages: (.messages // 0),
    messages_ready: (.messages_ready // 0),
    messages_unacknowledged: (.messages_unacknowledged // 0),
    consumers: (.consumers // 0)
  }
] | sort_by(-(.messages))'
```

Store result as the queue list.

### 3.5. Read history baselines

Load `historyCanvas` and `slackBotToken` from `~/.claude/skills/ams-health/config.json`.

If `historyCanvas` is missing or null: skip this step and all anomaly steps (history not set up).

Read the canvas content using the Canvas API helper (see **Canvas API helpers** section below).

Extract the JSON content from the `## Baselines` code block. Parse as `baselines` object.

If canvas read fails for any reason: print `⚠️ Baselines unavailable — canvas read failed, anomaly detection skipped this run.` and skip all anomaly steps.

Determine current slot: run `date +%H` → `current_slot = "0700" if hour < 8 else "1000"`.
Set `slot_baselines = baselines.slots[current_slot]`.

If `slot_baselines.total_runs < 14`: note "learning mode" — will print learning notice instead of anomaly alerts.

For stuck detection (Rule 2): extract all raw data lines, filter to `current_slot` only, take last 3.

### 4. Apply rules

Read `~/Projects/market-study-knowledge/queue-health-rules.md`. For each queue:
- Check for exact `## QUEUE_NAME` block. If found, apply its rule.
- If no exact match, apply `## DEFAULT` rule.
- For time-aware rules (MS_WEEKLY, MS_HUNGARY): run `date +%u` (day 1=Mon…7=Sun) and `date +%H%M` (HHMM) to get current time before evaluating.
- Result: 🟢 / 🟡 / 🔴 + note string.

### 5. Build and render the table

Print header:
```
# AMS health — ENV — YYYY-MM-DD HH:MM CEST
```
(Get timestamp: `date '+%Y-%m-%d %H:%M %Z'`)

Print table with top 15 queues sorted by `messages` descending:

```
## Queues (N MS_* of TOTAL total — sorted by messages)

| Status | Queue | Messages | Unacked | Consumers | Note |
|--------|-------|:--------:|:-------:|:---------:|------|
| 🟢 | MS_EXAMPLE | 4,783 | 2 | 2 | active crawl |
…
```

For queues beyond position 15 with `messages == 0`: collapse as one line:
```
+ N more (all 🟢, 0 messages)
```

For queues beyond position 15 with `messages > 0`: always include in table regardless of position (never collapse non-zero queues).

### 6. DL drill-down

For each queue where `name` ends with `_DL` AND `messages > 0`:

```bash
curl -s -u "USER:PASS" \
  -X POST "URL/queues/MS/QUEUE_NAME/get" \
  -H "Content-Type: application/json" \
  -d '{"count": 10, "ackmode": "ack_requeue_true", "encoding": "auto"}' \
  | jq '[.[] | {
      origin: (try .properties.headers."x-death"[0].queue catch "unknown"),
      body: (.payload[:60])
    }]'
```

Note: vhost is `MS` for all MarketStudy queues.

Render as subsection immediately below the main table:

```
## MS_DL contents — 47 messages (sample: first 10)

| # | from queue | first 60 chars |
|---|------------|----------------|
| 1 | MS_GENERAL_LISTING_URLS_TO_FETCH | https://www.otomoto.pl/osobowe/audi/a4/… |
```

### 6.5. Anomaly detection

If history was loaded in Step 3.5:
- If `slot_baselines.total_runs < 14`: print `⏳ Learning... (N/14 runs for SLOT slot before anomaly detection)` and skip to next step.
- Otherwise: apply all rules from `~/Projects/market-study-knowledge/anomaly-rules.md` against current queue states and `slot_baselines` (the slot-specific baselines from Step 3.5).
- If any anomalies found: render `## ⚠️ Anomaly Alerts` section immediately above `## Verdict`.
- If no anomalies: do not add the section.

### 7. Outlook check

Check whether any available MCP tool name contains "mail", "message", or "outlook" (case-insensitive).

- If found: query last 12 hours for emails from `graylogprod@b2b-carmarket.com` and `system@preskok.si`. Group by subject pattern (from `~/Projects/market-study-knowledge/alert-emails.md` if available). Show: sender, count, most recent timestamp.
- If not found: print:
```
## Email alerts (last 12h)
📧 Outlook MCP not configured — see ~/Projects/market-study-knowledge/outlook-mcp-setup.md
```

### 8. Verdict

Write a 2–4 sentence verdict paragraph:

```
## Verdict
```

- Count 🔴 queues → name each, state required action (from rule's Action field).
- Count 🟡 queues → name each, state what to watch.
- If all 🟢: "All queues nominal."

### 9. Feedback prompt

Print:
```
---
💬 **Want to improve these rules?**
Type your feedback directly in the chat (e.g. "MS_BULK_DL should be 🟢 if <2000", "ignore MS_HUNGARY in mornings") and I'll update the rule file.
Type `skip` to end.
```

Then wait for the user's next message.

If user replies with anything other than `ok` / `skip` / `good` / `looks good` / `fine`:
1. Parse intent into a concrete rule change.
2. Show proposed diff (old line → new line in queue-health-rules.md).
3. Ask: "Apply this change?"
4. If confirmed: overwrite `~/Projects/market-study-knowledge/queue-health-rules.md` with the change.
5. Print: "⚠️ Rules updated locally. Reply `sync rules to cron` to push changes to both scheduled tasks (07:00 + 10:00)."

If user replies `sync rules to cron`:
- Follow protocol in `~/Projects/market-study-knowledge/feedback-loop.md` → update both scheduled tasks via `mcp__scheduled-tasks__update_scheduled_task`.

### 9.5. Append snapshot to canvas

After all output is rendered and feedback is handled:

1. Build snapshot line:
```bash
TS=$(date -u +"%Y-%m-%dT%H:%M+02:00")
# Build JSON: {"ts":"TS","src":"local","q":{"MS_DL":[0,0],...}}
# Include all MS_* queues from step 3 result: [messages, consumers]
```

2. Read canvas → get section_id for the Raw Data code block (see **Canvas API helpers** below).
3. Append the new JSONL line to the Raw Data section using the canvas update curl helper.
4. If Raw Data now has >60 lines: read full Raw Data, trim to last 60 lines, replace entire Raw Data section.
5. If any canvas call fails: print `⚠️ Snapshot not saved — canvas write failed.` and continue (non-fatal).

## Canvas API helpers

Use these `curl` commands instead of the Slack MCP for all canvas operations.
`TOKEN` = `slackBotToken` from config.json. `CANVAS_ID` = `historyCanvas` from config.json.

### Read full canvas content (primary method)
```bash
# Get team_id from auth.test if unknown
curl -s -H "Authorization: Bearer TOKEN" https://slack.com/api/auth.test | jq -r '.team_id'

# Download canvas HTML (CANVAS_ID starts with F, team_id e.g. T8CK920BS)
curl -s -L "https://files.slack.com/files-pri/TEAM_ID-CANVAS_ID/canvas" \
  -H "Authorization: Bearer TOKEN"
```
The response is HTML. Sections appear as `<p class="prettyprint line">CONTENT</p>`.
- `## Baselines` is in the `<h2>` preceding the first prettyprint paragraph.
- Parse each `<p class="prettyprint line">` after the `## Raw Data` h2 as a JSONL line (some may be `(empty)` — skip those).

For the team_id, use the hardcoded value from auth.test if already known (e.g. `T8CK920BS` for preskok).

### Read section IDs (needed for updates)
```bash
curl -s -X POST "https://slack.com/api/canvases.sections.lookup" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"canvas_id":"CANVAS_ID","criteria":{"section_types":["h2"]}}'
```
Returns IDs for h2 headings. Match by position: first h2 = Baselines section, second h2 = Raw Data section.
Get the paragraph section IDs from the HTML (the `id=` attribute on each `<p>` tag).

### Update (replace) or append to a canvas section
**Always use `python3` for canvas writes** — shell heredocs break on nested JSON quotes.

```python
import json, subprocess

payload = {
    "canvas_id": "CANVAS_ID",
    "changes": [{
        "operation": "replace",          # or "insert_after" to append
        "section_id": "SECTION_ID",
        "document_content": {
            "type": "markdown",
            "markdown": "NEW_CONTENT"    # plain string, no extra escaping needed
        }
    }]
}

result = subprocess.run(
    ["curl", "-s", "-X", "POST", "https://slack.com/api/canvases.edit",
     "-H", "Authorization: Bearer TOKEN",
     "-H", "Content-Type: application/json",
     "-d", json.dumps(payload)],
    capture_output=True, text=True
)
print(result.stdout)
```

- Use `"replace"` to overwrite a section (e.g. Baselines code block).
- Use `"insert_after"` with the **last paragraph's section_id** (from the HTML `id=` attribute) to append a new line at the bottom of Raw Data.
- The Baselines section_id is the **first** h2 id; Raw Data is the **second** h2 id.

Check `"ok": true` in every response. On failure, log the `error` field and treat as non-fatal (skip anomaly detection or snapshot, but continue the healthcheck).

## Config schema (for reference)

```json
{
  "envs": {
    "prod":  { "url": "", "user": "", "pass": "" },
    "stage": { "url": "", "user": "", "pass": "" },
    "local": { "url": "", "user": "", "pass": "" }
  },
  "default": "prod"
}
```

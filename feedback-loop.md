# Feedback Loop Protocol

After each `ams-health` run, Claude asks: "💬 Improve these rules? Reply with feedback or skip."

## If user gives feedback

1. Parse the feedback into a concrete rule change (queue name + threshold + status).
2. Show the user a proposed diff:
   ```
   Change in queue-health-rules.md:
   ## MS_BULK_DL
   - OLD: 🟡 = 500 ≤ messages ≤ 5000
   + NEW: 🟡 = 2000 ≤ messages ≤ 5000
   ```
3. Ask: "Apply this change?"
4. If yes: write the updated `queue-health-rules.md`.
5. Print: "⚠️ Rules updated locally. To sync to the daily cron, reply `sync rules to cron`."

## If user replies "sync rules to cron"

1. Read the current `references/queue-health-rules.md`.
2. Update both scheduled tasks:
   - Load `mcp__scheduled-tasks__update_scheduled_task` via ToolSearch.
   - Update `ams-health-0700` prompt: replace the RULES BLOCK section with new rules.
   - Update `ams-health-1000` prompt: same.
3. Confirm: "✅ Rules synced to both scheduled tasks (07:00 + 10:00)."

## If user says "ok" / "skip" / "good" / "looks good"

No action. Session ends.

---
name: ams-export-chat
description: ALWAYS invoke this skill when the user says "ams-export-chat", "export this chat", "save this session", "export this investigation", "export this conversation", "save this debug session", "share this with the team", or any similar phrase requesting the current conversation be saved or exported. Works for any type of session — debugging, feature work, code changes, on-call, architecture discussions. Must be invoked BEFORE generating any summary text.
---

# ams-export-chat — Market Study Chat Exporter

Saves the current conversation to disk in two locations so nothing is lost even if the repo is deleted.

---

## Step 1 — Ask for the file name

Before writing anything, ask the user:

> What should I name this export? (e.g. `otomoto-linting-revert`, `ams-health-investigation`, `mar-1975-url-migration`)

Wait for the answer. The filename will be: `YYYY-MM-DD_{user-provided-name}.md`

Use today's date (from the session context or `date +%Y-%m-%d`).

---

## Step 2 — Determine export mode

Check if the user's message contains `-full` or `-briefly`:

- **`-full`** — verbatim export: write the entire conversation turn-by-turn, no summarization
- **`-briefly`** or no flag — structured summary (default): fill in the adaptive template below

---

## Step 3 — Write both files

Write the export to **both locations** using the same filename:

| Location | Path |
|----------|------|
| Project (gitignored) | `/Users/filipozbolt/Projects/market-study/chat-exports/YYYY-MM-DD_{name}.md` |
| Backup (outside repo) | `/Users/filipozbolt/Projects/market-study-chat-exports/YYYY-MM-DD_{name}.md` |

Create the backup directory if it doesn't exist (`mkdir -p`).

Tell the user both paths after writing.

---

## `-briefly` template (structured summary)

Use this when no `-full` flag is given. Include the universal sections always. Include the optional sections **only if that content actually appeared in the conversation** — the comment after each `←` is guidance, not literal text.

Bias toward including more rather than less. Omit a section only when truly nothing relevant happened (e.g. no commits were made → no Commits section).

```markdown
# AMS Chat Export: <descriptive topic title>

**Date:** YYYY-MM-DD
**Ticket / branch:** <MAR-XXXX or branch name if mentioned, otherwise omit>
**Skills used:** <comma-separated list of ams/crawler skills that were invoked>
**Model:** <model name from session>

## Context
<1-2 sentences: what problem, task, or question prompted this session and what the goal was.
Be concrete — name the site, ticket, or feature. A new reader should understand why this chat happened.>

## Attachments                      ← only if files, images, or S3/Graylog dumps were shared
| Type | Name / Description | Role in conversation |
|------|-------------------|----------------------|
| S3 response | storeId ee315ac1… | Raw cached HTML showing 403 DataDome block |

## Key Findings
- <Most important discovery, decision, or outcome — one bullet per thing>
- <Second most important — don't summarize, just list>

## Comparison / Data Tables         ← only if tables appeared; preserve verbatim
<Copy any markdown tables from the conversation exactly as they appeared>

## Code / Changes Produced          ← only if non-trivial code was written or reviewed
<Relevant snippets, diffs, or file changes — not every line, just what matters>

## Commits Made                     ← only if commits happened during this session
| Hash | Message |
|------|---------|
| `abc1234` | [MAR-1975][B] revert linting changes from otomoto service |

## Investigation Summary            ← only if systems were actively queried (RMQ/ES/S3/Graylog/curl)
| System | What was checked | Finding |
|--------|-----------------|---------|
| S3 | Raw cache for 3 storeIds | 403 response — DataDome block |
| Elasticsearch | Vehicle count today vs yesterday | −42% drop |
| RabbitMQ | MS_DL queue depth | 0 messages |
| Graylog | PARSER_DEBUGGING since last deploy | 0 occurrences |

## Root Cause                       ← only for bug/incident sessions
<One paragraph explaining what actually caused the problem>

## Decisions Made                   ← only if design or approach decisions were made
| Decision | Rationale |
|----------|-----------|
| Use workingUrl override instead of rewriting storeId | avoids breaking dedup on existing vehicles |

## Verification                     ← only if tests or post-fix checks were run
<Test results, crawler-test-flow output, Graylog post-fix confirmation, etc.>

## Open Questions
<Unresolved items — omit this section if nothing was left open>

## Next Steps
<Concrete follow-up actions — omit if none>
```

---

## `-full` template (verbatim)

Write the entire conversation as-is, turn by turn. No summarization. Useful when you need a complete audit trail or want to share context that a summary would lose.

```markdown
# AMS Chat Export (Full): <topic>

**Date:** YYYY-MM-DD
**Ticket / branch:** <if mentioned>
**Model:** <model name>
**Note:** This is a verbatim export. For a structured summary, use `ams-export-chat -briefly`.

---

**User:** <exact user message>

**Assistant:** <exact assistant response>

---

**User:** <next message>

**Assistant:** <next response>

...
```

---

## Rules

1. **Write the file first, then report the paths.** Never just print to the chat.
2. **Two files always** — project location AND backup location. If either write fails, report the error but still write the other.
3. **Preserve tables verbatim** — reformatting loses alignment and meaning.
4. **Skip tool output noise** — raw bash output, intermediate retries, draft rewrites. Keep conclusions.
5. **No git commits, no pushes** — the export is just a file on disk.
6. **Note what's missing** — if the conversation included images or live terminal output that Claude can't reproduce, say so at the top: `> **Note:** This session included live terminal output that is not captured here.`
7. **Bias toward completeness** — it's better to include a section that turns out to be borderline than to lose a finding. A long export beats a lossy one.

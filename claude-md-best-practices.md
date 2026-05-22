# CLAUDE.md authoring guidelines

Rules for keeping this project's CLAUDE.md effective as it grows.

## The five principles

**1. Stay under ~200 lines.**
Files past 200 lines consume more context window and reduce instruction adherence. When a section grows beyond ~30 lines, extract it to a referenced doc (like this one).

**2. Cover WHAT, not HOW.**
CLAUDE.md is a map, not a manual. Name the files, patterns, and skills Claude needs to find. Put the detail in the thing being pointed at — a README, a skill, a knowledge-base file.

**3. Progressive disclosure.**
Tell Claude how to find information, rather than inlining the information. Prefer: `"For X, use skill Y"` or `"See docs/foo.md"`. Claude reads those files on demand; you don't need to duplicate them here.

**4. "Always do X" rules only.**
Every line should be something that must hold in every session: commands, conventions, layout, hard constraints. If it only applies sometimes, or is better learned by reading the code, leave it out.

**5. Keep auto-memory separate.**
User preferences, workflow habits, and session context belong in the memory layer (`~/.claude/projects/.../memory/`), not CLAUDE.md. CLAUDE.md is project-scoped and team-visible; memory is personal and session-aware.

**6. Never include secrets or sensitive values.**
CLAUDE.md is checked into version control. Never put tokens, passwords, API keys, or hardcoded local credentials (even placeholder "default" dev values) directly in CLAUDE.md or any doc it references. Instead: point to the file where credentials are stored (e.g. `.env`, `http-client.private.env.json`), or point to the skill/README that explains how to obtain them. The same rule applies to any doc linked from CLAUDE.md — if Claude reads it, it's effectively in context and should contain no secrets.

## Site file authoring conventions

Site files live in `references/sites/<slug>.md`. Follow these rules when writing or editing them:

**History entries — newest first, dated, incident-style:**
```
- **2026-05-14** — what happened + outcome.
```

**Auto-expiry rule — entries > 18 months old move to `## Old history` section at the bottom of the file.** Cutoff = today minus 18 months. Timeless quirks (no specific date, no incident) stay in the main history section regardless of age. Old history is still useful for pattern matching — it just shouldn't dominate the top of the file.

**Status line** — always keep `## Current status` current. Use one of:
- `🟢 Healthy — last verified YYYY-MM-DD`
- `🟡 Degraded — [reason]`
- `🔴 Broken — [reason + ticket]`
- `⛔ Disabled — [reason]`
- `_Unknown — check Slack._` (when you genuinely don't know)

**Update `_index.md`** when status changes for a site. The index is the fast-triage entry point for `crawler-debug`.

## Signs this file needs a trim

- A section describes how to do something step-by-step (→ extract to docs/)
- A section names a specific site or incident (→ move to knowledge base)
- A rule is already enforced by a linter or type-checker (→ delete it)
- Two sections say the same thing differently (→ merge or delete one)

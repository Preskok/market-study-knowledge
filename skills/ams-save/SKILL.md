---
name: ams-save
description: ALWAYS invoke this skill when the user's message starts with "ams-save". Harvests the current conversation for reusable knowledge — new facts, corrected assumptions, new workflows — and saves them to the right destination (market-study-knowledge.md, memory feedback files, or skills).
---

# ams-save — Session Knowledge Harvester

Extracts durable knowledge from the current conversation and writes it to the right destination so future sessions are faster and require fewer messages.

## When to invoke

- User types `ams-save` (with or without arguments)
- Optionally: `ams-save [hint]` — a topic hint to narrow focus

## What to harvest

Scan the **entire conversation** (from first message to now) and collect items in six buckets:

| Bucket | What qualifies | Where it goes |
|--------|---------------|---------------|
| **AMS facts** | Operational truth about AMS systems — schedules, index names, queue rules, pipeline behavior, thresholds | `~/Projects/market-study-knowledge/market-study-knowledge.md` |
| **Code standards / patterns** | Coding conventions reinforced or corrected in this session — logger structure, naming, type usage, control flow patterns, DTO patterns. Anything a future Claude would write differently if it had read the rule. | `~/Projects/market-study-knowledge/code-standards.md` (Part 2 — Project-specific patterns) |
| **Corrections** | Something Claude assumed wrong — user-corrected OR silently self-corrected mid-session | Project memory as a `feedback_*.md` file |
| **Skill pitfall hits** | A pitfall that burned time during a skill invocation and is NOT already in that skill's pitfall table | Edit that skill's pitfall table directly |
| **Workflows** | A multi-step process that came up, worked, and isn't documented | New or updated skill in `~/.claude/skills/` |
| **Context / decisions** | One-off project decisions, deadlines, constraints that shaped this work | Project memory as a `project_*.md` file |

**Code standards vs. Corrections** — both come from user feedback, but:
- **Correction** = a one-off mistake about a fact ("the token is `abcd` not `asdf`"). Goes to feedback file.
- **Code standard** = a *pattern* that should be applied broadly ("logger always uses multi-line structured object first"). Goes to code-standards.md.

If the user said it twice, or said it once and it's clearly a style/structural rule, treat it as a code standard.

**Quality gate — save only if ALL of these are true:**
- A fresh Claude instance would waste ≥ 2 extra messages or ≥ 5 minutes getting this wrong without it
- It is NOT inferable from reading the code or existing docs
- It is NOT site-specific trivia (those go in `~/Projects/market-study-knowledge/sites/<site>.md`, not the general knowledge-base files)

**Skip:** minor details, things obvious from code, site-specific quirks already in per-site files, pitfalls that only apply to one site, anything that doesn't pass the quality gate above. When in doubt, don't save — a lean .md is more useful than a bloated one.

### Expanded scan triggers — don't miss these

After the broad scan, do a second pass with these specific questions:

**Silent self-corrections** (missed by "Corrections" bucket otherwise):
- Did Claude try something, get 0/unexpected results, and adapt? (e.g. brand filter returned 0 → checked ES → found real brand name)
- Did a system behave differently from what the skill assumed? (e.g. LocalStack returning malformed XML)
- Did an identifier/key that looked right turn out wrong? (e.g. aliases.json slug ≠ AdSiteKeysEnum for API call)

**Skill gap scan** (for every skill invoked in the session):
- Did any pitfall hit that isn't already in that skill's pitfall table?
- Did any step in the skill need to be adjusted/added? (e.g. Phase 7 missing server kill)
- Did any assumption in the skill prove false on this site?

**Infrastructure steps Claude took**:
- Did Claude start a process, service, or server? → add to skill's cleanup phase
- Did Claude make a temporary change outside the standard mod set? (e.g. `matchingDay` in CrawlingSites.ts) → add as pitfall with revert instruction
- Did Claude do something the user would expect to be automatic next time?

**New skills created this session**:
- Was a new `~/.claude/skills/crawler-*/` or `~/.claude/skills/ams-*/` skill written? → **Always** update all three of these as the **last save step**:
  1. `ams-skills/SKILL.md` — add table row + When to Use Which line
  2. `~/Projects/market-study/CLAUDE.md` — add row to the Available Skills table
  3. `README-adding-sources.md` — add a skill mention if it's a crawler workflow skill

**Code standards scan** — THREE passes. This is the most important bucket. Be aggressive — it is better to save too much than too little here.

**Pass A — known pattern types** (examples, not exhaustive):
- logger format correction (multi-line/inline, object/string, context choice)
- generic → descriptive variable rename
- logic moved between layers (controller/service/repository, inline/typed const)
- DTO validator stacking (`@IsDefined()` + `@IsBoolean()` etc.)
- `Date.now()` → `DateHelper` substitution
- pushback on defensive code (try/catch with no real failure mode, null guards masking bugs, `?.` on guaranteed keys)
- control-flow shape preference (`if (cond) { work }` vs `if (!cond) continue; work`, if/else vs early return for no-ops)
- inline type extracted to named interface file
- imported type required to be used explicitly
- naming conventions (`<noun>Raw`/`<noun>`/`<noun>Stringified`, repository-per-entity, file-per-domain, exception variable `ex` not `e`/`err`)
- method ordering (new methods at bottom of service file, pre-existing methods untouched)
- service timing pattern (`const start = Date.now()` → `durationMilliseconds` in finish log)
- Graylog field reuse (`errorMessage`, `count`, `durationMilliseconds` — never introduce new fields)
- alert email subject distinctiveness (critical alerts need unique, scannable subjects)
- no try/catch around operations that don't need it (email sends, etc.)
- param that always has one value → compute inside the method, don't pass it
- timestamp format consistency (`DateHelper.toISOString`, not UTC format strings)
- don't commit dev artifacts (`.gitignore` personal entries, dangerous `.http` endpoints)
- live config (CrawlingSites) over DB columns for site configuration

**Pass B — open scan for anything not covered above.** For every user message in the session, ask:
- Did the user push back on a stylistic or structural choice that isn't in Pass A's list?
- Did the user use phrases like "always", "never", "for future", "should be", "we typically", "from now on", "the pattern is", "we usually do"?
- Did the user reject an approach I picked and substitute a different one?
- Did the user reference an existing project convention I should have known? (file location, helper, decorator, etc.)
- Was the same correction made more than once in the session?
- Did a reviewer (mlencek or others) say "we usually do X" or "like we do elsewhere"? → That is ALWAYS a code standard.

If yes to any → it's a new code standard. Create a new `### <rule name>` section in Part 2. Don't shoehorn it into an existing entry.

**Pass C — cross-reference PR comments against codebase.** If a PR review was discussed:
- For each reviewer comment saying "we usually/typically do X": search the codebase for an existing example of X and save the pattern.
- For each "why didn't you use Y?" comment: Y is almost always an existing convention — save it.
- Don't assume a pattern is obvious just because it's in the codebase. If a reviewer had to point it out, it wasn't obvious enough to Claude — save it.
- Read 2–3 similar existing service files and compare against what was written. Any discrepancy that was flagged is a standard.

**Both passes** → add entries to **Part 2** of `code-standards.md`: rule (1 line) + code example + `**Source:** session YYYY-MM-DD`. No "why" prose.

**Important:** the existing list in code-standards.md is a *current snapshot*, not the universe of patterns. If a session surfaces a brand-new convention that no existing entry covers, that's the whole point of the scan — capture it. In a session with 40+ PR comments, expect to save 10–15 code standards minimum.

## Steps

### 1. Scan
Read the conversation and mentally list candidate items. For each, ask:
- Will this save tokens or messages in a future session?
- Would a fresh Claude instance get this wrong without it?
- Is it NOT already saved (check memory index + knowledge base headings)?

### 2. Categorize
Assign each item to a bucket (AMS facts / Corrections / Workflows / Context).

### 3. Save — follow the format for each bucket

#### AMS facts → market-study-knowledge.md
Read the file first, find or create a `## topic-name` section (lowercase-hyphenated).
Format:
```markdown
## topic-name

**Sub-header** — fact. fact. fact.
**Sub-header** — fact.
...
**Source:** [where you learned this — Confluence URL or "session YYYY-MM-DD"]
```
3–7 bullets, dense, no preamble. Append at end of file if new topic.

#### Code standards / patterns → code-standards.md (Part 2)
Read `~/Projects/market-study-knowledge/code-standards.md` first. Locate **Part 2 — Project-specific patterns**. Find or create a `### <short rule name>` section.
Format:
```markdown
### <Short rule name — imperative phrasing>

<1-line rule.>

```typescript
// short example, applied form only; use // BAD / // GOOD only if contrast is essential
```

**Source:** session YYYY-MM-DD.
```
No "why" prose. The rule + example should stand alone.
If the rule already exists, sharpen the wording. Don't duplicate.
Do NOT touch Part 1 (Confluence baseline) unless the user explicitly asks.

#### Corrections → project memory feedback file
File: `~/.claude/projects/<project-dir>/memory/feedback_<slug>.md`
Format:
```markdown
---
name: <short title>
description: <one-line — used for relevance matching>
type: feedback
---

<The rule itself — one clear sentence.>

**Why:** <what went wrong / what the user said>
**How to apply:** <when this kicks in>
```
Add a pointer line to `MEMORY.md`:
```
- [Title](feedback_slug.md) — one-line hook
```

#### Workflows → skill file
If the workflow is specific to AMS internals: add a new `## workflow-name` section inside an existing skill's SKILL.md.
If it's broadly reusable: create `~/.claude/skills/<name>/SKILL.md` (follow standard skill structure).
If it's a minor tweak to an existing skill: edit that skill directly.

#### Context / decisions → project memory project file
File: `~/.claude/projects/<project-dir>/memory/project_<slug>.md`
Same frontmatter format as feedback, `type: project`. Add pointer to MEMORY.md.

### 4. Report
After all saves, output a compact summary:

```
## ams-save — saved N items

| Type | Item | Destination |
|------|------|-------------|
| AMS fact | topic-name | market-study-knowledge.md |
| Code standard | rule-name | code-standards.md (Part 2) |
| Correction | feedback_slug.md | MEMORY.md |
| Workflow | skill-name | skills/ams/SKILL.md |

Nothing found for: [list any bucket with nothing]
```

If nothing qualifies, say so and explain why.

## Project directory resolution

Active market-study project memory:
`~/.claude/projects/-Users-filipozbolt-Projects-market-study/memory/`

Global (cross-project) memory:
`~/.claude/projects/-Users-filipozbolt/memory/`

Use the market-study path for AMS-specific items. Use global only for user-level preferences.

## Rules

- **Read before writing** — always read the destination file before editing it.
- **Don't duplicate** — if an entry already exists, update it rather than adding a new one.
- **Dense, not verbose** — AMS knowledge entries are bullets, not paragraphs.
- **Source line required** — every AMS fact entry must end with a `**Source:**` line.
- **One skill at a time** — if a workflow qualifies as a new skill, write and save it before moving to the next item.
- **No sensitive literals** — never write actual bucket names, account IDs, or profile names into saved files. Use env var placeholders: `$AWS_S3_BUCKET_DAILY_CACHE`, `$AWS_PROFILE`, etc. Example correct form: `AWS_PROFILE=preskok-prod aws s3 cp s3://$AWS_S3_BUCKET_DAILY_CACHE/YYYYMMDD/<hash> - | head -c 500`.
- **Credentials belong in `.env`** — if a secret key, token, password, or username came up in the session and is NOT already in `.env`, add it there (follow the existing env/comment-block pattern: `# local` / `# stage` / `# prod`). Never write credentials into reference docs, skill files, or memory files.

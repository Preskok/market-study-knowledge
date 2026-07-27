---
name: ams-address-pr
description: ALWAYS invoke when user types "ams-address-pr [PR URL/number]". Fetches all open reviewer comments on a market-study GitHub PR, cross-references them against code-standards.md, and either suggests fixes or implements them directly. Also invoke when user says "fix PR comments", "address review comments", or pastes a GitHub PR link and asks to fix/address comments.
---

# ams-address-pr — Market Study PR Comment Resolver

Fetches reviewer comments from a GitHub PR, cross-references code-standards.md, and resolves them.

**Required reading before fixing anything:**
- `~/Projects/market-study-knowledge/code-standards.md` — Part 2 (project patterns)
- `~/.claude/projects/-Users-filipozbolt-Projects-market-study/memory/feedback_phpstorm_format_on_save.md` — formatter noise rules
- `~/.claude/projects/-Users-filipozbolt-Projects-market-study/memory/feedback_lint_scope.md` — never run full lint

## Trigger

```
ams-address-pr <PR-URL-or-number> [--fix]
ams-address-pr https://github.com/Preskok/market-study/pull/21
ams-address-pr 21
ams-address-pr 21 --fix
```

- **No `--fix`** (default): suggest mode — explain what each comment requires and why, grouped by file
- **`--fix`**: implement mode — apply all addressable fixes directly to the files

## Steps

### 1. Fetch comments

```bash
# All open (non-outdated) reviewer comments — line != null means still active
gh api --paginate repos/Preskok/market-study/pulls/<N>/comments \
  --jq '.[] | select(.line != null) | {id, path, line, body, user: .user.login}'

# Also fetch review-level comments (not inline)
gh api repos/Preskok/market-study/pulls/<N>/reviews \
  --jq '.[] | select(.body != "") | {id, state, body, user: .user.login}'
```

Only work on comments with `line != null` (still pointing to current code). Outdated comments (`line: null`) are on already-changed code — skip unless user asks otherwise.

### 2. Read code standards

```bash
cat ~/Projects/market-study-knowledge/code-standards.md
```

Read **Part 2** fully. For every comment, ask: does this match an existing `### <rule name>` entry? Tag each comment as:
- **STANDARD** — violation of a documented pattern in code-standards.md (Part 2)
- **DESIGN** — architectural/design decision requiring discussion
- **QUESTION** — reviewer asking for clarification, not necessarily requiring a change
- **BUG** — functional issue

### 3. Group and prioritise

Group by file. Within each file, order: BUG → STANDARD → DESIGN → QUESTION.

For each comment output:
```
[FILE path:line] [TYPE]
Reviewer said: "..."
Fix: <1-line description of what to change>
Standard: <link to code-standards.md entry if applicable>
```

### 4. Suggest mode (default)

Print the grouped list with fix descriptions. Flag which ones are safe to auto-fix (`--fix` eligible) vs require human judgment (DESIGN/QUESTION).

### 5. Fix mode (`--fix`)

For each STANDARD and BUG comment that has a clear mechanical fix:

1. Read the file
2. Apply the fix
3. Run `npx tsc --noEmit` to verify no type errors introduced
4. Verify with `git diff <base-branch> -- <file>` that ONLY the intended lines changed — no unrelated prettier reformatting

**Critical: PhpStorm format-on-save** — the user's IDE auto-reformats files on edit. After every file edit, run:
```bash
git diff <base> -- <file> | grep "^[-+]" | grep -v "^---\|^+++" | grep -E "map\([a-z]|\) \{\}|, [a-z].*:.*,"
```
If unrelated formatting appears (arrow parens, constructor braces, single-line chains), restore the unformatted lines from the base commit:
```bash
git show <base>:<path/to/file> | grep -A3 -B3 "unrelated method"
```

Skip DESIGN and QUESTION comments — flag them for human decision with a clear summary.

### 6. Harvest new standards

After processing all comments, scan for any reviewer correction that is NOT already in `code-standards.md` Part 2:
- Reviewer said "we usually do X" or "like we do elsewhere" → new standard
- Reviewer flagged a naming, ordering, or pattern choice → new standard
- Same type of correction appeared on multiple files → definitely a new standard

For each new finding, append a `### <rule name>` entry to `~/Projects/market-study-knowledge/code-standards.md` Part 2 using the same format as existing entries (rule + example + `**Source:** session YYYY-MM-DD`).

### 7. Report

After suggest or fix mode, output:

```
## ams-address-pr summary — PR #N

Fixed (N):            list of comments addressed
Skipped/discuss (N):  list needing human judgment + 1-line reason each
New standards saved:  list of rules added to code-standards.md (or "none")
Type errors:          PASS / FAIL (with detail)
Diff clean:           YES / NO (unrelated formatting present?)
```

## Dos and Don'ts

**DO:**
- Read the actual file before every edit (`Read` tool, never assume current state)
- Check `git diff <base> -- <file>` after every edit to catch formatter noise
- Use `gh api` — all PR data is available via CLI
- Re-run `npx tsc --noEmit` after all fixes applied
- Lint only files you changed: `npx prettier --write <file>` + `npx eslint <file> --fix`

**DON'T:**
- Touch methods not mentioned in a comment — scope creep introduces unrelated diff noise
- Auto-fix DESIGN or QUESTION comments — they need human judgment
- Run `npm run lint` — it reformats 400+ unrelated files
- Assume a comment is fixed just because it's outdated (`line: null`) — check if the underlying issue was actually addressed in current code

## Common comment patterns in this repo (from MAR-2102)

| Pattern mlencek flags | Standard to apply |
|----------------------|-------------------|
| "use proper type instead of string" | Use `RunnableAdSiteKey` / `AvailableAdSiteKey` |
| "reuse `errorMessage` field" | Reuse existing Graylog log fields |
| "we usually do X elsewhere" | Check code-standards.md Part 2 for the pattern |
| "early return here?" | Use if/else for no-op guards |
| "destructure the parameters" | Destructure params — JS+TS Standards |
| "`ex` for consistency" | Exception variable always `ex` |
| "new methods at end of file" | New methods go at end of service file |
| "no `durationMilliseconds`?" | Service timing pattern |
| "this safeguard not needed" | Don't guard impossible cases |
| "don't commit this" | Don't commit dev artifacts |

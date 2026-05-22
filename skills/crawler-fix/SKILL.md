---
name: crawler-fix
description: Market Study crawler repair skill. ALWAYS invoke when the user types "crawler-fix [site]", says "fix [site]", "fix the [site] crawler", or when crawler-debug has finished its diagnosis and the conversation turns toward implementing the fix. Orchestrates the full repair loop: gather the problem, match it to the right fix pattern from the fix-playbook, implement, commit, and verify with crawler-test-flow. Use this for any crawler that stopped working — 403s, empty results, parsing failures, URL changes, rate limiting, DL queue floods, or anything in between.
---

# crawler-fix [site]

Repair skill that bridges diagnosis → implementation → verification for Market Study crawlers.

---

## Step 1 — Understand the problem

Ask: **"Možeš li opisati problem? (ili napiši 'ne znam' pa ću pokrenuti crawler-debug)"**

- **Problem is described** → proceed to Step 2
- **"Ne znam" / no description** → invoke the `crawler-debug [site]` skill to diagnose first, then return here with findings

If you're arriving from a `crawler-debug` run that already has a diagnosis, skip to Step 2 immediately.

---

## Step 2 — Match symptom to fix pattern

Open `~/Projects/market-study-knowledge/failure-patterns.md`. Use the tag vocabulary at the top to find matching patterns — grep the `**Tags:**` lines rather than reading top-to-bottom.

**Quick symptom → tag map:**

| What you see | Tags to grep |
|---|---|
| MS_DL flood, cheerio/undefined errors | `null-parse` `ms-dl` |
| "Prepared 0 listingUrls" (no error) | `prepared-0` `drop-zero` `selector` `getBrandsAndModels` |
| Sudden drop, 403/block | `403` `drop-sudden` `datadome` `cloudflare` `akamai` `scrapedo` |
| Gradual/slow decline | `drop-gradual` `credit` `proxy` |
| Vehicles duplicated or wrong | `duplicate` `url-change` `svl` |
| DL queue grows overnight | `ms-dl` `bulk-save` `rmq-stuck` |
| Empty body / fake 200 | `fake-200` `s3` `null-parse` |

Record which pattern(s) match and their prescribed fix. If no pattern matches, surface this to the user and ask for more context before proceeding.

---

## Step 3 — Plan the fix

Read the relevant section(s) in `~/Projects/market-study-knowledge/fix-playbook.md`. It's organized into:
- **Operational (non-code) actions**: S3 cache deletion, proxy swap, queue redeliver, disable/re-enable
- **Code patterns** (bottom half): Working URL 3-step checklist, ScrapeDo migration, parser quality rules

**Determine fix type:**
- **Operational only** (e.g. proxy swap, cache deletion, redeliver DL) → do it now, no code changes needed
- **Code fix** → follow the playbook's implementation pattern exactly
- **Both** → operational first (fast relief), code second (permanent fix)

Before touching code, confirm the plan with the user in one sentence: what you'll change and why. This takes 5 seconds and avoids implementing the wrong thing.

---

## Step 4 — Implement the code fix

Follow playbook instructions precisely. General rules from CLAUDE.md:
- Targeted changes only — no unrelated refactoring, no cleanup of surrounding code
- 4-space indent, explicit return types on every function, no `any`, path aliases only (no `../../..`)
- Every early `return` in `parseVehicleInput` / listing forEach must log via `this.logger.warn(...)` with `LoggingContexts.PARSER_DEBUGGING` (minimum: `message`, `site: this.site`, `url` or `itemId`)
- Lint only **newly created** files (never existing ones, even if modified): `npx prettier --write <file> && npx eslint <file> --fix`

**If the fix involves iterative testing** (e.g. ScrapeDo migration, selector change): add a narrow brand filter to `getBrandsAndModels()` while testing — see fix-playbook § "Narrow with a brand filter". Remove it before creating the PR.

---

## Step 5 — Commit

Derive commit message directly from the branch name (CLAUDE.md convention):
- Branch `bugfix/MAR-2085-otomoto-handling-damaged-vehicles` → `[MAR-2085][B] otomoto handling damaged vehicles`
- Branch `hotfix/MAR-2039-biltorvet-fix-api-requests` → `[MAR-2039][H] biltorvet fix api requests`
- No ticket: `[no-ticket][B] <short description>`

**Do NOT `git push` without telling the user first.** This is an explicit project rule — always confirm before pushing.

---

## Step 6 — Verify

Invoke `crawler-test-flow [site]` to run a local end-to-end verification.

Interpret the result:
- ✅ All phases green → fix verified. Report: "Fix verified locally. Ready to push when you say so."
- ❌ Phase fails → loop back to Step 2 with the new failure signal (fixing one thing sometimes reveals another)
- ⚠️ Partial pass → check if brand filter is too narrow or the issue is in a different pipeline phase

---

## Reference files (read on demand)

| When you need it | File |
|---|---|
| Pattern matching | `~/Projects/market-study-knowledge/failure-patterns.md` |
| Fix implementation | `~/Projects/market-study-knowledge/fix-playbook.md` |
| Code conventions | `CLAUDE.md` § "Code conventions" |
| Local testing details | `~/Projects/market-study-knowledge/local-testing.md` |

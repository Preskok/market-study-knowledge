---
name: crawler-info
description: >
  ALWAYS invoke this skill when the user's message starts with "crawler-info" followed by
  anything — e.g. "crawler-info otomoto", "crawler-info car-gr", "crawler-info leboncoin".
  This is the Market Study crawler on-call briefing skill. "crawler-info [site]" is the
  canonical trigger. Never search the codebase, never explore files — read the
  knowledge base and return a structured incident briefing for the named crawler site.
  Known sites include: otomoto, autoscout, mobile, mobile-bg, subito, avto-net,
  leboncoin, hasznalt-auto, njuskalo, car-gr, promo-neuve, lacentrale, ouestfrance-auto,
  olx-ro, blocket, finn, pazar3, polovni-automobili, autobazar, autoplius, oglasnik,
  flexicar, biltorvet, auto1, lease-plan, bob-automobile, eurostocks, auto-connect,
  willhaben, auto-zeilinger, gebrauchtwagen, autovit-ro, custojusto, ss-lv, vozi,
  index-hr, auti-hr, brie-des-nations, club-auto, commauto, ooyyo, sauto, sixtcarsales,
  rastetter, automobile, star-terre, and ~30 more.
  DO NOT invoke superpowers:systematic-debugging or any codebase search for crawler-info.
---

# crawler-info — Per-Site Crawler Briefing

## What this skill does

Produces a fast, structured status briefing for a specific Market Study crawler site.
The goal: save the on-call engineer the 10-minute Slack-archaeology session they would
otherwise need to answer "what's going on with [site]?".

## When this skill triggers

The canonical trigger is `crawler-info [site]`:

- `crawler-info otomoto`
- `crawler-info autoscout`
- `crawler-info mobile-bg`
- `crawler-info car-gr`
- `crawler-info leboncoin`
- `crawler-info avto-net`

The token immediately following `crawler-info` is the site name. It may be:
- A canonical name: `otomoto`, `autoscout`, `leboncoin`
- A spacing variant: `avto net` vs `avto-net`

## How to produce the briefing

### Step 1 — Resolve the site name via aliases.json (dictionary lookup)

Read `~/Projects/market-study-knowledge/aliases.json`. It's a flat map of `{alias: canonical-slug}`.

```json
{
  "as24": "autoscout",
  "autoscout": "autoscout",
  "autoscout24": "autoscout",
  "lbc": "leboncoin",
  ...
}
```

Lowercase the user's site token, strip leading/trailing spaces, and look it up.
If not found, try a few variants: hyphen↔space, removing dots, dropping country suffix.
If still not found, tell the user plainly and suggest the closest matches by fuzzy scan
of the `aliases.json` keys.

### Step 2 — Read the per-site file directly

Once you have the canonical slug, read **only** `~/Projects/market-study-knowledge/sites/[slug].md`.

Each file is small (~30–80 lines). Do NOT read other site files. Do NOT read the full
failure-patterns.md or foundational.md unless Step 3 calls for it.

The file contains:
- `## Current status` — one-line status (active / disabled / open issues)
- `## History & quirks` — chronological entries, newest first where dated
- `## Related patterns` — pattern numbers that apply to this site

### Step 3 — Find related failure patterns (Grep, not Read)

Use Grep to search `~/Projects/market-study-knowledge/failure-patterns.md` for the canonical slug (and common
variants — `autoscout` might appear as `autoscout24` or `autoscout-de` in the patterns
file). Collect every pattern that explicitly names the site.

Only Grep — never read the whole file. It's 510+ lines.

### Step 4 — Live Slack layer (when available)

The knowledge base is as fresh as the last build. To catch anything newer:

1. If you have access to the Slack MCP (`mcp__*__slack_search_*`), run a quick search
   in the Market Study channels for the canonical slug, limited to the last 30 days.
   Prioritise channels: `#tt-market-study` (C04K2LP3AG0), `#tt-market-study-checklist`
   (C0859KQ45B2).
2. Scan the results for incidents not already reflected in the site file: new errors,
   disables, URL changes, credit-burn alerts.
3. If you find anything relevant and newer than the knowledge base, include it at the
   top of the "Recent incidents" section with a note like `**[Slack, 2026-04-20]** —
   [summary + link to thread]`.
4. If Slack isn't available, skip this step silently. Don't tell the user you couldn't
   check Slack unless they specifically asked for fresh data.

Keep the Slack search cheap: one query, top 10 results. Don't read every thread — just
surface dates and one-line summaries.

### Step 5 — Operational context (optional, only if needed)

If the site file mentions a queue, proxy, or service that's worth expanding (e.g.
"on the limited consumer queue — 10 consumers"), open `~/Projects/market-study-knowledge/foundational.md`
and Grep for the relevant term. Include one or two lines of context if it adds value.

Skip if the site file is self-explanatory.

### Step 6 — Write the briefing in the standard format

## Output format

```
# [canonical site name] — [one-line status]

## Status
[1–3 sentences: is it running, is it disabled, any open issue right now? Pull from
the site file's Current status line. If the site is disabled or has an open issue,
say that FIRST.]

## Recent incidents (newest first)
- **[Date or period]** — [what happened + outcome]
- **[Date or period]** — [what happened + outcome]
...

## Known quirks & gotchas
- [Quirk / trap to watch for]
- [Quirk / trap to watch for]
...

## Failure patterns (from history)
- **#N — [Pattern title]** — [one-line reminder of how it manifests on this site]
...
(omit this section if no named patterns apply)

## Operational notes
- **Queue:** [which RMQ queue]
- **Anti-bot:** [DataDome / Cloudflare / ScraperAPI / scrape.do / mobile proxy / none]
- **Proxy:** [port or service if relevant]
- **Credits:** [ScraperAPI or scrape.do tier if relevant]
- **Deactivation risk:** [flag if site has history of mass-deactivation on issues]
(omit lines that aren't applicable)

## What to watch / next steps
[If there's an open issue or known instability, suggest the 1–2 things to check first.
 If the site is healthy, keep this short or omit it.]
```

## Tone and calibration

- **Dense and direct.** The reader is an engineer mid-incident or doing a morning check.
  No preamble, no "great question".
- **Newest first, always.** Lead with the most recent event. Older history is context,
  not the headline.
- **Use dates from the knowledge base.** "March 2025" beats "recently". Say "date unknown"
  if the knowledge base doesn't have one — don't guess.
- **Flag open issues at the top.** If the site's Current status says "disabled" or
  "has ongoing X", that goes in the status line, not buried.
- **If the site isn't found**, say so plainly, show the closest alias candidates, and
  offer to run the check on one of them. Don't fabricate.

## Reference files

| File | When to use | Load strategy |
|------|-------------|--------------|
| `~/Projects/market-study-knowledge/aliases.json` | Always — Step 1 | Read (tiny JSON) |
| `~/Projects/market-study-knowledge/sites/[slug].md` | Always — Step 2 | Read (small per-site file) |
| `~/Projects/market-study-knowledge/failure-patterns.md` | Step 3 | Grep only, never full read |
| `~/Projects/market-study-knowledge/foundational.md` | Step 5, optional | Grep only, if site file mentions it |
| `~/Projects/market-study-knowledge/fix-playbook.md` | Only if user asks "how do I fix X" | Grep the section |

## Troubleshooting

- **"Site not found"** — The token after `crawler-info` wasn't in aliases.json. Check
  `aliases.json` for the full list of canonical slugs. Add a new alias to
  `aliases-manual.json` at the source and rebuild if it's a common nickname.
- **Briefing is stale / missing a recent incident** — The knowledge base hasn't been
  updated. Tell the user the most recent date you have and suggest they update
  `sites/[slug].md` directly.
- **Multiple sites share an entry** (e.g. `merrjep-al-merrjep-xk-autoconnect.md`) —
  That's intentional; the Slack discussions cover all three together. Use the combined
  file regardless of which variant the user asked for.

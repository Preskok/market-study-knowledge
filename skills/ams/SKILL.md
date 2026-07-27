---
name: ams
description: ALWAYS invoke this skill when the user's message starts with "ams" followed by a topic — e.g. "ams active vehicles", "ams scrapedo", "ams es indices", "ams deactivation pipeline". Provides general AMS (Automatic Market Study) project knowledge — architecture, pipelines, data flow, queues, proxies, ScrapeDo, SVL, dealer handling, deploys, or any non-site-specific topic. NOT for per-site issues (use crawler-info / crawler-debug instead).
---

# ams — General AMS Project Knowledge

Quick lookup for general Automatic Market Study (market-study repo) topics. Different from `crawler-info` (per-site briefing) and `crawler-debug` (failure investigation) — this answers conceptual / architectural / operational questions.

## When to use

- User asks `ams [topic]` (e.g. `ams active vehicles`, `ams scrapedo`)
- User asks general questions about how AMS works without naming a specific site
- User wants to understand a pipeline, queue, index, or service

**Do NOT use when:**
- User names a specific site → use `crawler-info [site]` or `crawler-debug [site]`
- User reports a failure they want investigated → `crawler-debug`

## Steps

1. **Parse the topic** from the message (everything after `ams`).
2. **Read `~/Projects/market-study-knowledge/market-study-knowledge.md`** — search for matching `## topic` heading. Topics are lowercase, hyphenated (e.g. `active-vehicles`, `es-indices`, `scrapedo`). Match liberally — `active vehicles`, `Active Vehicles`, `active_vehicles`, `vehicles active` all map to `active-vehicles`.
3. **If found** → output the entry verbatim (already pre-formatted as dense bullets + Source line).
4. **If not found, fall back** to `~/Projects/market-study-knowledge/foundational.md` — search for relevant sections (use grep mentally: heading match, then keyword match). Distill into the same dense-bullet format. Always end with `**Source:** ~/Projects/market-study-knowledge/foundational.md § [section name]` and a Confluence link if you remember one.
5. **If truly unknown** → say so. Suggest checking Confluence directly. Offer to add the topic to `market-study-knowledge.md` after the user provides info or fetches the relevant Confluence page.

## Output format (rigid — match this exactly)

- 3-7 dense bullets, each with `**Bold sub-header** —` followed by the fact
- No preamble ("Here's what I know about..." → never)
- No closing ("Hope this helps!" → never)
- End with one or two `**Source:**` lines (Confluence URL preferred; reference file path acceptable)
- If the topic has known gaps (e.g. dedicated Confluence page not yet synced), mention briefly at the end before Source

## Example output (this is the target style)

> **Active vs inactive** — vehicles stay "active" as long as the crawler keeps seeing them. Deactivation pipeline runs nightly at 22:00, ~250k/day average, peak ~2M (leboncoin days).
>
> **Data index lifecycle** — `activeFrom` / `activeTo` track when a vehicle was first seen and when it went offline. No `activeTo` = still active.
>
> **Zombie vehicles** — active in the Data index but the crawler can't actually reach them (URL changed, site gone, detection failed). Marko has a detection script.
>
> **Safe threshold** — above ~900k deactivations/night the pipeline slows significantly.
>
> **Source:** [Active vehicles (Confluence)](https://preskok.atlassian.net/wiki/spaces/M/pages/2840821764/Active+vehicles) — full Confluence page not yet synced into knowledge base; ask if you need more depth.

## Tone

- Dense and direct, like a knowledgeable teammate dropping facts
- No hedging unless genuinely uncertain
- Don't repeat the topic name as a heading — go straight to the facts

## When user wants to add a topic

If user says "add this to ams" or "save this":
1. Pick a lowercase-hyphenated `## topic-name` heading
2. Append the entry to `~/Projects/market-study-knowledge/market-study-knowledge.md` in the same format
3. If a Confluence page exists, fetch it (via Atlassian MCP) and use it as the Source

## Reference files

- `~/Projects/market-study-knowledge/market-study-knowledge.md` — curated topic entries (primary lookup)
- `~/Projects/market-study-knowledge/foundational.md` — full architecture reference (fallback, copy from crawler-info)

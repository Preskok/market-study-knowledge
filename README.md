# market-study-knowledge

Knowledge base for the [Market Study](https://github.com/Preskok/market-study) crawler project — a NestJS service that crawls 80+ European car marketplaces.

## Contents

| File | Purpose |
|---|---|
| `failure-patterns.md` | Recurring failure modes across all crawler sites |
| `fix-playbook.md` | Step-by-step operational fix procedures |
| `foundational.md` | Architecture deep-dive: ES indices, RMQ, S3, deactivation pipeline |
| `graylog-queries.md` | Graylog query templates for production debugging |
| `multi-day-trend-analysis.md` | Methodology for multi-day anti-bot pressure analysis |
| `alert-emails.md` | Alert email formats and false-alarm signals |
| `aliases.json` | Site name → canonical slug mapping (auto-rebuilt) |
| `code-standards.md` | Project code conventions, patterns, naming rules |
| `market-study-knowledge.md` | Curated topic index: active vehicles, ES indices, ScrapeDo, SVL, etc. |
| `anomaly-rules.md` | Queue anomaly detection rules for ams-health |
| `queue-health-rules.md` | RabbitMQ queue health thresholds |
| `feedback-loop.md` | How the ams-health skill improves over time |
| `outlook-mcp-setup.md` | Setting up Outlook MCP for alert email integration |
| `sites/` | Per-site history, quirks, and incident timeline (~100 sites) |

## Setup (one-time)

```bash
git clone git@github.com:Preskok/market-study-knowledge.git ~/Projects/market-study-knowledge
```

No manual pulls needed — the `crawler-sync` skill auto-pushes updates after every sync run.
Teammates can `git pull` at any time for the latest.

## ⚠️ Disclaimer

**This repo is maintained largely by Claude (AI).** Knowledge files are auto-generated from Slack incident history, Confluence pages, and session harvests — no code review, no manual approval process. Direct pushes to `main` only.

**Use at your own risk.** Not everything here is guaranteed to be accurate or up to date. Treat it as a helpful starting point, not a source of truth. If something looks wrong, fix it directly — there is no bureaucracy here.

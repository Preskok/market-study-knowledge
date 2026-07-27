---
name: ams-open-ticket
description: Use when the user wants to create a new Jira ticket, open an issue, file a bug, write a ticket, or create a task in the MAR project. Triggers on "ams-open-ticket", "open a ticket", "create a ticket", "write a ticket", "file a bug", or any request to create a new Jira issue in the market-study board.
---

# ams-open-ticket — Create a Well-Formatted MAR Jira Ticket

Creates a Jira ticket in the `MAR` project following the house style — bold + code mixed inline, ad examples, screenshots, Slack references, acceptance criteria checklist.

## Constants

| Field | Value |
|-------|-------|
| `cloudId` | `preskok.atlassian.net` |
| `projectKey` | `MAR` |
| Default assignee | `63b53138f3e7004f77fe842b` (Filip Ožbolt) |
| Default issue type | `Bug` (use `Task` for features, `Story` for larger scope) |

---

## Step 1 — Gather information

Ask the user for everything needed. Do it in **one message** — don't ask round-trip per field.

**Required:**
- **Title / summary** — snake_case like existing tickets (`fix_mobile_de_parser`, `add_autobazar_sk_support`)
- **Type** — Bug / Task / Story
- **What's broken / what needs building** — current behaviour vs expected
- **Affected site or service** (if applicable)

**Optional but encouraged (ask if not provided):**
- Slack thread URL(s) for context
- Ad example URL(s) — real listing URLs that demonstrate the problem
- Screenshot paths — if the user has screenshots, ask them to attach; note `[screenshot here]` placeholder in description
- Steps to reproduce (for bugs)
- Special caveats / important warnings

**Acceptance criteria** — always ask: "What does done look like? List conditions one by one."

---

## Step 2 — Draft the description (markdown)

Use `contentFormat: "markdown"`. Follow the exact style of MAR-2067:

### Description template

```markdown
## Context

<1-3 sentences: what currently happens and why it's a problem. Mention the affected method/field/service using `code` formatting.>

<If there's a Slack thread: "Background and discussion: [slack thread](URL)">

---

## What needs to be done

- **<Task 1 headline with `code` for method/field names>**

  <Detail paragraph. Use **bold** for key terms and `code` for identifiers.>

  - ad example: [description](URL)

  ![screenshot description](placeholder — attach in Jira)

- **<Task 2 headline>**

  <Detail paragraph.>

  - Note: <caveat about listing vs details, SVL, etc.>

---

> ⚠️ **IMPORTANT:** <Any cross-cutting concern — e.g. "must work on both listings AND details, verify SVL does not fail">

---

## Acceptance criteria

- [ ] <Concrete, testable condition 1>
- [ ] <Concrete, testable condition 2>
- [ ] <Condition 3 — e.g. "No increase in SVL fail rate">
- [ ] <Condition 4 — e.g. "Verified on stage with crawler-test-flow">
```

### Formatting rules (non-negotiable)

| Element | Format |
|---------|--------|
| Method / field names | `` `getBrandsAndModels()` ``, `` `rawVersion` ``, `` `trimLine` `` |
| Key nouns / concepts | **bold** |
| Mixed (field name in sentence) | **Add** `rawVersion` **parsing on details** |
| Slack links | inline hyperlink `[thread](url)` |
| Ad example URLs | full clickable link on its own bullet |
| Images / screenshots | `![alt](url)` — if user has file paths, embed them; otherwise write `![description — attach in Jira]()` as a reminder |
| Acceptance criteria | `- [ ]` checkbox list |
| Important warnings | `> ⚠️ **IMPORTANT:**` blockquote |
| Updates (added later) | `### UPDATE DD.MM.YYYY` heading with bullet changes |

---

## Step 3 — Create the ticket via MCP

```
createJiraIssue(
  cloudId:        "preskok.atlassian.net",
  projectKey:     "MAR",
  issueTypeName:  "<Bug|Task|Story>",
  summary:        "<snake_case title>",
  description:    "<markdown string from Step 2>",
  contentFormat:  "markdown",
  assignee_account_id: "63b53138f3e7004f77fe842b",
  additional_fields: {
    priority: { name: "<High|Medium|Low>" }
  }
)
```

After creation, output the ticket URL:
```
https://preskok.atlassian.net/browse/<KEY>
```

---

## Step 4 — Confirm and offer to edit

Tell the user:
- Ticket URL (clickable)
- Summary of what was included
- "Screenshots need to be attached manually in Jira — the description has placeholders."

Offer: "Want me to add anything else — more acceptance criteria, steps, or a Slack link?"

---

## Quality checklist (before calling createJiraIssue)

- [ ] At least one `code`-formatted identifier in the description
- [ ] At least one **bold** key term
- [ ] Acceptance criteria has ≥ 2 checkboxes
- [ ] Ad example URL included (if applicable — skip for pure infrastructure tasks)
- [ ] No acceptance criteria written as vague "it works" — each must be testable
- [ ] IMPORTANT warning added if the change touches both listing and detail paths, SVL, or shared services
- [ ] Summary is snake_case

---

## Example (MAR-2067 style)

**User input:** "mobile.de parser is broken — rawVersion is wrong, also need to add DK and CZ countries, skip unknown-country vehicles"

**Description produced:**

```markdown
## Context

Currently, `getBrandsAndModels()` falls back to hardcoded "local" brand values due to blocks on their site.
Background and discussion: [Slack thread](https://preskok.slack.com/archives/C04K2LP3AG0/p1778679073096599)

---

## What needs to be done

- **Add more specific `rawVersion` parsing on details** (check if also present on listings). On details it's present as attribute `tag: "trimLine"`. If this field does not exist, fall back to the existing logic (`title` with brand and model stripped).

  - ad example: [mobile.de listing](https://suchen.mobile.de/fahrzeuge/details.html?id=450770776&cn=DE&...)

  ![trimLine attribute in details page HTML — attach screenshot in Jira]()

- **Add `Denmark` and `Czech Republic` to the `mobile` country list.**

  Currently we recognise 8 countries besides DE and fall back to DE for all others — which means non-European vehicles are saved as German market.
  Remove the DE fallback: **skip vehicles not from a predefined country list.**

---

> ⚠️ **IMPORTANT:** Changes must work on **both listings and details** — verify no SVL fail rate increase.

---

## Acceptance criteria

- [ ] `rawVersion` uses `trimLine` attribute when present on detail pages
- [ ] Fallback to old title-stripping logic when `trimLine` is absent
- [ ] DK and CZ vehicles appear in ES with correct country codes
- [ ] Vehicles with unrecognised countries are skipped (not saved as DE)
- [ ] No SVL fail rate increase — verified with `crawler-test-flow mobile`
```

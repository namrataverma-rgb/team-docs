---
name: cursor-feature-scout
description: >-
  Weekly briefing on what just got unlocked in Cursor, Claude Code, and the
  Intuit AI ecosystem. Scans public release notes (Cursor, Claude Code,
  Anthropic) plus Intuit Slack channels (#codeassist-support,
  #ds-agentic-dev-mcp-support, #gen-ai-curious, #cursor-users) and produces a
  standardized, team-neutral markdown briefing. Tracks six capabilities: live
  editing in HTML, inline commenting in HTML, dashboard-level HTML, new MCPs,
  new Cursor chat/compose features, and new Claude Code modes. Use when the
  user says "run the feature scout", "weekly scout", "what's new in Cursor
  this week", "what's new in Claude Code", "feature briefing", or "update the
  cursor-feature-scout briefing".
---

# Cursor Feature Scout

This skill produces a weekly, team-facing briefing that answers the question
*"what just got unlocked in our AI tooling?"*. It is Pillar 2 of the
LatentView Risk AI Adoption Strategy.

The skill does **not** measure adoption (that's `ai-adoption-report`). It does
**not** codify best practices (that's the LatentView Risk AI Playbook). It
scouts new capabilities and describes them factually so every teammate reads
the same briefing the same way.

## Quick Start

```
Task Progress:
- [ ] Step 1: Read sources.json to know what to check
- [ ] Step 2: Fetch public release notes (Cursor, Claude Code, Anthropic)
- [ ] Step 3: Search Intuit Slack channels (last 7 days)
- [ ] Step 4: Categorize findings against the 6 tracked capabilities
- [ ] Step 5: Write risk-analytics gloss for each finding
- [ ] Step 6: Fill the template and archive
- [ ] Step 7: Post summary link in team Slack
```

Default cadence: weekly (Monday morning). Can be re-run ad hoc when a
teammate sees a release note they want contextualized.

---

## Step 1 — Read sources.json

Always start by reading `sources.json` in this skill folder. It is the single
source of truth for what to scan. If the user wants to add or drop a source,
edit the JSON — never hardcode URLs in the SKILL.md body.

The file declares four source groups:
- `cursor` — Cursor changelog, docs, forum
- `claude_code` — Anthropic release notes, GitHub releases, blog, engineering blog
- `intuit_slack` — channel list + keyword set + lookback window
- `tracked_capabilities` — the six capabilities we always report on, with
  keywords and risk-relevance blurbs

## Step 2 — Fetch public release notes

Use whichever fetch tool is available in the current runtime:
- **Preferred:** the `WebFetch` tool if the user's runtime has it.
- **Fallback:** the `user-fetch` MCP server (`fetch_url` tool) if present.
- **Last resort:** the `WebSearch` tool to find the latest changelog URL, then fetch.

Fetch these URLs in parallel and note the HTTP status. For each, extract the
last ~7 days of entries (or fewer if nothing new). Skip entries older than the
previous briefing's week-end date.

Minimum to capture per entry:
- Date
- Feature / change name
- One-paragraph factual description
- Source URL

Do **not** copy long product marketing text verbatim into the briefing — always
compress to a single factual sentence.

## Step 3 — Search Intuit Slack channels

Use the `plugin-slack-slack` MCP. For each channel in
`sources.intuit_slack.channels`, run `slack_search_public` with:
- `query`: the channel name + a relevant keyword from
  `sources.intuit_slack.search_terms`
- `after`: today minus `lookback_days` (default 7)

Dedupe results. For each notable thread found, capture:
- Date
- Channel
- Paraphrased summary (not the raw message — paraphrase to avoid quoting users)
- Any linked artifact (PR, Google Doc, internal URL)

### Privacy rules (HARD CONSTRAINTS)

- **Never paste Slack messages verbatim.** Paraphrase into neutral language.
- **Never include user handles** (`@someuser`) in the briefing. Either omit the
  attribution, or use the person's role ("FinTech DevSuccess shared…").
- **Never include dollar figures, internal PR numbers, or customer names**
  from Slack threads unless they are already published on a public Intuit
  engineering page.
- **Skip messages from externally shared (Slack Connect) channels.**

## Step 4 — Categorize against the six tracked capabilities

For each finding, tag it against one or more of the six `tracked_capabilities`
ids in sources.json:
- `live_html_editing`
- `inline_html_comments`
- `html_dashboard_caps`
- `new_mcps`
- `cursor_chat_compose`
- `claude_code_modes`

If a finding matches none of the six, put it in a general "what changed" bucket
for §1–3 of the template. Every finding also goes into §4 under the relevant
sub-heading. If nothing matched a particular capability this week, that
sub-heading says "No change this week." — do not invent content.

## Step 5 — Write the practical implication (team-neutral)

For each item, write 1–2 sentences of "what this practically enables." Keep
it factual and team-agnostic so anyone on the team reads the briefing the
same way. Do **not** correlate findings to any specific teammate's skills,
projects, or ongoing work.

**Style rubric:**
- ✅ "Replaces hand-rolled HTML+JS dashboards with first-party Cursor components."
- ✅ "Reduces permission-prompt friction for routine MCP calls."
- ❌ "Directly overlaps [teammate]'s [specific skill]."
- ❌ "Pilot this on the [specific monthly workflow]."
- ❌ "This is a powerful new capability that unlocks many workflows." (too abstract)

If the practical implication is "no material effect for AI-assisted analytics
workflows right now", say so plainly. Do not pad.

Recommendations in §5 of the template should be stated generically ("Anyone
on Cursor CLI should try X", "Teams using MCP-heavy configs should upgrade").
Never name specific teammates or specific client projects.

## Step 6 — Fill the template and archive

Read `templates/briefing-template.md`. Replace every `{{PLACEHOLDER}}` with
the content from Steps 2–5. Keep the HTML comments as guidance for future
scouts (they make the template self-documenting).

When drafting, write output to `/tmp/briefing-draft.md` first for review,
then archive:

```bash
python ~/.cursor/skills/cursor-feature-scout/scripts/archive_briefing.py \
  --input /tmp/briefing-draft.md \
  --week-start YYYY-MM-DD \
  --scout <user_label>
```

The archive script:
- Copies the draft to `briefings/briefing-YYYY-MM-DD.md`
- Rebuilds `briefings/INDEX.md` with every past briefing
- Is idempotent — safe to re-run

Week-start is the Monday of the week being reported on.

## Step 7 — Post summary in team Slack

Via the `plugin-slack-slack` MCP, post the TL;DR section of the briefing into
the team channel, with a link to the full briefing file. Use
`slack_send_message_draft` (not direct send) so the scout can review + send
from Slack directly. Recipient channel is configurable; default is the
team AI channel if known, otherwise DM the scout to have them place it.

---

## When nothing changed

If after scanning all sources a full week has zero notable findings, still
produce a briefing — but make it a single short section titled "Quiet week."
Do not pad. The rhythm matters more than any individual entry; the team
should see a briefing every week so they know the scout ran.

## Privacy & safety checklist (before archiving)

- [ ] No Slack messages quoted verbatim
- [ ] No user handles mentioned
- [ ] No dollar figures / internal PR numbers / customer names
- [ ] No secrets or tokens leaked through changelog quotes
- [ ] Every external claim has a source URL
- [ ] No correlations to specific teammates' skills or projects
- [ ] Practical-implication sentences are factual, not opinion dressed as fact
- [ ] Recommendations are phrased generically ("anyone using X should Y")

## File Reference

| File | Role |
|---|---|
| `sources.json` | Canonical source config (URLs, channels, tracked capabilities). Edit this to change scope. |
| `templates/briefing-template.md` | The weekly output skeleton. |
| `scripts/archive_briefing.py` | Archives the draft + rebuilds INDEX.md. |
| `briefings/` | Every past briefing, one file per week. |
| `briefings/INDEX.md` | Auto-generated navigation. |
| `examples/briefing-sample.md` | A realistic filled-in example. |

## Anti-Patterns

- Do not hardcode URLs in this SKILL.md — put them in `sources.json`.
- Do not quote Slack messages verbatim — paraphrase.
- Do not fabricate a release note if the week was quiet — say "Quiet week."
- Do not correlate findings to specific teammates' skills or projects (e.g.
  "this replaces teammate X's workflow"). Briefings are reference material,
  not personal task lists.
- Do not write abstract, hand-wavy implication sentences ("unlocks many
  workflows") — be factual and specific to the capability itself.
- Do not upload the briefing as a Google Doc (yet). Keep briefings in the repo
  as markdown for diff-ability; post links to them in Slack.

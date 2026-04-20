# cursor-feature-scout

Weekly briefing on what just got unlocked in Cursor, Claude Code, and the
Intuit AI ecosystem — filtered for the LatentView Risk team at Intuit.

## What it does

Every week, this skill:

1. **Scans public release notes** — Cursor changelog, Claude Code release
   notes, Anthropic news/engineering blog.
2. **Scans Intuit Slack signal** — `#codeassist-support`,
   `#ds-agentic-dev-mcp-support`, `#gen-ai-curious`, `#cursor-users` over the
   last 7 days (paraphrased, never quoted verbatim).
3. **Categorizes findings** against six capabilities the team actively tracks:
   - Live editing in HTML pages
   - Inline commenting in HTML
   - Dashboard-level HTML capabilities
   - New MCPs relevant to risk analytics
   - New Cursor chat / compose features
   - New Claude Code modes
4. **Writes a concrete "risk-analytics gloss"** for every finding — no
   abstract fluff, only "here's what this means for our MBR/FNPL/cohort work."
5. **Produces a standardized markdown briefing**, archived into `briefings/`
   with an auto-generated INDEX.md.
6. **Drafts a Slack summary** for the scout to review + send.

## How it fits the bigger picture

This is **Pillar 2** of the LatentView Risk AI Adoption Strategy:

| Pillar | Instrument | Role |
|---|---|---|
| 1. Measurement | `ai-adoption-report` skill | "What are we using today?" |
| **2. Feature intelligence** | **this skill + `slack-ai-scout`** | **"What just got unlocked?"** |
| 3. Best practices | LatentView Risk AI Playbook (Akash) | "How do we work well?" |

## Running it

Just ask the agent in Cursor or Claude Code:

- *"Run the cursor-feature-scout for this week"*
- *"What's new in Cursor this week?"*
- *"Scout Claude Code changes for the last 7 days"*
- *"Update the feature briefing"*

The skill's trigger phrases cover: *run the feature scout, weekly scout,
what's new in Cursor/Claude Code, feature briefing, cursor-feature-scout.*

## Rotating scout role

Each month a different LV Risk teammate picks 2–3 items from the latest
briefings and demos them in the bi-weekly meeting. This spreads feature
literacy across the team instead of concentrating it in one person.

## Adjusting what it watches

Edit `sources.json`. The skill never hardcodes URLs or channel names — all
source configuration lives in that one file:

- Add a new URL to the `cursor` / `claude_code` blocks
- Add a channel to `intuit_slack.channels`
- Add a new capability to `tracked_capabilities` (keywords + risk_relevance)

## Privacy

- Only paraphrases Slack content — never quotes messages verbatim.
- Drops user handles, dollar figures, and internal PR/customer names.
- Skips externally shared (Slack Connect) channels.
- Every non-trivial claim in the briefing carries a source URL.

## Layout

```
cursor-feature-scout/
├── SKILL.md
├── README.md
├── sources.json                   # what to scan (single source of truth)
├── scripts/
│   └── archive_briefing.py        # saves the briefing + rebuilds INDEX.md
├── templates/
│   └── briefing-template.md       # the weekly output skeleton
├── briefings/                     # one file per week
│   ├── INDEX.md                   # auto-generated
│   └── briefing-YYYY-MM-DD.md
└── examples/
    └── briefing-sample.md         # worked example
```

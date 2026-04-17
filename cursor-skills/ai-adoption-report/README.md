# ai-adoption-report

Auto-generate AI adoption documentation from a teammate's AI coding environment
(Cursor and/or Claude Code), with zero manual writing.

## Supported runtimes

| Runtime | Skills path | Works? |
|---|---|---|
| Cursor IDE | `~/.cursor/skills/ai-adoption-report/` | Yes — native |
| Cursor CLI (`cursor-agent`) | `~/.cursor/skills/ai-adoption-report/` | Yes — native |
| Claude Code CLI (`claude`) | `~/.claude/skills/ai-adoption-report/` (copy or symlink) | Yes — native |
| Claude Desktop / Claude.ai | — | No (no filesystem skill loader) |

The `SKILL.md` format is Anthropic's shared Agent Skills spec, so the same
folder works in both Cursor and Claude Code. The scanner auto-detects which
tool(s) are installed on each machine and scans whichever is present.

## What it does

Two modes:

1. **Individual** — each teammate runs the scanner on their laptop. It
   produces three files:
   - `<user>-inventory.json` — **PRIVATE, NEVER UPLOADED.** Contains full
     SKILL.md bodies, transcript titles, MCP command-lines, hook commands.
     Stays on the teammate's machine forever.
   - `<user>-report.md` — shareable narrative, grouped by source tool
   - `<user>-digest.json` — shareable sanitized structured data (skill names
     only, MCP names only, hook event names only, theme cluster counts only)
2. **Aggregate** — the team lead collects every teammate's `digest.json` in a
   folder, runs the aggregator, and gets a team JSON + team Markdown summary
   showing tool adoption (Cursor vs Claude Code vs both), shared skills,
   unique skills, per-source MCP adoption, hook adoption, and cross-team
   theme clusters. The aggregator never needs the private inventory.

## How to invoke

Just ask the agent in Cursor, e.g.:
- "Run the AI adoption report on my environment and upload it to our team Drive
  folder."
- "Aggregate these four teammate inventory files into a team summary."
- "Document what AI tooling my team uses."

The skill's trigger phrases include: *AI documentation, AI adoption report, AI
audit, team AI inventory, cursor skills inventory, team AI rollup*.

## Layout

```
ai-adoption-report/
├── SKILL.md
├── README.md
├── scripts/
│   ├── scan_environment.py       # individual-mode scanner
│   └── aggregate_inventories.py  # aggregate-mode merger
├── templates/
│   ├── individual_report.md
│   └── team_summary.md
└── examples/
    └── individual_sample.md
```

## Privacy

**Two-tier output design:**

| Stays local (private) | Leaves the machine (shareable) |
|---|---|
| `<user>-inventory.json` | `<user>-report.md`, `<user>-digest.json` |
| Full SKILL.md bodies | Skill names + description previews only (≤200 chars) |
| All 60-day transcript titles | Theme cluster names + counts only |
| MCP `command` + `args` | MCP server names only |
| Hook event commands | Hook event names only |
| Host, OS, user paths | User label only |

**Additional scanner guarantees:**

- Reads only the **first user message** of each transcript (≤220 chars),
  truncated and redacted
- Strips emails, bearer tokens, API keys, OpenAI/GitHub tokens, long hex
  strings before any JSON is written
- Never includes raw assistant responses or tool-call payloads
- The agent is instructed to paraphrase project/client/dollar references when
  writing narrative

## Team workflow

Shared team Drive folder (default destination):
[team-ai-adoption-report](https://drive.google.com/drive/folders/1ltq7KtGpufp8RNO5cwSewX1QsKGDwHfI)
· folder ID `1ltq7KtGpufp8RNO5cwSewX1QsKGDwHfI`.

1. Share this skill with the team. Each teammate installs it in whichever tool
   they use:
   - Cursor users → copy into `~/.cursor/skills/ai-adoption-report/`
   - Claude Code users → copy into `~/.claude/skills/ai-adoption-report/`
   - Users of both → install in one location and symlink from the other:
     ```bash
     ln -s ~/.cursor/skills/ai-adoption-report ~/.claude/skills/ai-adoption-report
     ```
2. Each teammate asks the agent (in whichever tool): *"Run the AI adoption
   report and upload to our team Drive folder."* The skill auto-detects their
   tool(s) and produces:
   - `<user>-inventory.json` — **stays local, never uploaded**
   - `<user>-report.md` — uploaded as a Google Doc
   - `<user>-digest.json` — uploaded to the Drive folder (sanitized data for
     aggregation)
3. Team lead asks the agent: *"Aggregate the team digests from our Drive
   folder and upload the team summary."* The skill pulls every
   `*-digest.json`, runs the aggregator (which produces a tool-adoption
   breakdown, shared-skill registry, per-source MCP/hook adoption, etc.), and
   uploads `team-summary-YYYY-MM-DD.md` back to the same folder.
4. Repeat monthly/quarterly for rolling adoption tracking.

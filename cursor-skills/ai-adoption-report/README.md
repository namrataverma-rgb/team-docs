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

1. **Individual** — each teammate runs a scanner on their laptop. It reads
   skills, rules/memory, hooks, and MCP configs for whichever of Cursor /
   Claude Code are installed, plus the first user message of each recent
   agent transcript (Cursor's `agent-transcripts/` layout **and** Claude
   Code's `~/.claude/projects/` layout). Every output field is tagged with
   `"source": "cursor"` or `"source": "claude-code"`. The agent then writes a
   Markdown report from that structured data, grouped by source tool.
2. **Aggregate** — the team lead collects every teammate's `inventory.json` in
   a folder, runs the aggregator, and gets a team JSON + team Markdown summary
   showing tool adoption (Cursor vs Claude Code vs both), shared skills,
   unique skills, per-source MCP adoption, hook adoption, and cross-team
   transcript themes.

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

- Reads only the **first user message** of each transcript (≤220 chars),
  truncated and redacted
- Strips emails, bearer tokens, API keys, OpenAI/GitHub tokens, long hex
  strings before the JSON is written
- Never includes raw assistant responses or tool-call payloads
- The agent is instructed to paraphrase project/client/dollar references when
  writing narrative

## Team workflow

Shared team Drive folder (default destination):
[team-ai-adoption-report](https://drive.google.com/drive/folders/1tPqQ4NsWNiTFJ182GU81FsJXIaAbulFb)
· folder ID `1tPqQ4NsWNiTFJ182GU81FsJXIaAbulFb`.

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
   tool(s) and uploads two files:
   - `<user>-inventory.json` (raw structured data, used for aggregation)
   - `<user>-report.md` (human-readable narrative, grouped by Cursor / Claude
     Code sections)
3. Team lead asks the agent: *"Aggregate the team inventories from our Drive
   folder and upload the team summary."* The skill pulls every
   `*-inventory.json`, runs the aggregator (which produces a tool-adoption
   breakdown, shared-skill registry, per-source MCP/hook adoption, etc.), and
   uploads `team-summary-YYYY-MM-DD.md` back to the same folder.
4. Repeat monthly/quarterly for rolling adoption tracking.

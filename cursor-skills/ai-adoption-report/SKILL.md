---
name: ai-adoption-report
description: >-
  Automatically generate AI adoption documentation for a teammate or an entire
  team by scanning their AI coding environment (Cursor and/or Claude Code) —
  skills, rules/memory, hooks, MCP servers, and recent agent-transcript themes.
  Produces a Markdown report per person and an aggregated team summary, and can
  upload results to a shared Google Drive folder. Use when the user mentions AI
  documentation, AI adoption report, AI audit, team AI inventory, cursor skills
  inventory, claude code skills inventory, team AI rollup, or asks to "document
  what AI we use", "scan my AI environment", "scan my cursor environment",
  "scan my claude code environment", or "generate team AI docs".
---

# AI Adoption Report

Generate audit-grade documentation of how a person (or team) uses AI coding
tools, without any manual writing. Supports **Cursor IDE**, **Cursor CLI**
(both use `~/.cursor/`), and **Claude Code CLI** (uses `~/.claude/`). The
scanner auto-detects installed tools and tags every artifact with its source.

The skill runs in two modes:

- **individual** — each teammate runs this on their own laptop. Produces a
  per-person Markdown report.
- **aggregate** — the team lead runs this after collecting everyone's reports
  from a shared Drive folder. Produces a team-wide summary.

## Quick Start

```
Task Progress:
- [ ] Step 1: Confirm mode (individual vs aggregate) and output folder
- [ ] Step 2: Run the environment scanner → inventory.json
- [ ] Step 3: Fill the markdown template using the JSON + LLM narrative
- [ ] Step 4: Save the markdown locally
- [ ] Step 5: Upload to the shared Google Drive folder
- [ ] Step 6: Print the final path/URL
```

Always pick the correct mode first. If the user says "my report" / "scan my
environment" → **individual**. If they say "merge team reports" / "aggregate" /
"team summary" → **aggregate**.

---

## Individual Mode

### Step 1 — Confirm parameters

Ask the user (only if not already provided):
- Output folder for the report (default `~/ai-adoption-report/`)
- Transcript look-back window in days (default `60`)
- Shared Google Drive folder URL (**default:** the team folder at
  https://drive.google.com/drive/folders/1tPqQ4NsWNiTFJ182GU81FsJXIaAbulFb —
  folder ID `1tPqQ4NsWNiTFJ182GU81FsJXIaAbulFb`). Use this folder unless the
  user names a different one.

### Step 2 — Run the scanner

Use the correct skill path depending on which AI tool the teammate is using:

```bash
mkdir -p ~/ai-adoption-report

# If invoked from Cursor (IDE or CLI):
python ~/.cursor/skills/ai-adoption-report/scripts/scan_environment.py \
  --tool auto \
  --out ~/ai-adoption-report/inventory.json \
  --transcript-days 60

# If invoked from Claude Code CLI (same script lives at ~/.claude/skills/...):
python ~/.claude/skills/ai-adoption-report/scripts/scan_environment.py \
  --tool auto \
  --out ~/ai-adoption-report/inventory.json \
  --transcript-days 60
```

Flags:
- `--tool auto` (default) — detects `~/.cursor/` and `~/.claude/` and scans
  whatever is present. This is the right default.
- `--tool cursor` — force Cursor-only.
- `--tool claude-code` — force Claude Code-only.
- `--tool both` — scan both even if one appears empty.

The scanner is **deterministic, privacy-safe, and tool-aware**:
- Detects Cursor and Claude Code installations automatically
- Reads SKILL.md files, hook configs, MCP configs, rules/memory files
- Handles Cursor's transcript format (`{role, message.content[]}`) and Claude
  Code's (`{type, message: {role, content}}`)
- Reads only the **first user message** from each transcript, truncated to 220
  chars
- Redacts emails, bearer tokens, hex secrets, API keys before output
- Never includes full transcript bodies
- Tags every skill/rule/hook/MCP/transcript with `"source": "cursor"` or
  `"source": "claude-code"`

### Step 3 — Generate the report

Read `~/ai-adoption-report/inventory.json` and the template at
`templates/individual_report.md`. Fill every `{{placeholder}}` using the JSON
data; for the narrative sections (executive summary, theme clusters, standout
tasks, value-add per skill) write original prose — do not parrot the raw SKILL.md.

**Required schema fields per skill** (from the design contract):

| Field | Source |
|---|---|
| Source tool | `skills[].source` (`cursor` or `claude-code`) |
| Name & Purpose | `skills[].name`, `skills[].description` (rewrite in your own words) |
| Value add | Infer from description + body — explain why the team benefits |
| Key features | Bullet list distilled from `skills[].section_features` or body headings |
| Limitations | `skills[].section_limitations` if non-empty, else infer conservatively (write "None documented" if you can't tell) |
| Challenges | `skills[].section_challenges` if non-empty, else "None documented" |
| Author / dates | `skills[].created`, `skills[].modified` |

Group skills by source tool in the report (Cursor section, Claude Code
section). If both tools host the same skill name, document it once and note
it's installed in both.

**For theme clustering** (Section 5 of the template): group the
`transcript_themes.samples` list into 3–7 coherent clusters. Use neutral,
paraphrased cluster names. Do not quote titles verbatim if they mention
proprietary project names — paraphrase.

Write the filled markdown to `~/ai-adoption-report/<user_label>-report.md`.

### Step 4 — Upload to Google Drive

Upload both `<user_label>-inventory.json` AND `<user_label>-report.md` to the
team Drive folder (default ID `1tPqQ4NsWNiTFJ182GU81FsJXIaAbulFb`,
https://drive.google.com/drive/folders/1tPqQ4NsWNiTFJ182GU81FsJXIaAbulFb) using
the `user-google-drive-mcp` server.

Preferred file names in Drive:
- `<user_label>-inventory.json` (raw structured data — needed later by the
  aggregator)
- `<user_label>-report.md` (human-readable narrative)

If the MCP returns an error (e.g. auth expired), do **not** block. Print:
1. Local paths of both files
2. The Drive folder URL
3. A short note: *"Google Drive MCP is currently unavailable — please upload
   these two files to the team folder manually, or re-authenticate the MCP in
   Cursor Settings → MCP and re-run this step."*

Local markdown is the primary deliverable; Drive upload is a convenience.

### Step 5 — Report back

Print:
- Local report path
- Drive URL (if uploaded)
- Top-line stats: N skills documented, M transcript sessions analyzed

---

## Aggregate Mode

### Step 1 — Collect per-user inventories

The team lead downloads every `<user_label>-inventory.json` file from the team
Drive folder
(https://drive.google.com/drive/folders/1tPqQ4NsWNiTFJ182GU81FsJXIaAbulFb) into
a local folder, e.g. `~/ai-adoption-report/team-inputs/`.

You can do this via the `user-google-drive-mcp` server (list the folder by ID
`1tPqQ4NsWNiTFJ182GU81FsJXIaAbulFb`, then download every `*-inventory.json`
file) or the user can drag-and-drop them manually.

Expected naming: `<user_label>-inventory.json`.

### Step 2 — Run the aggregator

```bash
python ~/.cursor/skills/ai-adoption-report/scripts/aggregate_inventories.py \
  --inputs '~/ai-adoption-report/team-inputs/*.json' \
  --out ~/ai-adoption-report/team-summary.json \
  --samples-per-user 15
```

This emits a structured team JSON with roster, shared skill registry, unique
skills, MCP adoption, hook adoption, rules adoption, transcript volumes, and
per-user theme samples.

### Step 3 — Write the team summary

Read `team-summary.json` and `templates/team_summary.md`. Fill placeholders and
write these narrative sections yourself:
- Executive summary (5–8 sentences)
- Cross-team theme clusters (merge `theme_samples` from all users into 5–10
  team-wide themes)
- Notable unique wins (paraphrase 5–10 standout sessions, credit the teammate)
- Recommendations (which unique skills to promote to shared skills, which MCPs
  to adopt broadly, gaps to fill)

Write to `~/ai-adoption-report/team-summary.md`.

### Step 4 — Upload team summary

Upload `team-summary.md` (and optionally `team-summary.json`) to the same team
Drive folder
(https://drive.google.com/drive/folders/1tPqQ4NsWNiTFJ182GU81FsJXIaAbulFb) via
the `user-google-drive-mcp` server. File name: `team-summary-YYYY-MM-DD.md` so
historical snapshots stack cleanly in the folder.

Fall-back behavior is the same as individual mode — never block on Drive.

---

---

## Tool Compatibility

| Platform | Install location | Status |
|---|---|---|
| Cursor IDE | `~/.cursor/skills/ai-adoption-report/` | Native — auto-triggers |
| Cursor CLI (`cursor-agent`) | `~/.cursor/skills/ai-adoption-report/` | Native — auto-triggers |
| Claude Code CLI (`claude`) | `~/.claude/skills/ai-adoption-report/` | Native — auto-triggers |
| Claude Desktop app | — | Not supported (no local skill loader) |
| Claude.ai web | — | Not supported (sandboxed) |

### Installing into Claude Code

Either **copy** or **symlink** the skill folder so Claude Code can discover it:

```bash
# Option A: copy
cp -R ~/.cursor/skills/ai-adoption-report ~/.claude/skills/

# Option B: symlink (stays in sync with any future edits)
mkdir -p ~/.claude/skills
ln -s ~/.cursor/skills/ai-adoption-report ~/.claude/skills/ai-adoption-report
```

The same `SKILL.md` works in both runtimes because the Agent Skills spec is
shared. Scripts inside the skill use `python3` and stdlib only, so they work
anywhere Python 3.9+ is installed.

---

## Privacy Rules (Hard Constraints)

The scanner is already privacy-safe, but the agent must also follow these when
writing narratives:

1. **Do not quote transcript content verbatim** if it contains project code
   names, client names, or dollar figures — paraphrase.
2. **Do not invent data.** If a skill has no documented limitations or
   challenges, write "None documented" rather than making something up.
3. **Do not include secrets** in the final markdown, even if they somehow
   survived redaction. Sanity-check the output.
4. **Do not read additional transcript files** beyond what the scanner surfaces.
   The scanner's output is the authoritative transcript data source.

## Anti-Patterns

- Do not run the scanner on someone else's laptop remotely — it is designed for
  local, consent-based self-inventory.
- Do not paste `inventory.json` directly into the report. The report is a
  narrative rendered *from* the JSON.
- Do not skip the scanner and try to gather data ad-hoc with shell commands —
  the scanner enforces consistent schema and redaction.
- Do not nest reference files: all templates and scripts live one level deep
  from this SKILL.md.

## File Reference

| File | Role |
|---|---|
| `scripts/scan_environment.py` | Deterministic environment scanner (individual mode) |
| `scripts/aggregate_inventories.py` | Aggregates per-user JSONs (aggregate mode) |
| `templates/individual_report.md` | Per-person markdown template |
| `templates/team_summary.md` | Team-level markdown template |
| `examples/individual_sample.md` | Example filled-in individual report |

## Troubleshooting

- **Scanner finds 0 transcripts** — increase `--transcript-days`. Default 60;
  try 180.
- **Google Drive MCP errors** — tell the user to re-authenticate in Cursor
  Settings → MCP, then continue with local-only output.
- **Empty `section_limitations`/`section_challenges` for most skills** —
  expected. Older SKILL.md files rarely have those headings; write "None
  documented" and suggest the owner add them.
- **Aggregator finds 0 files** — verify input path is quoted (shells expand
  globs unexpectedly). Wrap in single quotes.

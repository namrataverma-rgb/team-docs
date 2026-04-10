# FNPL MBR — Cursor Agent Skill (Cover + Slides 9–13)

This folder mirrors the **fnpl-mbr-slide9** Cursor skill: Databricks extraction, AIG validation, HTML slide generation, and Google Sheets handoff.

## Contents

| File | Purpose |
|------|---------|
| `SKILL.md` | Full workflow, steps, template enforcement, Slide 13 verification gates |
| `slide11-table-spec.md` / `slide13-chart-spec.md` | Canonical table/chart behavior |
| `template.html`, `template-slide10.html` … `template-slide13.html` | Plotly/HTML templates (`{{PLACEHOLDER}}` only) |
| `queries.md`, `queries-slide10.md` … `queries-slide13.md` | SQL reference |
| `schema-reference.md` | Column notes |
| `intuit-ecosystem-white.svg` | Cover slide logo asset |

## Install (local Cursor)

```bash
mkdir -p ~/.cursor/skills
cp -R /path/to/cg-credit-risk/cursor-skills/fnpl-mbr-slide9 ~/.cursor/skills/fnpl-mbr-slide9
cp ~/.cursor/skills/fnpl-mbr-slide9/run-history.example.json ~/.cursor/skills/fnpl-mbr-slide9/run-history.json
```

Edit `run-history.json` only on your machine (successful runs append here; not required for the skill to load).

## Upstream

Changes to the skill should be edited **here** (or in your `~/.cursor/skills/fnpl-mbr-slide9` copy) and kept in sync so the repo stays the team source of truth.

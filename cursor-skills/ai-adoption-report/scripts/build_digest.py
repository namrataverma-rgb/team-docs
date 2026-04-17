#!/usr/bin/env python3
"""
Build a shareable `digest.json` from a local `inventory.json`.

The digest is the **only** structured artifact safe to upload to the team
Drive folder. It strips:
  - Full SKILL.md body markdown
  - Extracted section_features / section_limitations / section_challenges text
  - Raw transcript titles (only cluster names + counts survive)
  - MCP server command lines and args
  - Hook event commands

Theme clusters must be supplied separately (either via --themes clusters.json
or inline via --themes-inline '[{"name":"MBR","count":22}, ...]') because
clustering is an LLM step the agent does in context while writing the report.
If no themes are supplied, a single "(themes not clustered)" entry is emitted
with the total session count — the digest is still useful for tool/skill/MCP
rollups.

Usage:
    python build_digest.py --inventory ~/ai-adoption-report/nverma14-inventory.json \\
        --out ~/ai-adoption-report/nverma14-digest.json \\
        --themes ~/ai-adoption-report/themes.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SAFE_DESCRIPTION_CHARS = 200


def build_digest(inv: dict[str, Any], themes: list[dict[str, Any]]) -> dict[str, Any]:
    tools = inv.get("tools_scanned", [])
    tool_summary: dict[str, dict[str, int]] = {
        t: {
            "skill_count": sum(1 for s in inv.get("skills", []) if s.get("source") == t),
            "mcp_count": sum(1 for m in inv.get("mcp_servers", []) if m.get("source") == t),
            "hook_event_count": len(
                ((inv.get("hooks", {}) or {}).get(t, {}) or {}).get("events", {}) or {}
            ),
            "session_count": ((inv.get("transcript_themes", {}) or {}).get(t, {}) or {}).get(
                "total_sessions", 0
            ),
        }
        for t in tools
    }

    skills = []
    for s in inv.get("skills", []):
        desc = (s.get("description") or "").strip()
        if desc.startswith("- "):
            desc = desc[2:].strip()
        skills.append(
            {
                "source": s.get("source"),
                "name": s.get("name"),
                "description_preview": desc[:SAFE_DESCRIPTION_CHARS],
                "line_count": s.get("line_count"),
                "created": s.get("created"),
                "modified": s.get("modified"),
                "has_scripts": s.get("has_scripts", False),
                "has_documented_limitations": bool((s.get("section_limitations") or "").strip()),
                "has_documented_challenges": bool((s.get("section_challenges") or "").strip()),
            }
        )

    mcp_servers = [
        {"source": m.get("source"), "name": m.get("name")}
        for m in inv.get("mcp_servers", [])
    ]

    hook_events = []
    for src, payload in (inv.get("hooks", {}) or {}).items():
        if not isinstance(payload, dict):
            continue
        for event_name, items in (payload.get("events", {}) or {}).items():
            hook_events.append(
                {"source": src, "event": event_name, "handler_count": len(items or [])}
            )

    return {
        "schema_version": 1,
        "user_label": inv.get("user_label"),
        "generated_at": inv.get("generated_at"),
        "tools_scanned": tools,
        "tool_summary": tool_summary,
        "skills": skills,
        "mcp_servers": mcp_servers,
        "hook_events": hook_events,
        "has_custom_rules": bool(inv.get("rules")),
        "rules_count": len(inv.get("rules", [])),
        "theme_clusters": themes,
        "privacy_note": (
            "This digest is sanitized for team sharing. It does NOT contain "
            "SKILL.md bodies, transcript titles, MCP command-lines, hook "
            "commands, or OS/host identifiers. For the full local snapshot, "
            "see the inventory.json on the teammate's machine (never upload)."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--themes", type=Path, default=None,
                    help='JSON file with [{"name": "cluster", "count": int, '
                         '"tool_split": {"cursor": int, "claude-code": int}}, ...]')
    ap.add_argument("--themes-inline", default=None,
                    help="Inline JSON list of theme clusters")
    args = ap.parse_args()

    inv = json.loads(args.inventory.read_text(encoding="utf-8"))

    themes: list[dict[str, Any]] = []
    if args.themes_inline:
        themes = json.loads(args.themes_inline)
    elif args.themes and args.themes.is_file():
        themes = json.loads(args.themes.read_text(encoding="utf-8"))
    else:
        total = 0
        for src, tt in (inv.get("transcript_themes", {}) or {}).items():
            total += (tt or {}).get("total_sessions", 0)
        themes = [{"name": "(themes not clustered)", "count": total, "tool_split": {}}]

    digest = build_digest(inv, themes)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(digest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"Wrote {args.out} — {len(digest['skills'])} skills, "
        f"{len(digest['mcp_servers'])} MCPs, "
        f"{len(digest['hook_events'])} hook events, "
        f"{len(digest['theme_clusters'])} theme clusters",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

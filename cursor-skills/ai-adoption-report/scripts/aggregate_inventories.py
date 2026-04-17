#!/usr/bin/env python3
"""
Aggregate multiple per-teammate inventory JSON files (schema v1 or v2) from
scan_environment.py into one team-level JSON summary.

Usage:
    python aggregate_inventories.py --inputs './reports/*.json' --out team.json

Emits:
  - roster: list of (user_label, generated_at, skill counts per tool, etc.)
  - tool_adoption: how many teammates use cursor vs claude-code vs both
  - skill_registry: deduped skills with adopters + source tools they appear in
  - unique_skills: skills only one person has
  - common_skills: skills >= 2 adopters
  - mcp_adoption: MCP server usage across team (per-source)
  - hook_adoption: hook events in use (per-source)
  - rules_adoption: users with custom rules/memory
  - transcript_volume: totals and per-user per-tool session counts
  - theme_samples: sample titles per user (for the agent to cluster)
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def get_source(entry: dict[str, Any], fallback: str = "cursor") -> str:
    """Return `source` field, defaulting to cursor for legacy v1 inventories."""
    return entry.get("source") or fallback


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="+", required=True,
                    help="Glob(s) or paths to per-user inventory JSONs")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--samples-per-user", type=int, default=15,
                    help="Max transcript titles per user in output (default: 15)")
    args = ap.parse_args()

    files: list[Path] = []
    for pattern in args.inputs:
        expanded = os.path.expanduser(pattern)
        matches = [Path(p) for p in glob.glob(expanded)] or [Path(expanded)]
        files.extend(m for m in matches if m.is_file())
    if not files:
        print("No input files found.", file=sys.stderr)
        return 1

    inventories = [load(f) for f in files]

    roster: list[dict[str, Any]] = []
    # Key: (skill_name, source) -> list of users
    skill_adopters: dict[tuple[str, str], list[str]] = defaultdict(list)
    skill_descriptions: dict[tuple[str, str], list[str]] = defaultdict(list)
    skill_last_modified: dict[tuple[str, str], str] = {}
    mcp_adopters: dict[tuple[str, str], list[str]] = defaultdict(list)
    hook_events: dict[tuple[str, str], list[str]] = defaultdict(list)
    rules_adopters: list[str] = []
    theme_samples: dict[str, list[dict[str, str]]] = {}
    per_user_tool_usage: dict[str, dict[str, int]] = {}
    total_sessions_by_source: dict[str, int] = defaultdict(int)
    tool_membership: dict[str, set[str]] = defaultdict(set)  # tool -> {users}

    for inv in inventories:
        user = inv.get("user_label", "unknown")

        # Detect which tools this teammate actually uses (skills > 0 or sessions > 0)
        skills_by_source: dict[str, int] = defaultdict(int)
        for s in inv.get("skills", []):
            skills_by_source[get_source(s)] += 1

        tt = inv.get("transcript_themes") or {}
        if isinstance(tt, dict) and "samples" in tt:
            # legacy v1 layout: cursor-only, flat shape
            legacy = tt
            tt = {"cursor": legacy}

        sessions_by_source: dict[str, int] = {}
        for src, payload in tt.items():
            sessions_by_source[src] = (payload or {}).get("total_sessions", 0)
            total_sessions_by_source[src] += sessions_by_source[src]

        per_user_tool_usage[user] = {
            "cursor_skills": skills_by_source.get("cursor", 0),
            "claude_code_skills": skills_by_source.get("claude-code", 0),
            "cursor_sessions": sessions_by_source.get("cursor", 0),
            "claude_code_sessions": sessions_by_source.get("claude-code", 0),
        }

        for src in ("cursor", "claude-code"):
            if skills_by_source.get(src, 0) > 0 or sessions_by_source.get(src, 0) > 0:
                tool_membership[src].add(user)

        roster.append({
            "user_label": user,
            "generated_at": inv.get("generated_at"),
            "host": inv.get("host"),
            "schema_version": inv.get("schema_version", 1),
            "tools_used": sorted([s for s, v in skills_by_source.items() if v > 0]
                                 + [s for s in sessions_by_source
                                    if sessions_by_source[s] > 0
                                    and s not in skills_by_source]),
            "skill_count_total": len(inv.get("skills", [])),
            "skill_count_by_tool": dict(skills_by_source),
            "session_count_total": sum(sessions_by_source.values()),
            "session_count_by_tool": sessions_by_source,
            "mcp_count": len(inv.get("mcp_servers", [])),
            "has_rules": bool(inv.get("rules")),
            "hook_event_count": sum(
                len((v or {}).get("events", {}) or {})
                for v in (inv.get("hooks") or {}).values()
                if isinstance(v, dict)
            ) if isinstance(inv.get("hooks"), dict) and all(
                isinstance(v, dict) for v in (inv.get("hooks") or {}).values()
            ) else len((inv.get("hooks") or {}).get("events", {}) or {}),
        })

        for s in inv.get("skills", []):
            src = get_source(s)
            name = s.get("name", "unknown")
            key = (name, src)
            skill_adopters[key].append(user)
            if s.get("description"):
                skill_descriptions[key].append(s["description"])
            mod = s.get("modified", "")
            if mod and mod > skill_last_modified.get(key, ""):
                skill_last_modified[key] = mod

        for m in inv.get("mcp_servers", []):
            src = get_source(m)
            mcp_adopters[(m.get("name", "unknown"), src)].append(user)

        if inv.get("rules"):
            rules_adopters.append(user)

        hooks = inv.get("hooks") or {}
        # v2: {"cursor": {"events": {...}}, "claude-code": {...}}
        # v1: {"events": {...}} (cursor)
        if "events" in hooks and isinstance(hooks.get("events"), dict):
            # v1
            for event_name in hooks["events"]:
                hook_events[(event_name, "cursor")].append(user)
        else:
            for src, payload in hooks.items():
                if not isinstance(payload, dict):
                    continue
                for event_name in (payload.get("events") or {}):
                    hook_events[(event_name, src)].append(user)

        # Transcript samples
        samples_flat: list[dict[str, str]] = []
        for src, payload in tt.items():
            for sample in (payload or {}).get("samples", []) or []:
                if "source" not in sample:
                    sample = {**sample, "source": src}
                samples_flat.append(sample)
        samples_flat.sort(key=lambda s: s.get("date", ""), reverse=True)
        theme_samples[user] = samples_flat[: args.samples_per_user]

    # Build skill registry
    skill_registry: list[dict[str, Any]] = []
    # Group by name across sources, but show per-source adoption
    by_name: dict[str, dict[str, Any]] = {}
    for (name, src), adopters in skill_adopters.items():
        bucket = by_name.setdefault(name, {
            "name": name,
            "sources": [],
            "adopters": set(),
            "description_sample": "",
            "last_modified": "",
            "per_source_adopters": {},
        })
        bucket["sources"].append(src)
        bucket["per_source_adopters"][src] = sorted(set(adopters))
        bucket["adopters"].update(adopters)
        for d in skill_descriptions.get((name, src), []):
            if d and not bucket["description_sample"]:
                bucket["description_sample"] = d[:400]
                break
        mod = skill_last_modified.get((name, src), "")
        if mod > bucket["last_modified"]:
            bucket["last_modified"] = mod
    for name, bucket in by_name.items():
        bucket["sources"] = sorted(set(bucket["sources"]))
        bucket["adopter_count"] = len(bucket["adopters"])
        bucket["adopters"] = sorted(bucket["adopters"])
        skill_registry.append(bucket)
    skill_registry.sort(key=lambda s: (-s["adopter_count"], s["name"]))

    unique_skills = [s for s in skill_registry if s["adopter_count"] == 1]
    common_skills = [s for s in skill_registry if s["adopter_count"] >= 2]

    # Tool adoption summary
    cursor_users = tool_membership.get("cursor", set())
    claude_users = tool_membership.get("claude-code", set())
    both_users = cursor_users & claude_users
    tool_adoption = {
        "cursor_only": sorted(cursor_users - claude_users),
        "claude_code_only": sorted(claude_users - cursor_users),
        "both": sorted(both_users),
        "neither": sorted(
            {r["user_label"] for r in roster}
            - cursor_users - claude_users
        ),
        "counts": {
            "cursor": len(cursor_users),
            "claude-code": len(claude_users),
            "both": len(both_users),
        },
    }

    out = {
        "schema_version": 2,
        "team_size": len(inventories),
        "roster": sorted(roster, key=lambda r: r["user_label"]),
        "tool_adoption": tool_adoption,
        "skill_registry": skill_registry,
        "common_skills": common_skills,
        "unique_skills": unique_skills,
        "mcp_adoption": sorted(
            [{"server": k[0], "source": k[1],
              "users": sorted(set(v)), "count": len(set(v))}
             for k, v in mcp_adopters.items()],
            key=lambda x: -x["count"],
        ),
        "hook_adoption": sorted(
            [{"event": k[0], "source": k[1],
              "users": sorted(set(v)), "count": len(set(v))}
             for k, v in hook_events.items()],
            key=lambda x: -x["count"],
        ),
        "rules_adoption": {
            "users_with_rules": sorted(set(rules_adopters)),
            "count": len(set(rules_adopters)),
        },
        "transcript_volume": {
            "total_sessions_by_source": dict(total_sessions_by_source),
            "total_sessions": sum(total_sessions_by_source.values()),
            "per_user": per_user_tool_usage,
        },
        "theme_samples": theme_samples,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {args.out} (team={len(inventories)}, skills={len(skill_registry)}, "
          f"cursor_users={len(cursor_users)}, claude_code_users={len(claude_users)})",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

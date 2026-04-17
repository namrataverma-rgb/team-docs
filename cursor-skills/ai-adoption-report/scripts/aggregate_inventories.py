#!/usr/bin/env python3
"""
Aggregate multiple per-teammate digest JSON files into one team-level summary.

Accepts both the modern shareable `<user>-digest.json` format (preferred — no
sensitive content) and legacy `<user>-inventory.json` files (back-compat; not
recommended for real team use).

Usage:
    python aggregate_inventories.py --inputs './team-inputs/*.json' --out team.json

Emits:
  - roster: list of (user_label, generated_at, per-tool counts)
  - tool_adoption: how many teammates use cursor vs claude-code vs both
  - skill_registry: deduped skills with adopters + source tools they appear in
  - unique_skills: skills only one person has
  - common_skills: skills >= 2 adopters
  - mcp_adoption: MCP server usage across team (per-source, names only)
  - hook_adoption: hook events in use (per-source, event names only)
  - rules_adoption: users with custom rules/memory (boolean, no content)
  - transcript_volume: totals and per-user per-tool session counts
  - theme_clusters_merged: cluster-name-based rollup across teammates (no titles)
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
    hook_adopters: dict[tuple[str, str], list[str]] = defaultdict(list)
    rules_adopters: list[str] = []
    # Theme clusters: (cluster_name, user) -> count. Merged by name across team.
    theme_totals: dict[str, int] = defaultdict(int)
    theme_contributors: dict[str, list[str]] = defaultdict(list)
    per_user_tool_usage: dict[str, dict[str, int]] = {}
    total_sessions_by_source: dict[str, int] = defaultdict(int)
    tool_membership: dict[str, set[str]] = defaultdict(set)

    for inv in inventories:
        user = inv.get("user_label", "unknown")
        is_digest = "tool_summary" in inv

        # --- Per-source counts ---
        if is_digest:
            tool_summary = inv.get("tool_summary", {})
            skills_by_source: dict[str, int] = {
                t: v.get("skill_count", 0) for t, v in tool_summary.items()
            }
            sessions_by_source: dict[str, int] = {
                t: v.get("session_count", 0) for t, v in tool_summary.items()
            }
            hook_counts_by_source: dict[str, int] = {
                t: v.get("hook_event_count", 0) for t, v in tool_summary.items()
            }
        else:
            # legacy inventory
            skills_by_source = defaultdict(int)
            for s in inv.get("skills", []):
                skills_by_source[get_source(s)] += 1
            tt = inv.get("transcript_themes") or {}
            if isinstance(tt, dict) and "samples" in tt:
                tt = {"cursor": tt}
            sessions_by_source = {
                src: (p or {}).get("total_sessions", 0) for src, p in tt.items()
            }
            hooks_blob = inv.get("hooks") or {}
            hook_counts_by_source = {}
            if "events" in hooks_blob and isinstance(hooks_blob.get("events"), dict):
                hook_counts_by_source["cursor"] = len(hooks_blob["events"])
            else:
                for src, payload in hooks_blob.items():
                    if isinstance(payload, dict):
                        hook_counts_by_source[src] = len((payload.get("events") or {}))

        for src, c in sessions_by_source.items():
            total_sessions_by_source[src] += c

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
            "source_format": "digest" if is_digest else "legacy_inventory",
            "tools_used": sorted(
                {s for s, v in skills_by_source.items() if v > 0}
                | {s for s, v in sessions_by_source.items() if v > 0}
            ),
            "skill_count_total": len(inv.get("skills", [])),
            "skill_count_by_tool": dict(skills_by_source),
            "session_count_total": sum(sessions_by_source.values()),
            "session_count_by_tool": dict(sessions_by_source),
            "mcp_count": len(inv.get("mcp_servers", [])),
            "has_rules": inv.get("has_custom_rules", bool(inv.get("rules"))),
            "hook_event_count": sum(hook_counts_by_source.values()),
        })

        # --- Skills ---
        for s in inv.get("skills", []):
            src = get_source(s)
            name = s.get("name", "unknown")
            key = (name, src)
            skill_adopters[key].append(user)
            desc = s.get("description_preview") or s.get("description") or ""
            if desc:
                skill_descriptions[key].append(desc)
            mod = s.get("modified", "")
            if mod and mod > skill_last_modified.get(key, ""):
                skill_last_modified[key] = mod

        # --- MCP servers ---
        for m in inv.get("mcp_servers", []):
            src = get_source(m)
            mcp_adopters[(m.get("name", "unknown"), src)].append(user)

        # --- Rules ---
        if inv.get("has_custom_rules") or inv.get("rules"):
            rules_adopters.append(user)

        # --- Hooks ---
        if is_digest:
            for he in inv.get("hook_events", []) or []:
                hook_adopters[(he.get("event", "unknown"), he.get("source", "cursor"))].append(user)
        else:
            hooks_blob = inv.get("hooks") or {}
            if "events" in hooks_blob and isinstance(hooks_blob.get("events"), dict):
                for event_name in hooks_blob["events"]:
                    hook_adopters[(event_name, "cursor")].append(user)
            else:
                for src, payload in hooks_blob.items():
                    if not isinstance(payload, dict):
                        continue
                    for event_name in (payload.get("events") or {}):
                        hook_adopters[(event_name, src)].append(user)

        # --- Theme clusters ---
        clusters = inv.get("theme_clusters") or []
        if clusters:
            for c in clusters:
                name = c.get("name", "(unnamed)")
                count = int(c.get("count", 0))
                theme_totals[name] += count
                if count > 0:
                    theme_contributors[name].append(user)
        else:
            # legacy: cluster samples weren't provided. Skip — aggregate still works.
            pass

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
             for k, v in hook_adopters.items()],
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
        "theme_clusters_merged": sorted(
            [{"name": name, "total_count": theme_totals[name],
              "contributors": sorted(set(theme_contributors.get(name, [])))}
             for name in theme_totals],
            key=lambda x: -x["total_count"],
        ),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {args.out} (team={len(inventories)}, skills={len(skill_registry)}, "
          f"cursor_users={len(cursor_users)}, claude_code_users={len(claude_users)})",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

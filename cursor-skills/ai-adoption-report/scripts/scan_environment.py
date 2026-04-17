#!/usr/bin/env python3
"""
Scan a user's AI coding environment (Cursor and/or Claude Code) and emit a
structured JSON inventory.

Collects, for each detected tool:
  - Skills (SKILL.md files)
  - Rules / memory files
  - Hooks
  - MCP server names (tokens redacted)
  - Transcript themes (first user message only, truncated & redacted)

Designed for the `ai-adoption-report` skill. Output JSON is tagged per-entry
with `"source": "cursor" | "claude-code"` so downstream aggregation can split
teammates by tool.

Usage:
    python scan_environment.py --out inventory.json
    python scan_environment.py --tool cursor --out inventory.json
    python scan_environment.py --tool claude-code --out inventory.json
    python scan_environment.py --transcript-days 180 --out inventory.json

Safety:
  * Never dumps full transcript bodies. Only first user message per session.
  * Redacts emails, bearer tokens, long hex strings, and common secret patterns.
  * Caps each extracted string to bounded length.
"""

from __future__ import annotations

import argparse
import datetime as dt
import getpass
import json
import os
import platform
import re
import socket
import sys
from pathlib import Path
from typing import Any

HOME = Path.home()
CURSOR_DIR = HOME / ".cursor"
CLAUDE_DIR = HOME / ".claude"
MAX_BODY_CHARS = 20_000
MAX_TITLE_CHARS = 220
MAX_RULE_CHARS = 5_000

SECRET_PATTERNS = [
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[EMAIL]"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9\-_.=]+"), "bearer [TOKEN]"),
    (re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*[\"']?[^\s\"',}]+"),
     r"\1=[REDACTED]"),
    (re.compile(r"\b[a-f0-9]{32,}\b"), "[HEX]"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), "[OPENAI_KEY]"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"), "[GH_TOKEN]"),
]

SOURCES = ("cursor", "claude-code")


# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------

def redact(text: str) -> str:
    if not text:
        return text
    for pat, repl in SECRET_PATTERNS:
        text = pat.sub(repl, text)
    return text


def shorten_path(p: Path) -> str:
    return str(p).replace(str(HOME), "~")


def parse_frontmatter(md: str) -> tuple[dict[str, str], str]:
    if not md.startswith("---"):
        return {}, md
    end = md.find("\n---", 3)
    if end < 0:
        return {}, md
    raw = md[3:end].strip()
    body = md[end + 4 :].lstrip("\n")
    meta: dict[str, str] = {}
    key: str | None = None
    buf: list[str] = []
    for line in raw.splitlines():
        if re.match(r"^[A-Za-z_][\w\-]*\s*:", line):
            if key is not None:
                meta[key] = " ".join(buf).strip()
            key, _, val = line.partition(":")
            key = key.strip()
            buf = [val.strip().lstrip(">|").strip()]
        else:
            buf.append(line.strip())
    if key is not None:
        meta[key] = " ".join(buf).strip()
    return meta, body


def section_after(body: str, *keywords: str) -> str | None:
    lines = body.splitlines()
    buf: list[str] = []
    capture = False
    for line in lines:
        h = re.match(r"^(#{1,6})\s+(.*)$", line)
        if h:
            title = h.group(2).strip().lower()
            if capture:
                break
            if any(k in title for k in keywords):
                capture = True
                continue
        elif capture:
            buf.append(line)
    return ("\n".join(buf).strip() or None) if capture else None


def timestamps(path: Path) -> dict[str, str]:
    try:
        st = path.stat()
        created_ts = st.st_birthtime if hasattr(st, "st_birthtime") else st.st_ctime
        return {
            "created": dt.datetime.fromtimestamp(created_ts).date().isoformat(),
            "modified": dt.datetime.fromtimestamp(st.st_mtime).date().isoformat(),
        }
    except Exception:
        return {"created": "", "modified": ""}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


# -----------------------------------------------------------------------------
# Tool detection
# -----------------------------------------------------------------------------

def detect_tools() -> list[str]:
    """Return list of tool names that appear installed on this machine."""
    found: list[str] = []
    if (CURSOR_DIR / "skills").is_dir() or (CURSOR_DIR / "hooks.json").is_file():
        found.append("cursor")
    if CLAUDE_DIR.is_dir() or (HOME / ".claude.json").is_file():
        found.append("claude-code")
    return found


# -----------------------------------------------------------------------------
# Skills scanning (shared logic)
# -----------------------------------------------------------------------------

def scan_skills_at(root: Path, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not root.is_dir():
        return out
    for skill_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue
        raw = skill_md.read_text(encoding="utf-8", errors="replace")
        meta, body = parse_frontmatter(raw)
        body_trim = body[:MAX_BODY_CHARS]
        entry = {
            "source": source,
            "name": meta.get("name") or skill_dir.name,
            "path": shorten_path(skill_md),
            "description": redact(meta.get("description", "")),
            "body_markdown": redact(body_trim),
            "line_count": raw.count("\n") + 1,
            "files": sorted(
                str(p.relative_to(skill_dir))
                for p in skill_dir.rglob("*")
                if p.is_file() and p.name != ".DS_Store"
            )[:50],
            "has_scripts": (skill_dir / "scripts").is_dir(),
            "section_limitations": redact(
                section_after(body, "limitation", "caveat", "known issue",
                              "constraint", "anti-pattern", "what this doesn't") or ""
            ),
            "section_challenges": redact(
                section_after(body, "challenge", "trade-off", "gotcha",
                              "troubleshoot", "pitfall") or ""
            ),
            "section_features": redact(
                section_after(body, "feature", "capabilit", "what this does",
                              "overview", "quick start", "workflow", "what it does") or ""
            ),
            **timestamps(skill_md),
        }
        out.append(entry)
    return out


# -----------------------------------------------------------------------------
# Rules / memory scanning
# -----------------------------------------------------------------------------

def scan_rules_cursor() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    root = CURSOR_DIR / "rules"
    if root.is_dir():
        for f in sorted(root.rglob("*.md*")):
            if not f.is_file():
                continue
            out.append({
                "source": "cursor",
                "kind": "rule",
                "path": shorten_path(f),
                "content": redact(f.read_text(encoding="utf-8", errors="replace")[:MAX_RULE_CHARS]),
                **timestamps(f),
            })
    return out


def scan_rules_claude() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    candidates = [
        (CLAUDE_DIR / "CLAUDE.md", "memory"),
        (HOME / "CLAUDE.md", "memory"),
    ]
    for p, kind in candidates:
        if p.is_file():
            out.append({
                "source": "claude-code",
                "kind": kind,
                "path": shorten_path(p),
                "content": redact(p.read_text(encoding="utf-8", errors="replace")[:MAX_RULE_CHARS]),
                **timestamps(p),
            })
    memories = CLAUDE_DIR / "memories"
    if memories.is_dir():
        for f in sorted(memories.rglob("*.md*")):
            if not f.is_file():
                continue
            out.append({
                "source": "claude-code",
                "kind": "memory",
                "path": shorten_path(f),
                "content": redact(f.read_text(encoding="utf-8", errors="replace")[:MAX_RULE_CHARS]),
                **timestamps(f),
            })
    return out


# -----------------------------------------------------------------------------
# Hooks scanning
# -----------------------------------------------------------------------------

def scan_hooks_cursor() -> dict[str, Any]:
    path = CURSOR_DIR / "hooks.json"
    if not path.is_file():
        return {}
    data = load_json(path)
    if not isinstance(data, dict):
        return {"error": "unparseable hooks.json"}
    summary: dict[str, Any] = {"source": "cursor", "version": data.get("version"), "events": {}}
    for event, items in (data.get("hooks") or {}).items():
        summary["events"][event] = [
            {"command": redact(str(i.get("command", ""))[:300])} for i in (items or [])
        ]
    return summary


def scan_hooks_claude() -> dict[str, Any]:
    path = CLAUDE_DIR / "settings.json"
    if not path.is_file():
        return {}
    data = load_json(path)
    if not isinstance(data, dict):
        return {"error": "unparseable settings.json"}
    hooks = data.get("hooks") or {}
    if not hooks:
        return {}
    summary: dict[str, Any] = {"source": "claude-code", "events": {}}
    for event, items in hooks.items():
        flattened: list[dict[str, str]] = []
        for entry in items or []:
            for h in entry.get("hooks", []) if isinstance(entry, dict) else []:
                flattened.append({
                    "matcher": redact(str(entry.get("matcher", "")))[:120],
                    "command": redact(str(h.get("command", ""))[:300]),
                })
        summary["events"][event] = flattened
    return summary


# -----------------------------------------------------------------------------
# MCP scanning
# -----------------------------------------------------------------------------

def _summarize_mcp(servers: dict[str, Any], source: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for name, cfg in (servers or {}).items():
        cmd = cfg.get("command") if isinstance(cfg, dict) else ""
        args = cfg.get("args", []) if isinstance(cfg, dict) else []
        out.append({
            "source": source,
            "name": name,
            "command": redact(str(cmd))[:120],
            "args_summary": redact(" ".join(str(a) for a in args))[:200],
        })
    return out


def scan_mcp_cursor() -> list[dict[str, str]]:
    path = CURSOR_DIR / "mcp.json"
    if not path.is_file():
        return []
    data = load_json(path)
    if not isinstance(data, dict):
        return []
    servers = data.get("mcpServers") or data.get("servers") or {}
    return _summarize_mcp(servers, "cursor")


def scan_mcp_claude() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for path in (HOME / ".claude.json", CLAUDE_DIR / "settings.json"):
        if not path.is_file():
            continue
        data = load_json(path)
        if not isinstance(data, dict):
            continue
        servers = data.get("mcpServers") or {}
        out.extend(_summarize_mcp(servers, "claude-code"))
    return out


# -----------------------------------------------------------------------------
# Transcripts
# -----------------------------------------------------------------------------

def _extract_first_user_text_cursor(line: dict) -> str | None:
    if line.get("role") != "user":
        return None
    content = (line.get("message") or {}).get("content")
    return _flatten_content(content)


def _extract_first_user_text_claude(line: dict) -> str | None:
    if line.get("type") != "user":
        return None
    msg = line.get("message") or {}
    if msg.get("role") != "user":
        return None
    return _flatten_content(msg.get("content"))


def _flatten_content(content: Any) -> str | None:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                return part.get("text", "")
    return None


def _first_user_message(jsonl_path: Path, extractor) -> str:
    try:
        with jsonl_path.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                text = extractor(rec)
                if text is None:
                    continue
                text = re.sub(r"</?user_query>", "", text).strip()
                text = re.sub(r"\s+", " ", text)
                if text:
                    return redact(text)[:MAX_TITLE_CHARS]
        return ""
    except Exception:
        return ""


def _scan_transcripts(root: Path, pattern: str, days: int, extractor, source: str) -> dict[str, Any]:
    if not root.is_dir():
        return {"source": source, "window_days": days, "total_sessions": 0, "samples": []}
    cutoff = dt.datetime.now() - dt.timedelta(days=days)
    samples: list[dict[str, str]] = []
    for jsonl in root.rglob("*.jsonl"):
        # Extra Cursor filter: only agent-transcripts sub-trees
        if source == "cursor" and "agent-transcripts" not in jsonl.parts:
            continue
        try:
            mtime = dt.datetime.fromtimestamp(jsonl.stat().st_mtime)
        except Exception:
            continue
        if mtime < cutoff:
            continue
        title = _first_user_message(jsonl, extractor)
        if not title:
            continue
        samples.append({
            "source": source,
            "date": mtime.date().isoformat(),
            "title": title,
            "transcript_id": jsonl.stem,
        })
    samples.sort(key=lambda s: s["date"], reverse=True)
    return {
        "source": source,
        "window_days": days,
        "total_sessions": len(samples),
        "samples": samples,
    }


def scan_transcripts_cursor(days: int) -> dict[str, Any]:
    return _scan_transcripts(
        CURSOR_DIR / "projects", "*.jsonl", days,
        _extract_first_user_text_cursor, "cursor",
    )


def scan_transcripts_claude(days: int) -> dict[str, Any]:
    return _scan_transcripts(
        CLAUDE_DIR / "projects", "*.jsonl", days,
        _extract_first_user_text_claude, "claude-code",
    )


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def run_scan(tools: list[str], transcript_days: int) -> dict[str, Any]:
    skills: list[dict[str, Any]] = []
    rules: list[dict[str, Any]] = []
    hooks: dict[str, Any] = {}
    mcps: list[dict[str, Any]] = []
    transcripts: dict[str, Any] = {}

    if "cursor" in tools:
        skills.extend(scan_skills_at(CURSOR_DIR / "skills", "cursor"))
        rules.extend(scan_rules_cursor())
        cursor_hooks = scan_hooks_cursor()
        if cursor_hooks:
            hooks["cursor"] = cursor_hooks
        mcps.extend(scan_mcp_cursor())
        transcripts["cursor"] = scan_transcripts_cursor(transcript_days)

    if "claude-code" in tools:
        skills.extend(scan_skills_at(CLAUDE_DIR / "skills", "claude-code"))
        rules.extend(scan_rules_claude())
        claude_hooks = scan_hooks_claude()
        if claude_hooks:
            hooks["claude-code"] = claude_hooks
        mcps.extend(scan_mcp_claude())
        transcripts["claude-code"] = scan_transcripts_claude(transcript_days)

    return {
        "schema_version": 2,
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "user_label": getpass.getuser(),
        "host": socket.gethostname(),
        "os": f"{platform.system()} {platform.release()}",
        "tools_scanned": tools,
        "tools_detected_on_disk": detect_tools(),
        "skills": skills,
        "rules": rules,
        "hooks": hooks,
        "mcp_servers": mcps,
        "transcript_themes": transcripts,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=None,
                    help="Output path (default: stdout)")
    ap.add_argument("--tool", choices=["cursor", "claude-code", "both", "auto"],
                    default="auto",
                    help="Which tool(s) to scan. `auto` (default) detects installed tools.")
    ap.add_argument("--transcript-days", type=int, default=60,
                    help="Look-back window for transcripts (default: 60 days)")
    ap.add_argument("--user-label", default=None,
                    help="Override user label (default: $USER on machine)")
    args = ap.parse_args()

    if args.tool == "auto":
        tools = detect_tools() or ["cursor"]  # default to cursor if nothing detected
    elif args.tool == "both":
        tools = list(SOURCES)
    else:
        tools = [args.tool]

    inv = run_scan(tools, args.transcript_days)
    if args.user_label:
        inv["user_label"] = args.user_label

    payload = json.dumps(inv, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
        by_src = ", ".join(
            f"{s}:{sum(1 for k in inv['skills'] if k['source']==s)} skills / "
            f"{(inv['transcript_themes'].get(s) or {}).get('total_sessions', 0)} sessions"
            for s in tools
        )
        print(f"Wrote {args.out} ({by_src})", file=sys.stderr)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())

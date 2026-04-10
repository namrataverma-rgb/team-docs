#!/usr/bin/env python3
"""Verify combined FNPL MBR HTML against template contracts (Slides 9, 12, 13)."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def fail(msgs: list[str]) -> int:
    for m in msgs:
        print(m, file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("html_path", type=Path, help="Path to FNPL_MBR_<MonYY>.html")
    args = ap.parse_args()
    path: Path = args.html_path
    if not path.is_file():
        return fail([f"Not a file: {path}"])

    text = path.read_text(encoding="utf-8", errors="replace")
    errs: list[str] = []

    # --- Slide 9: chart id + CSS targets measured chart container ---
    if 'id="chart9"' not in text and "id='chart9'" not in text:
        errs.append("Slide 9: missing id=\"chart9\" on chart container (template uses #slide9 #chart9).")
    if "#slide9 #chart9" not in text and "#chart9" not in text:
        errs.append("Slide 9: expected CSS targeting chart container (#slide9 #chart9).")

    # --- Slide 12: mandatory script markers (see SKILL.md) ---
    s12_markers = [
        ("void document.getElementById('slide12').offsetHeight", "layout commit before Plotly"),
        ("getBoundingClientRect", "measured chart div"),
        ("yAxisTop", "shared Y max across four Vantage panels"),
        ("range:[0,yAxisTop]", "shared yaxis.range (not per-panel autoscale)"),
        ("responsive:false", "Plotly config (slide 12)"),
    ]
    for lit, why in s12_markers:
        if lit not in text:
            errs.append(f"Slide 12: missing marker ({why}): {lit!r}")

    # --- Slide 13: mandatory script markers ---
    s13_markers = [
        ("plotJobs", "two-phase plot queue"),
        ("void row.offsetHeight", "layout before measure"),
        ("padSeriesToMobs", "MoB padding"),
        ("type:'linear'", "numeric x-axis"),
        ("responsive:false", "Plotly config (slide 13)"),
    ]
    for lit, why in s13_markers:
        if lit not in text:
            errs.append(f"Slide 13: missing marker ({why}): {lit!r}")

    # --- Slide 12 DATA: every row must have tl (total_loans) ---
    m = re.search(r"var\s+SLIDE12_DATA\s*=\s*(\[[\s\S]*?\])\s*;", text)
    if not m:
        errs.append("Slide 12: could not find var SLIDE12_DATA = [...];")
    else:
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError as e:
            errs.append(f"Slide 12: SLIDE12_DATA is not valid JSON: {e}")
            data = None
        if data is not None:
            for i, row in enumerate(data):
                if not isinstance(row, dict):
                    errs.append(f"Slide 12: SLIDE12_DATA[{i}] is not an object.")
                    continue
                if "tl" not in row:
                    errs.append(
                        f"Slide 12: SLIDE12_DATA[{i}] missing required field 'tl' (total_loans). "
                        f"Keys: {list(row.keys())}"
                    )
                elif row["tl"] is None:
                    errs.append(f"Slide 12: SLIDE12_DATA[{i}].tl is null (use a number from SQL total_loans).")

    if errs:
        print(f"verify_fnpl_mbr_html.py: {len(errs)} failure(s) in {path}", file=sys.stderr)
        return fail(errs)

    print(f"OK: {path} (Slides 9, 12, 13 checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

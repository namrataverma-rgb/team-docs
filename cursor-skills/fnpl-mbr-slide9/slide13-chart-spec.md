# Slide 13 — DPD30+ by term charts (canonical JS behavior)

**Status: MANDATORY.** The implementation lives in [template-slide13.html](template-slide13.html) (Plotly). Agents replace `{{PLACEHOLDER}}` tokens only; do not rewrite chart logic unless this spec changes.

**Enforcement:** [SKILL.md](SKILL.md) § *Step 3F — Build HTML (Slide 13)* requires a **marker verification** (grep for `plotJobs`, `void row.offsetHeight`, `padSeriesToMobs`, `type:'linear'`, `responsive:false`) before merging Slide 13 into the deck, and § *3C.1 — Preview* requires a **visual** Slide 13 x-axis spot-check (M0 through M{MOB_CAP}, no clipped ticks).

## Shared legend vs cohort tables

Build the **color legend** from **sorted unique `origination_month` values in `{{COHORT_DATA_JSON}}`**, restricted to terms in `{{TERMS_JSON}}`. Do **not** build the legend from the union of all DPD rows across terms — that can add vintages (e.g. Jan-26) that appear in raw DPD for only one term but **do not** appear in the cohort summary tables, which confuses readers.

## Per-term Y-axis (avoid scale distortion)

Each **term** panel (e.g. 3-month vs 6-month) has **its own** Y range computed from **that term’s** `rate_30dpd` (or equivalent) series only.

Do **not** use a single global max across terms for both charts — that compresses or stretches one term’s panel incorrectly.

### 3-month vs 6-month

- **3-month:** DPD30+ is often **0% until M3+** on the curve; a tall 0–100% or 0–15% axis makes the chart look “empty.” Use a **tighter ceiling** (cap around **10%** max): e.g. `yTop = min(10, max(yMax * 1.48 + 1.05, 4))` so small non-zero rates use most of the vertical space. Use `dtick` 1 when `yTop <= 8`.
- **6-month:** `yTop = min(100, yMax * 1.32 + 0.65)` (typical larger rates).

If `yMax <= 0`, use a small default ceiling (~5%) so the empty chart still renders sensibly.

### Headroom for smooth curves

Charts use **spline** lines (`shape: 'spline'`). Splines can arc slightly above the max data point — padding is included in `yTop`. Use `connectgaps: false` on traces.

## X-axis (Month on Books) — all terms

- Build the MoB list `M0`…`M{MOB_CAP}` from `{{MOB_CAP}}` (same for 3-month and 6-month panels).
- **Pad each vintage’s series** to that full list: use `null` for MoB buckets with no row in the query so lines span the full horizon.
- Use **numeric linear x** (`0`…`MOB_CAP`) with `tickmode: 'array'`, `tickvals` = those integers, `ticktext` = `M0`…`M{MOB_CAP}`, and a slightly padded `range` (e.g. `[-0.35, MOB_CAP + 0.35]`). Category-only axes plus `responsive` resizing still dropped or mis-ordered MoB labels on the 3-month panel; linear + explicit ticks is stable. Hovers use `customdata` so the label reads `M3`, not `3`.
- Set `config.responsive: false` and pass an explicit `layout.width` from the chart div so export/HTML does not reflow ticks.
- **Build all term panels in the DOM first, then call `Plotly.newPlot` for each.** If the first chart is plotted while the flex row only has one child, `getBoundingClientRect()` is ~full slide width; the plot stays that wide and `overflow: hidden` on the chart box clips the right side (M3+ ticks look missing; a lone “M” from a cut-off `M5`). Force layout (`void row.offsetHeight`) after all boxes are appended, then measure each chart div.

## Line shape

Use **smooth spline** curves: `line: { shape: 'spline', smoothing: ~1.22, width: 2.5 }` — **not** jagged linear segments, unless this spec is explicitly revised.

## Other

- MoB cap, vintage colors, legend, and term omission rules remain as in [SKILL.md](SKILL.md) § Slide 13.
- Chart `height` / `margin` in the template take precedence over older SKILL prose if they differ.

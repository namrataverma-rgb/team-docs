---
name: fnpl-mbr-slide9
description: >-
  Generate FNPL Monthly Business Review Cover + Slides 9–13 (Cover
  + Application Profile + Funded Loans Profile + Monthly Performance
  + DPD30+ by Vantage Group + DPD30+ by Term). Extracts data from Databricks,
  validates against prior months and AIG reference tables, creates high-resolution
  HTML slides, preserves all monthly artifacts, and (when relevant) interactive deck
  conventions: presentation-style page layout, Add Slide modal templates, Export HTML.
  Use when the user mentions MBR, monthly business review, FNPL slide 1,
  FNPL slide 9, FNPL slide 10, FNPL slide 11, FNPL slide 12, FNPL slide 13,
  FNPL application profile, FNPL funded loans profile,
  FNPL monthly performance, DPD30+ by vantage, DPD30+ by term, Add New Slide,
  Key Takeaway slide, Export HTML deck, or team-docs fnpl-mbr viewer.
---

# FNPL MBR — Cover + Slides 9–13 Workflow

> **SAFETY: All Databricks queries are READ-ONLY (SELECT). NEVER execute DROP, DELETE, INSERT, UPDATE, CREATE, ALTER, or any DDL/DML on user tables. Only read data.**

> **PERFORMANCE: Parallelize independent steps wherever possible. See the execution plan below.**

> **AUTO-SWITCH: After receiving user input at ANY Plan-mode checkpoint (Step 0 questions, Step 2C verdict acknowledgment, Step 3C commentary choice, missing-column decisions), the agent MUST immediately switch back to Agent mode and continue execution WITHOUT waiting for the user to manually approve the mode switch. Never pause between Plan→Agent transitions — treat user input as implicit approval to proceed.**

> **AUTO-RUN QUERIES: Execute ALL Databricks SQL queries automatically without asking the user for confirmation before each query. The `execute_sql` tool may prompt for mutation confirmation — since all queries in this skill are SELECT-only, always proceed. Batch and fire all independent queries in parallel. Do NOT present queries to the user and ask "shall I run this?" — just run them.**

## MANDATORY TEMPLATE ENFORCEMENT — CRITICAL

> **THIS IS THE #1 RULE OF THIS SKILL. VIOLATION PRODUCES BROKEN OUTPUT.**

Every data-driven slide (9, 10, 11, 12, 13) has a **self-contained HTML template file**. When building slide HTML:

1. **READ** the template file verbatim using the Read tool
2. **REPLACE** only the `{{PLACEHOLDER}}` tokens with computed data values
3. **NEVER** modify any CSS, HTML structure, or JavaScript from the template
4. **NEVER** generate slide HTML "from scratch" using the design descriptions below — those descriptions are documentation for HUMANS, not build instructions for the agent
5. **NEVER** rearrange, merge, or simplify the CSS from templates
6. **Slide 11 table & Slide 13 term charts** — Follow the canonical specs. Do not improvise metric order, section titles, roll-rate label text, or chart scaling:
   - **[slide11-table-spec.md](slide11-table-spec.md)** — table rows, `{{TABLE_SUBTITLE}}`, sub-headers, `# Roll rate -> 30D to CO` / `$ Roll rate -> 30D to CO`, typography parity with Slide 10 (`#slide10 .tbl`)
   - **[slide13-chart-spec.md](slide13-chart-spec.md)** — full Plotly contract for Slide 13 (per-term Y-axis, spline, **X-axis**, **two-phase render**). Implementation **must** come from **[template-slide13.html](template-slide13.html)** in this skill — read that file from disk each run; replace `{{PLACEHOLDER}}` tokens only.
   - **Slide 13 regressions that are FORBIDDEN** (they break the 3-month panel): calling `Plotly.newPlot` before every `chart-box` exists in the row (flex measures full width once → clipped x-axis); using a **single global Y max** across terms; swapping in hand-written or cached JS instead of the current template.
   - **Monthly HTML Git archive:** Each successful run must also add `exports/fnpl-mbr/FNPL_MBR_<MonYY>.html` to `https://github.intuit.com/SBG-Risk-Analytics-Insight/cg-credit-risk` (see **Step 5**), unless the user or environment blocks git.

### Template Registry

| Slide | Template File | Container ID | Placeholders |
|-------|--------------|-------------|-------------|
| 9 | `template.html` | `#slide9` | `{{MBR_MONTH}}`, `{{LATEST_MONTH_LABEL}}`, `{{MONTHS_JSON}}`, `{{BARS_JSON}}`, `{{APPROVAL_JSON}}`, `{{KPI_*}}`, `{{TABLE_*}}`, `{{DATA_DATE}}`, `{{SOURCE_TABLE}}` — `{{DATA_DATE}}` = Question **2** cutoff (formatted); SQL uses `{{CUTOFF_DATE}}` in [queries.md](queries.md) |
| 10 | `template-slide10.html` | `#slide10` | `{{MBR_MONTH}}`, `{{TABLE_HEADERS}}`, `{{TABLE_ROWS}}`, `{{TABLE_MONTH_COLS}}`, `{{COMMENTARY_DATA}}`, `{{DATA_DATE}}`, `{{SOURCE_TABLE}}` |
| 11 | `template-slide11.html` | `#slide11` | `{{MBR_MONTH}}`, `{{AS_OF_DATE}}`, `{{TABLE_SUBTITLE}}`, `{{TABLE_HEADERS}}`, `{{TABLE_ROWS}}`, `{{TABLE_MONTH_COLS}}`, `{{DATA_DATE}}`, `{{SOURCE_TABLE}}` — `{{AS_OF_DATE}}` = `date_sub({{CUTOFF_DATE}}, 3)` formatted; see **Data cutoff contract** |
| 12 | `template-slide12.html` | `#slide12` | `{{DATA_JSON}}`, `{{MOB_CAP}}`, `{{BASE_TABLE}}`, `{{MBR_MONTH}}` — SQL in [queries-slide12.md](queries-slide12.md): **`{{BASE_TABLE}}`** + **`{{MOB_CAP}}`** only; **no `asofDate` filter** — joins on explicit `daysonbooks IN (1,30,60,…)` values; charge-off counts as delinquent |
| 13 | `template-slide13.html` | `#slide13` | `{{DPD_DATA_JSON}}`, `{{COHORT_DATA_JSON}}`, `{{MOB_CAP}}`, `{{TERMS_JSON}}`, `{{TERMS_SUBTITLE}}`, `{{BASE_TABLE}}`, `{{MBR_MONTH}}` — SQL in [queries-slide13.md](queries-slide13.md): same **`{{BASE_TABLE}}`** + **`{{MOB_CAP}}`** only, no cutoff, same charge-off rule |

### CSS Scoping Rule

Each template's CSS is **scoped under its slide container ID** (e.g., `#slide9 .chart-area`, `#slide12 .chart-box`, `#slide13 .chart-box`). This is CRITICAL because Slides 12 and 13 share class names (`.chart-box`, `.chart-div`, `.shared-legend`) but with DIFFERENT CSS properties. Without ID scoping, whichever slide's CSS loads last wins and the other slide breaks.

**When combining all slides into one HTML file:**
- Each slide's `<style>` block is already scoped — append them all to a single `<style>` tag
- Each slide's `<div class="slide" id="slideN">` keeps its unique ID
- Each slide's `<script>` block is appended to a combined `<script>` section
- Element IDs are unique per slide (e.g., `legend12` vs `legend13`, not `legend` for both)
- NEVER flatten, merge, or deduplicate CSS rules across slides — the scoping MUST remain

### Combined HTML Assembly Procedure (Step 5)

```
1. Create outer HTML shell:
   - <head> with shared font @import (Inter + Poppins), shared body/reset CSS
   - NO slide-specific CSS in the shared section
2. For EACH slide (in slide order):
   a. Read the template file
   b. Extract its <style> block → append to combined <style> (CSS is ID-scoped, safe to combine)
   c. Extract the <div class="slide" id="slideN"> → wrap in a slide container, append to <body>
   d. Extract its <script> block → wrap in an IIFE or append to combined <script>
   e. Replace all {{PLACEHOLDER}} tokens with computed values — including **`{{CUTOFF_DATE}}`** in every inlined query fragment so `app_date`, AIG bounds, and `date_sub` servicing dates match Step 0 Question **2**
3. Static slides (1, 2, 3, 4, 5) use their Reference HTML from this SKILL.md directly (inline styles, no class conflicts)
4. NEVER regenerate CSS from the design descriptions — ONLY use template files
```

**If you find yourself writing CSS properties like `flex`, `grid`, `padding`, `margin`, `font-size` etc. for a data slide — STOP. You are violating this rule. Go read the template file instead.**

---

## Global Design System

**Fonts**:
- **Google Fonts import**: `Inter` (body/tables) + `Poppins` (headers)
- All `<h1>` elements use `font-family: 'Poppins', sans-serif`
- All other text uses `font-family: 'Inter', sans-serif`

**Slide canvas**: 1280×720 (16:9), white card on gray `#CBD5E1` background.

**Chart-to-table spacing**: `.chart-area` has `margin-bottom: 10px` to leave a gap between the Plotly chart and the data table below it (applies to Slide 9).

---

## Slide 1 — Cover (Static)

This slide is **fully static** — no data queries, no placeholders, no monthly changes. It is always placed as the first slide in the combined HTML output.

**Background**: `#0F172A` (dark navy), full 1280×720 canvas.

**Brand bar**: The official **Intuit 1-line ecosystem lock-up** logo (reversed/white version for dark backgrounds). The SVG file `intuit-ecosystem-white.svg` is served alongside the HTML. It contains:
- INTUIT wordmark in white
- TurboTax (red icon), Credit Karma (green icon), QuickBooks (green icon), Mailchimp (yellow icon) — all with white brand name text

Logo is rendered as `<img src="intuit-ecosystem-white.svg" style="height:34px">` in a top-left padded div (`padding: 28px 48px 0`).

**Title**: "Monthly Risk Performance Overview" — `font-family: 'Poppins'`, 52px, bold, white, `line-height: 1.15`. Displayed on two lines with a `<br>` after "Performance".

**Subtitle**: "Consumer Risk Team" — `font-family: 'Inter'`, 16px, semi-bold, `color: #cbd5e1`.

**Layout**: Flex column, title centered vertically in the remaining space below the brand bar.

### Slide 1 — Reference HTML

```html
<div class="slide slide-fixed" id="slide1" style="background:#0F172A;display:flex;flex-direction:column;justify-content:flex-start;padding:0;">
  <div style="padding:28px 48px 0;">
    <img src="intuit-ecosystem-white.svg" alt="Intuit ecosystem" style="height:34px;">
  </div>
  <div style="flex:1;display:flex;flex-direction:column;justify-content:center;padding:0 48px;">
    <h1 style="font-family:'Poppins',sans-serif;font-size:52px;font-weight:700;color:#fff;line-height:1.15;margin:0 0 24px;">Monthly Risk Performance<br>Overview</h1>
    <p style="font-family:'Inter',sans-serif;font-size:16px;font-weight:600;color:#cbd5e1;margin:0;">Consumer Risk Team</p>
  </div>
</div>
```

**Dependency**: `intuit-ecosystem-white.svg` must be in the same directory as the HTML file. A copy is stored in this skill folder.

---

## Slide 2 — Agenda (Dynamic)

A static-layout slide whose **product order** changes based on user input from **Step 0 Question 3 — Agenda product order** (`{{PRODUCT_ORDER}}`).

**Background**: White (`#FFFFFF`)
**Canvas**: 1280 × 720

**Elements**:

1. **Title**: "Agenda" — top-left, `Poppins` 36px, bold, `#0F172A`, bottom margin 32px.
2. **Decorative accent**: 4px-wide vertical bar on the left edge of the agenda card, `#0F172A` (dark navy), `border-radius: 2px`, stretches full height of the card.
3. **Agenda card**: Rounded rectangle (`border-radius: 12px`, `background: #F8FAFC`, `border: 1px solid #E2E8F0`), `padding: 32px 40px`, `flex: 1` to fill available space.
4. **Agenda items** (inside the card, each separated by `margin-bottom: 24px`):
   - **Executive Summary & Follow ups** — `Inter` 18px semi-bold `#334155`, time "10 mins" in 14px `#64748B`
   - **Credit Portfolio review by Product** — same style, time "35 mins"
     - Indented sub-items from `{{PRODUCT_ORDER}}`, each rendered as `— <PRODUCT>` in `Inter` 15px `#64748B`, `padding-left: 24px`, `gap: 4px`
   - **Fraud Update** — same style, time "10 mins" (last item, no bottom margin)
5. **Footer**: "Consumer Risk Team | {{MBR_MONTH_LABEL}}" — bottom-right, `Inter` 12px, `#94A3B8`, `margin-top: 16px`.

**Build rule**: The agent constructs this slide at **Step 3** alongside other slides. The only dynamic parts are:
- The product list order under "Credit Portfolio review by Product" (from `{{PRODUCT_ORDER}}`)
- The footer month label (from `{{MBR_MONTH_LABEL}}`)

### Slide 2 — Reference HTML

Replace `{{PRODUCT_ORDER}}` sub-items and `{{MBR_MONTH_LABEL}}` at build time.

```html
<div class="slide slide-fixed" id="slide2" style="background:#FFFFFF;display:flex;flex-direction:column;padding:48px 56px 32px;">
  <h1 style="font-family:'Poppins',sans-serif;font-size:36px;font-weight:700;color:#0F172A;margin:0 0 32px;">Agenda</h1>
  <div style="display:flex;flex:1;align-items:flex-start;">
    <div style="width:4px;background:#0F172A;border-radius:2px;align-self:stretch;margin-right:0;"></div>
    <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:32px 40px;flex:1;">
      <div style="margin-bottom:24px;">
        <div style="font-family:'Inter',sans-serif;font-size:18px;font-weight:600;color:#334155;margin-bottom:4px;">Executive Summary & Follow ups</div>
        <div style="font-family:'Inter',sans-serif;font-size:14px;color:#64748B;">10 mins</div>
      </div>
      <div style="margin-bottom:24px;">
        <div style="font-family:'Inter',sans-serif;font-size:18px;font-weight:600;color:#334155;margin-bottom:8px;">Credit Portfolio review by Product</div>
        <div style="font-family:'Inter',sans-serif;font-size:14px;color:#64748B;margin-bottom:8px;">35 mins</div>
        <div style="padding-left:24px;display:flex;flex-direction:column;gap:4px;">
          <!-- {{PRODUCT_ORDER}} — replace these lines dynamically -->
          <div style="font-family:'Inter',sans-serif;font-size:15px;color:#64748B;">— FNPL</div>
          <div style="font-family:'Inter',sans-serif;font-size:15px;color:#64748B;">— PCA</div>
          <div style="font-family:'Inter',sans-serif;font-size:15px;color:#64748B;">— RAD</div>
          <div style="font-family:'Inter',sans-serif;font-size:15px;color:#64748B;">— TTFA</div>
        </div>
      </div>
      <div>
        <div style="font-family:'Inter',sans-serif;font-size:18px;font-weight:600;color:#334155;margin-bottom:4px;">Fraud Update</div>
        <div style="font-family:'Inter',sans-serif;font-size:14px;color:#64748B;">10 mins</div>
      </div>
    </div>
  </div>
  <div style="text-align:right;font-family:'Inter',sans-serif;font-size:12px;color:#94A3B8;margin-top:16px;">Consumer Risk Team | {{MBR_MONTH_LABEL}}</div>
</div>
```

---

## Slide 4 — Agenda Transition (FNPL Highlight)

This slide is a **copy of Slide 2 (Agenda)** with the currently-presenting product highlighted. It is placed between the Executive Summary (Slide 3) and Slide 9. Since this skill only generates FNPL slides, the highlighted product is always **FNPL**.

**Highlighting rules**:
- The active product (**FNPL**) is displayed in bold, dark color (`#0F172A`), with a blue play arrow (`▶`, `color: #236CFF`) replacing the dash prefix.
- All other items (Executive Summary, PCA, RAD, TTFA, Fraud Update) are **dimmed** to `#CBD5E1` (light gray).
- The parent header "Credit Portfolio review by Product" stays in normal color (`#334155`).

**Dynamic behavior**: The highlighted product and the product order both follow `{{PRODUCT_ORDER}}` from Step 0 Question 3. The first product in the FNPL skill is always FNPL.

### Slide 4 — Reference HTML

Same structure as Slide 2, with dimming applied to non-active items. Replace `{{MBR_MONTH_LABEL}}` at build time.

```html
<div class="slide slide-fixed" id="slide4" style="background:#FFFFFF;display:flex;flex-direction:column;padding:48px 56px 32px;">
  <h1 style="font-family:'Poppins',sans-serif;font-size:36px;font-weight:700;color:#0F172A;margin:0 0 32px;">Agenda</h1>
  <div style="display:flex;flex:1;align-items:flex-start;">
    <div style="width:4px;background:#0F172A;border-radius:2px;align-self:stretch;margin-right:0;"></div>
    <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:32px 40px;flex:1;">
      <div style="margin-bottom:24px;">
        <div style="font-family:'Inter',sans-serif;font-size:18px;font-weight:600;color:#CBD5E1;margin-bottom:4px;">Executive Summary & Follow ups</div>
        <div style="font-family:'Inter',sans-serif;font-size:14px;color:#CBD5E1;">10 mins</div>
      </div>
      <div style="margin-bottom:24px;">
        <div style="font-family:'Inter',sans-serif;font-size:18px;font-weight:600;color:#334155;margin-bottom:8px;">Credit Portfolio review by Product</div>
        <div style="font-family:'Inter',sans-serif;font-size:14px;color:#64748B;margin-bottom:8px;">35 mins</div>
        <div style="padding-left:24px;display:flex;flex-direction:column;gap:4px;">
          <!-- Active product: bold + blue arrow -->
          <div style="font-family:'Inter',sans-serif;font-size:15px;color:#0F172A;font-weight:700;display:flex;align-items:center;gap:8px;"><span style="color:#236CFF;">&#9654;</span> FNPL</div>
          <!-- Dimmed products -->
          <div style="font-family:'Inter',sans-serif;font-size:15px;color:#CBD5E1;">— PCA</div>
          <div style="font-family:'Inter',sans-serif;font-size:15px;color:#CBD5E1;">— RAD</div>
          <div style="font-family:'Inter',sans-serif;font-size:15px;color:#CBD5E1;">— TTFA</div>
        </div>
      </div>
      <div>
        <div style="font-family:'Inter',sans-serif;font-size:18px;font-weight:600;color:#CBD5E1;margin-bottom:4px;">Fraud Update</div>
        <div style="font-family:'Inter',sans-serif;font-size:14px;color:#CBD5E1;">10 mins</div>
      </div>
    </div>
  </div>
  <div style="text-align:right;font-family:'Inter',sans-serif;font-size:12px;color:#94A3B8;margin-top:16px;">Consumer Risk Team | {{MBR_MONTH_LABEL}}</div>
</div>
```

---

## Slide 5 — Executive Summary of GA 2.0 (ONE-TIME: April 2026 MBR only)

> **DO NOT include this slide for any month other than April 2026.** It is a one-time announcement slide. Skip it entirely for May 2026 and beyond.

This is a **static content slide** placed between Slide 4 (Agenda FNPL highlight) and Slide 9. It presents the GA 2.0 strategy overview with a summary paragraph and a 2-row strategy table.

**Background**: White, same header accent as other slides.

**Elements**:
1. **Title**: "Executive Summary of GA 2.0" — `Poppins` 24px, bold.
2. **Summary paragraph**: 3 sentences about applicant quality, pricing test, and decline swap-in test — `Inter` 11px, `#475569`.
3. **Strategy table**: 2 rows (Pricing Test, Decline Swap-in Test) × 3 columns (Learnings so far, Proposed Strategy & Rationale, Impact Expected in April). Dark header (`#0F172A`), `Inter` 10px body. Row 1 label column has light background (`#F1F5F9`).

**Content is hardcoded** — no placeholders, no queries.

**Color highlighting for key numbers**:
- **Red** (`#DC2626`): Risk/negative metrics (70% drop-off, 89% RS1 drop-off, 9% adoption, 35% declined, 27% loss rate, 30 bps increase)
- **Blue** (`#236CFF`): Strategy thresholds (500 bps, 300 bps, 0.35 PD, 19.7% target APR)
- **Green** (`#16A34A`): Positive impact ($1.9MM–$3.9MM, 5.3% stable loss rate, +4% approval, $2MM funded)
- **Orange** (`#EA580C`): Caution/risk trade-offs (27% segment loss rate, 30 bps loss increase)

**Condition**: At Step 0, if `{{MBR_MONTH_LABEL}}` is "Apr 2026", include this slide. Otherwise skip it.

### Slide 5 — Reference HTML

```html
<div class="slide slide-fixed" id="slide5" style="background:#FFFFFF;display:flex;flex-direction:column;padding:0;overflow:hidden;">
  <div style="background:#F8FAFC;border-bottom:1px solid #E2E8F0;padding:28px 48px 18px;">
    <div style="width:100%;height:4px;background:#0F172A;border-radius:2px;margin-bottom:16px;"></div>
    <h1 style="font-family:'Poppins',sans-serif;font-size:26px;font-weight:700;color:#0F172A;margin:0 0 12px;">Executive Summary of GA 2.0</h1>
    <p style="font-family:'Inter',sans-serif;font-size:12.5px;color:#475569;line-height:1.6;margin:0;">
      Observed strong applicant quality from GA, however there is opportunity to gather more insights to optimize policy going into FY'27.
      Through Pricing test we are offering as low as 10% for lowest risk segment (500bps lower) and 300 bps across all other risk segments to evaluate price sensitivity.
      Decline swap-in test is another opportunity for us to test credit expansion opportunities, and assess riskier segments where alternate data will help.
    </p>
  </div>
  <div style="flex:1;display:flex;flex-direction:column;padding:18px 48px 8px;">
    <table style="width:100%;border-collapse:collapse;font-family:'Inter',sans-serif;font-size:12px;flex:1;">
      <thead>
        <tr>
          <th style="background:#0F172A;color:#F1F5F9;padding:14px 16px;text-align:left;font-weight:700;font-size:13px;width:12%;border-radius:6px 0 0 0;"></th>
          <th style="background:#0F172A;color:#F1F5F9;padding:14px 16px;text-align:left;font-weight:600;font-size:13px;width:30%;">Learnings so far</th>
          <th style="background:#0F172A;color:#F1F5F9;padding:14px 16px;text-align:left;font-weight:600;font-size:13px;width:30%;">Proposed Strategy & Rationale</th>
          <th style="background:#0F172A;color:#F1F5F9;padding:14px 16px;text-align:left;font-weight:600;font-size:13px;width:28%;border-radius:0 6px 0 0;">Impact Expected in April</th>
        </tr>
      </thead>
      <tbody>
        <tr style="vertical-align:top;height:50%;">
          <td style="background:#F1F5F9;padding:18px 16px;font-weight:700;color:#0F172A;font-size:13px;border-bottom:1px solid #E2E8F0;">Pricing<br>Test</td>
          <td style="padding:18px 16px;color:#334155;line-height:1.7;border-bottom:1px solid #E2E8F0;">
            <div style="margin-bottom:10px;">&#8226; <strong style="color:#DC2626;">70%</strong> of credit-approved customers drop off; RS 1 is worst at <strong style="color:#DC2626;">89%</strong></div>
            <div>&#8226; FNPL adoption is only <strong style="color:#DC2626;">9%</strong> for our lowest-risk customers (780+ Vantage), suggesting price is a barrier</div>
          </td>
          <td style="padding:18px 16px;color:#334155;line-height:1.7;border-bottom:1px solid #E2E8F0;">
            <div style="margin-bottom:10px;">&#8226; Test setup — Randomized 80/20 split</div>
            <div style="margin-bottom:10px;">&#8226; <strong style="color:#236CFF;">500 bps</strong> reduction for RS 1 and <strong style="color:#236CFF;">300 bps</strong> across RS 2–6</div>
            <div>&#8226; Tests whether drop-off is driven by need vs. offer value</div>
          </td>
          <td style="padding:18px 16px;color:#334155;line-height:1.7;border-bottom:1px solid #E2E8F0;">
            <div style="margin-bottom:10px;">&#8226; Avg. APR may drop from <strong>20.3%</strong> to <strong style="color:#236CFF;">19.7%</strong></div>
            <div style="margin-bottom:10px;">&#8226; Incremental <strong style="color:#16A34A;">$1.9MM – $3.9MM</strong> in funded loans</div>
            <div>&#8226; Overall loss rate to remain at <strong style="color:#16A34A;">5.3%</strong>, as we expect more low risk customers to take loan with this test</div>
          </td>
        </tr>
        <tr style="vertical-align:top;height:50%;">
          <td style="background:#F1F5F9;padding:18px 16px;font-weight:700;color:#0F172A;font-size:13px;">Decline<br>Swap-in<br>Test</td>
          <td style="padding:18px 16px;color:#334155;line-height:1.7;">
            <div style="margin-bottom:10px;">&#8226; <strong style="color:#DC2626;">35%</strong> of customers are declined — we don't have cashflow or other alternative data to test</div>
            <div>&#8226; For FY'27, learnings from declined segment will help with policy optimization and UW model</div>
          </td>
          <td style="padding:18px 16px;color:#334155;line-height:1.7;">
            <div style="margin-bottom:10px;">&#8226; Model PD up to <strong style="color:#236CFF;">0.35</strong> with good risk and income profile</div>
            <div>&#8226; Small $ DQs in last 6 months and customer is in good standing currently</div>
          </td>
          <td style="padding:18px 16px;color:#334155;line-height:1.7;">
            <div style="margin-bottom:10px;">&#8226; Incremental <strong style="color:#16A34A;">+4%</strong> (56% → 58%) approval rate</div>
            <div style="margin-bottom:10px;">&#8226; Incremental <strong style="color:#16A34A;">$2MM</strong> funded</div>
            <div>&#8226; This segment estimated loss rate is at <strong style="color:#EA580C;">27%</strong>, losses may increase by <strong style="color:#EA580C;">30 bps</strong></div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
  <div style="text-align:right;font-family:'Inter',sans-serif;font-size:12px;color:#94A3B8;padding:0 48px 14px;">Consumer Risk Team | Apr 2026</div>
</div>
```

---

## Slide 3 — Executive Summary & Follow ups (Dynamic)

This slide is built **after** Slack inputs are collected from contributors at **Step 3C**. It is placed between the Agenda and Slide 4 in the combined HTML output.

### Contributors

| Product | Person | Slack ID |
|---------|--------|----------|
| FNPL | Sindhu Bhat | `U0322UD004R` |
| PCA | Gurmeet Arora | `U02TXQELKT8` |
| RAD | Shan Cong | `U09EXBVQ38C` |
| TTFA | Sindhu Bhat | `U0322UD004R` |

Sindhu owns two sections (FNPL + TTFA) — she receives one message covering both.

### Design — 4-Quadrant Layout

**Background**: White (`#FFFFFF`)
**Canvas**: 1280 × 720

**Elements**:

1. **Title**: "Executive Summary & Follow ups" — `Poppins` 28px, bold, `#0F172A`, bottom margin 24px.
2. **Header accent**: Same blue accent bar as other slides (`#0F172A`, 4px top border).
3. **Header section**: Light background (`#F8FAFC`), contains the title.
4. **Quadrant grid**: 2×2 CSS grid (`grid-template-columns: 1fr 1fr`, `gap: 16px`), filling the remaining slide height.
5. **Each quadrant box**:
   - `border-radius: 10px`, `border: 1px solid #E2E8F0`, `background: #FFFFFF`
   - **Product header**: Dark bar (`background: #0F172A`, `color: #F1F5F9`, `padding: 10px 16px`, `font-family: 'Inter'`, 13px, bold, uppercase, `border-radius: 10px 10px 0 0`)
   - **Content area**: `padding: 14px 16px`, `font-family: 'Inter'`, 12px, `color: #334155`, `line-height: 1.5`. Content rendered as-is from contributor input (bullet points, paragraphs, or mixed).
   - If input is missing: show placeholder text "Pending input from [Name]" in `#94A3B8` italic.
6. **Quadrant order**: Follows `{{PRODUCT_ORDER}}` — first two products in top row, last two in bottom row.
7. **Footer**: "Consumer Risk Team | {{MBR_MONTH_LABEL}}" — bottom-right, `Inter` 12px, `#94A3B8`.

### Slide 3 — Reference HTML

Replace `{{PRODUCT_1}}` through `{{PRODUCT_4}}`, `{{CONTENT_1}}` through `{{CONTENT_4}}`, and `{{MBR_MONTH_LABEL}}` at build time. Product labels and order come from `{{PRODUCT_ORDER}}`.

**Optional — “Edit on GitHub” (when the deck is hosted on GitHub Pages under `…/mbr/<file>.html`):** include the `<p>` + `<script>` block below the `<h1>`. The script sets the link to  
`https://github.com/namrataverma-rgb/fnpl-funnel-dashboard/edit/main/mbr/<current-html-filename>`.  
Change the `base` string inside the script if you use a different repo or path. Omit this block for local-only files or other hosts.

```html
<div class="slide slide-fixed" id="slide3" style="background:#FFFFFF;display:flex;flex-direction:column;padding:0;">
  <div style="background:#F8FAFC;border-bottom:1px solid #E2E8F0;padding:28px 48px 20px;">
    <div style="width:100%;height:4px;background:#0F172A;border-radius:2px;margin-bottom:16px;"></div>
    <h1 style="font-family:'Poppins',sans-serif;font-size:28px;font-weight:700;color:#0F172A;margin:0;">Executive Summary & Follow ups</h1>
    <p style="font-family:'Inter',sans-serif;font-size:11px;margin:12px 0 0 0;line-height:1.4;">
      <a id="fnpl-mbr-gh-edit" href="#" target="_blank" rel="noopener noreferrer" style="color:#1D4E89;font-weight:600;">Edit executive summary on GitHub</a>
      <span style="color:#94A3B8;font-weight:400;"> — opens this HTML file in the repo editor</span>
    </p>
    <script>
    (function(){
      var a=document.getElementById('fnpl-mbr-gh-edit');
      if(!a) return;
      var base='https://github.com/namrataverma-rgb/fnpl-funnel-dashboard/edit/main/mbr/';
      var seg=(location.pathname||'').split('/').filter(Boolean).pop()||'';
      if(!seg||!/\.html$/i.test(seg)) seg='FNPL_MBR_Apr26.html';
      a.href=base+encodeURIComponent(seg);
    })();
    </script>
  </div>
  <div style="flex:1;display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:20px 48px 12px;">
    <div style="border:1px solid #E2E8F0;border-radius:10px;display:flex;flex-direction:column;overflow:hidden;">
      <div style="background:#0F172A;color:#F1F5F9;padding:10px 16px;font-family:'Inter',sans-serif;font-size:13px;font-weight:700;text-transform:uppercase;">{{PRODUCT_1}}</div>
      <div style="padding:14px 16px;font-family:'Inter',sans-serif;font-size:12px;color:#334155;line-height:1.5;flex:1;">{{CONTENT_1}}</div>
    </div>
    <div style="border:1px solid #E2E8F0;border-radius:10px;display:flex;flex-direction:column;overflow:hidden;">
      <div style="background:#0F172A;color:#F1F5F9;padding:10px 16px;font-family:'Inter',sans-serif;font-size:13px;font-weight:700;text-transform:uppercase;">{{PRODUCT_2}}</div>
      <div style="padding:14px 16px;font-family:'Inter',sans-serif;font-size:12px;color:#334155;line-height:1.5;flex:1;">{{CONTENT_2}}</div>
    </div>
    <div style="border:1px solid #E2E8F0;border-radius:10px;display:flex;flex-direction:column;overflow:hidden;">
      <div style="background:#0F172A;color:#F1F5F9;padding:10px 16px;font-family:'Inter',sans-serif;font-size:13px;font-weight:700;text-transform:uppercase;">{{PRODUCT_3}}</div>
      <div style="padding:14px 16px;font-family:'Inter',sans-serif;font-size:12px;color:#334155;line-height:1.5;flex:1;">{{CONTENT_3}}</div>
    </div>
    <div style="border:1px solid #E2E8F0;border-radius:10px;display:flex;flex-direction:column;overflow:hidden;">
      <div style="background:#0F172A;color:#F1F5F9;padding:10px 16px;font-family:'Inter',sans-serif;font-size:13px;font-weight:700;text-transform:uppercase;">{{PRODUCT_4}}</div>
      <div style="padding:14px 16px;font-family:'Inter',sans-serif;font-size:12px;color:#334155;line-height:1.5;flex:1;">{{CONTENT_4}}</div>
    </div>
  </div>
  <div style="text-align:right;font-family:'Inter',sans-serif;font-size:12px;color:#94A3B8;padding:0 48px 16px;">Consumer Risk Team | {{MBR_MONTH_LABEL}}</div>
</div>
```

---

Run on the **Friday before the 3rd Wednesday** of each month. Data cutoff is typically the preceding Thursday.

### Execution Plan (parallelization)

```
Step 0 — Pre-run questions (two `AskQuestion` rounds: MBR month → then cutoff + base table + agenda; needs user input)
    │
    ▼
Step 1 — ONE MASSIVE PARALLEL BATCH: Fire ALL queries at once:
         • Slide 9 Query 1 + Query 2
         • Slide 10 Query (single ROLLUP — monthly + total)
         • Slide 11 Query (single ROLLUP — monthly + total)
         • Slide 12 Query (DPD30+ by vantage)
         • Slide 13 Query A (DPD30+ by term) + Query B (cohort summary)
         • DESCRIBE {{BASE_TABLE}} (ONLY if custom table — skip for ga1/ga2)
         • AIG cross-ref: cg_risk_vendor_rule_data (Slide 9 validation)
         • AIG cross-ref: cg_risk_fnpl_loan_status (Slide 10+11 validation)
    │
    ▼  (if DESCRIBE finds missing columns → pause for user in Plan mode)
    │
Step 2C — Verdict: In-memory comparison only (no new queries needed)
          Compare data query results vs AIG results. Present GO/YELLOW/RED.
    │
    ▼
Step 3-Static — Build Slides 1, 2, 4, 5 (no data needed, template-only)
Step 3A + 3B + 3D + 3E + 3F — PARALLEL: Build all data-driven HTML sections
                               + Slide 3 placeholder (pending inputs)
    │
    ▼
Step 3C — Preview + commentary + Slide 3 inputs (sequential, needs user input)
           Slack outreach to Sindhu (FNPL+TTFA+commentary),
           Gurmeet (PCA), Shan (RAD) — single Canvas, parallel DMs
    │
    ▼  (checkpoint: user says "check replies")
    │
Step 3G — Build Slide 3 from collected inputs, inject commentary
    │
    ▼
Step 4 + 5 — PARALLEL: Create Google Sheet tabs + save final HTML simultaneously
    │
    ▼
Step 0c — Update run history
```

**Key rules**:
- Only pause for user input at the designated checkpoints (Step 0, missing columns, Step 2C, Step 3C).
- **ONE Databricks round-trip**: All data + validation queries fire in a single parallel batch at Step 1. Step 2C is just in-memory comparison — zero additional queries.
- **Static slides build in parallel** with data slides — they need no query results.
- Everything else should be batched and parallelized.

## Step 0 — Pre-Run Confirmation (Plan Mode)

**Before doing ANY work, switch to Plan mode** using `SwitchMode(target_mode_id: "plan")`.

### 0a — Read Run History

Read [run-history.json](run-history.json). If it contains previous successful runs, extract the most recent `base_table` value to offer as an additional option in the table selection below.

### 0b — Ask Configuration Questions

> **CRITICAL: You MUST use the `AskQuestion` tool** for Step 0 — do **not** ask these as free-form chat text. **Policy test groups are no longer asked**; `{{POLICY_GROUPS}}` is a **fixed default** (see substitutions below).
>
> **Two rounds** (cutoff options depend on the selected MBR month):
> 1. **First `AskQuestion` call** — **Question 1 only** (MBR month label).
> 2. **Second `AskQuestion` call** — **Questions 2, 3, and 4** together, in this order: **Data cutoff** → **Agenda product order** → **Base table**.

---

**Question 1 — MBR month label** (first `AskQuestion` call — **only this question**)

Use `AskQuestion` with **dynamically generated options** from **March 2026** through the **current calendar month** (inclusive). Each option value is a short key (e.g. `mar26`, `apr26`); each label describes the MBR presentation month and coverage (same style as before).

| Option (example) | Label (example) |
|-------------------|-------------------|
| `mar26` | Mar 2026 — all Feb + mid Mar data |
| `apr26` | Apr 2026 — all Mar + mid Apr data |
| … | … |

List **oldest → newest**. Map the chosen option to **`{{MBR_MONTH_LABEL}}`** for slide titles/footers (short format, e.g. **"Apr 2026"**).

---

**Question 2 — Data cutoff date** (second `AskQuestion` call — **requires Question 1**)

After Question 1 is answered, compute **three** ISO cutoff candidates from the **selected MBR month** (derive year/month from the same option used for `{{MBR_MONTH_LABEL}}`):

| # | Option value (ISO) | Meaning |
|---|-------------------|---------|
| A | `last_day(add_months(<first_day_of_MBR_month>, -1))` | **Last calendar day of the month before** the MBR month (e.g. MBR Apr 2026 → `2026-03-31`; MBR Mar 2026 → `2026-02-28`) |
| B | `<MBR_year>-<MBR_month>-15` | **15th** of the MBR month (e.g. Apr 2026 → `2026-04-15`) |
| C | `last_day(<first_day_of_MBR_month>)` | **Last day** of the MBR month (e.g. Apr 2026 → `2026-04-30`) |

Present **exactly these three** as `AskQuestion` options (labels can be human-readable, e.g. "Mar 31, 2026 — end of month before MBR period"). The selected value becomes **`{{CUTOFF_DATE}}`** (`YYYY-MM-DD`). **`{{DATA_DATE}}`** in HTML footers uses the **same** date, formatted for display.

---

**Question 3 — Agenda product order** (second `AskQuestion` call — **ask this before Question 4**)

Controls **Slide 2 — Agenda** under "Credit Portfolio review by Product".

| Option | Label |
|--------|-------|
| `order1` | FNPL, PCA, RAD, TTFA |
| `order2` | PCA, FNPL, RAD, TTFA |
| `custom` | Custom order (I'll type the product list) |

If `custom`, follow up for the ordered list. Store as **`{{PRODUCT_ORDER}}`**.

---

**Question 4 — Base table** (second `AskQuestion` call — **after Question 3**)

| Option | Label |
|--------|-------|
| `ga1` | `sandbox_risk_7216.fnpl_base_alpha_ga1` (upd Mar) |
| `ga2` | `sandbox_risk_7216.fnpl_base_alpha_ga2` (upd Apr) |
| `history` | *(only if [run-history.json](run-history.json) has a previous table different from ga1/ga2)* — show the table name from the last successful run |
| `custom` | Custom table (I'll type the name) |

If the user picks `custom`, follow up once for the full table name. Map to **`{{BASE_TABLE}}`**.

---

Wait until **both** `AskQuestion` rounds are answered. Then **immediately switch to Agent mode** (`SwitchMode(target_mode_id: "agent")`) and begin execution.

**SQL substitutions from Step 0** (use in every data query and validation query that references the base table or servicing snapshot):

| Token | Source |
|--------|--------|
| `{{MBR_MONTH_LABEL}}` | Question **1** — display label for slides (e.g. "Apr 2026") |
| `{{CUTOFF_DATE}}` | Question **2** — ISO `YYYY-MM-DD` (Data Cutoff Date) |
| `{{PRODUCT_ORDER}}` | Question **3** — agenda product order |
| `{{BASE_TABLE}}` | Question **4** — full table name |
| `{{POLICY_GROUPS}}` | **Fixed — not asked.** Use exactly: `('Alpha/Beta','Beta2.0','GA1.0','GA1.1','GA2.0')` (same as former `pg3`). **Approval rate logic** in [queries.md](queries.md) Query 2 is unchanged: contingent approval for `GA*`, overall for non-GA. |

**Servicing snapshot date — Slide 11 only** (repayment / DoB for the monthly performance table): `date_sub(CAST('{{CUTOFF_DATE}}' AS DATE), 3)` — anchored to Question **2**, not the calendar run day.

**Slides 12–13** (DPD vintage charts): **no `{{CUTOFF_DATE}}`.** Cohort = all `funded_loan = 1` rows in `{{BASE_TABLE}}`. DoB / DPD measurement uses **`loan_repayment_daily.asofDate = (SELECT MAX(asofDate) FROM … loan_repayment_daily)`** — latest available snapshot. Slides 12–13 are **not** tied to Slide 11’s `AS_OF` date.

**Slide 11 `{{AS_OF_DATE}}` (HTML)**: Set to the **resolved** Slide 11 servicing snapshot (`date_sub({{CUTOFF_DATE}}, 3)`), formatted for display.

**Data cutoff contract (mandatory — applies to every run):**

| Layer | Rule |
|-------|------|
| **Deck footers (`{{DATA_DATE}}`)** | Use the **same calendar date** as Question **2** (`{{CUTOFF_DATE}}`) — format for display only. Do not substitute `current_date()` or the servicing snapshot here unless the template explicitly requires it. |
| **Base table (`{{BASE_TABLE}}`)** | **Slides 9, 10, 11:** `app_date <= CAST('{{CUTOFF_DATE}}' AS DATE)` on application- and funded-loan queries — defines the extract as of the cutoff. **Slides 12, 13:** no `app_date` cutoff in [queries-slide12.md](queries-slide12.md) / [queries-slide13.md](queries-slide13.md); cohort = all funded loans in the base table. |
| **Servicing / DoB** | **Slide 11:** `loan_repayment_daily.asofDate = date_sub(CAST('{{CUTOFF_DATE}}' AS DATE), 3)`. **Slides 12–13:** **no `asofDate` filter** — join on `daysonbooks IN (1, 30, 60, 90, 120, …)` only (see [queries-slide12.md](queries-slide12.md)). |
| **AIG validation (Slides 9 / 10 / 11)** | Apply the **same `{{CUTOFF_DATE}}`** upper bound on `application_submit_date` or `originationDate` as documented in Step 2A / 2B / 2D so cross-checks are apples-to-apples with the base table. Keep the existing lower bounds (`>= '2025-09-18'` apps, `>= '2025-09-01'` funded) unless the user explicitly changes them. |

**Feasibility check:** GA2 (`fnpl_base_alpha_ga2`) application history in production starts at **`app_date` ≥ 2025-09-18**. If **`{{CUTOFF_DATE}}` is before 2025-09-18**, the intersection with `application_submit_date >= '2025-09-18'` is **empty** — AIG validation returns no rows and the base table returns zero apps. **Reject or flag** cutoffs that precede the population start unless the user is doing a deliberate historical test with adjusted lower-bound filters.

**Cross-check (Slide 9 Check B):** After substitution, compare **monthly app counts**: base table `GROUP BY app_month` vs AIG `GROUP BY last_day(application_submit_date)` with the **same cutoff**. Under normal GA2 runs, month-level counts typically agree within **a few apps** per month; the skill tolerance remains **±10%**. Example (validated on warehouse): cutoff **2026-03-15** — AIG vs base differed by at most **2 apps** per month on Mar-26 partial month and adjacent months.

### 0c — Update Run History (end of run)

After a **fully successful** run (all steps completed, HTML generated), append the run to [run-history.json](run-history.json):

```json
{
  "month": "<MBR month label>",
  "base_table": "<confirmed table>",
  "cutoff_date": "<confirmed cutoff>",
  "policy_groups": "('Alpha/Beta','Beta2.0','GA1.0','GA1.1','GA2.0') — fixed in skill; not asked at Step 0",
  "run_date": "<today YYYY-MM-DD>",
  "repo_html_path": "exports/fnpl-mbr/FNPL_MBR_<MonYY>.html",
  "repo_html_pushed": true
}
```

Include `repo_html_path` when the deck was copied into `cg-credit-risk`; set `repo_html_pushed` to `false` if commit/push was skipped.

**Only write on success.** If the run fails or is aborted, do NOT update the file.

---

## Slide 9 — Application Profile

### Step 1A — Data Extraction (Slide 9) ⚡ PARALLEL with 1B

**Before writing any query**, consult [schema-reference.md](schema-reference.md) for known column names, cross-table naming differences, and gotchas. This avoids DESCRIBE trial-and-error and speeds up execution.

Authenticate with Databricks, then run **ALL of the following in a SINGLE parallel batch** (one Databricks round-trip for the entire skill):

**Data queries** (7 queries):
1. Slide 9 Query 1 (Vantage Distribution)
2. Slide 9 Query 2 (KPIs + Approval Rate)
3. Slide 10 — Single ROLLUP query (monthly + total combined, replaces old Query A+B)
4. Slide 11 — Single ROLLUP query (monthly + total combined, replaces old Query A+B)
5. Slide 12 Query (DPD30+ by vantage group)
6. Slide 13 Query A (DPD30+ by term)
7. Slide 13 Query B (Cohort Summary)

**Schema check** (conditional — 0 or 1 query):
- `DESCRIBE {{BASE_TABLE}}` — **ONLY if the user selected `custom` table at Step 0 Question 4**. For known tables (`ga1` = `sandbox_risk_7216.fnpl_base_alpha_ga1`, `ga2` = `sandbox_risk_7216.fnpl_base_alpha_ga2`), skip DESCRIBE entirely and trust the column mappings in [schema-reference.md](schema-reference.md).

**Validation queries** (2 queries, in the SAME batch — no separate round-trip):
8. AIG Slide 9 cross-ref: `aig.cg_risk_vendor_rule_data` (see Step 2A Check B below)
9. AIG Slide 10+11 cross-ref: `aig.cg_risk_fnpl_loan_status` (see Step 2B Check B and Step 2D below)

**Total: 9 queries in ONE parallel batch** (down from 13+ sequential queries previously). This eliminates all sequential round-trips — data extraction + validation run simultaneously.

Slide 9 queries come from [queries.md](queries.md).

**Required base filters** (apply to ALL Slide 9 queries — see [queries.md](queries.md)):
- `app_number2 = 1`
- `la_status != 'OFFER_PENDING'` (equivalently `is_offer_pending = 0` if column exists)
- `application_submit_date >= '2025-09-18'`
- `app_date <= CAST('{{CUTOFF_DATE}}' AS DATE)` — aligns the application universe with Question **2** (Data Cutoff Date)

These filters are non-negotiable. Never omit them.

**Substitution**: Replace `{{CUTOFF_DATE}}` with the ISO date from Step 0 Question **2** before executing queries. Replace `{{POLICY_GROUPS}}` with the **fixed** list from the Step 0 substitutions table (not user-configurable).

- **Query 1 (Vantage Distribution)**: Monthly counts by vantage band (Super Prime >=780, Prime 660-779, Near Prime 600-659, Subprime <600, Invalid NULL).
- **Query 2 (KPIs + Approval Rate)**: Monthly num_apps, avg_vantage, median_income, contingent_approval_rate using fixed **`{{POLICY_GROUPS}}`** per Step 0.

### Step 2A — Validation (Slide 9) — IN-MEMORY (no new queries)

> All data was already fetched in Step 1. This step only compares results in memory.

#### Check A — Historical Consistency (RED FLAG)

Compare every previous month's counts from this run against last month's saved Google Sheet. **Any delta in historical months is a big red flag** — investigate duplicates, missing filters, or table changes before proceeding.

#### Check B — Cross-Reference aig.cg_risk_vendor_rule_data

Compare Slide 9 monthly app counts against the AIG results already fetched in Step 1. **Both** must use the same **`{{CUTOFF_DATE}}`** upper bound (`application_submit_date <= cutoff`) and the same lower bound (`>= '2025-09-18'`) as [queries.md](queries.md) Validation Query B. Compare **by month**: base `app_month` totals vs AIG `last_day(application_submit_date)` totals.

The AIG query was:

```sql
SELECT last_day(application_submit_date) AS app_month,
       COUNT(*) AS apps
FROM aig.cg_risk_vendor_rule_data
WHERE (is_test_app = 0 OR is_test_app IS NULL)
  AND application_status != 'OFFER_PENDING'
  AND app_rank_desc = 1
  AND application_submit_date >= '2025-09-18'
  AND application_submit_date <= CAST('{{CUTOFF_DATE}}' AS DATE)
GROUP BY app_month ORDER BY app_month
```

**±10% tolerance**.

### Step 2C — Validation Verdict

After running both 2A and 2B, present a single clear verdict to the user. **Do NOT add your own commentary or interpretation — just report the status.**

| Condition | Indicator | Message |
|-----------|-----------|---------|
| Check A passes AND Check B passes (within ±10%) for both slides | **GO GREEN** | "Validation passed. Historical data is consistent across runs. Cross-validation against reference tables is within tolerance. Safe to proceed." |
| Check A detects change **only in the most recent month** AND Check B passes (within ±10%) | **GO GREEN** | "Historical data for prior months is consistent. The most recent month shows a delta — this is expected due to table refresh (new data arriving for the latest period). Cross-validation confirms alignment. Safe to proceed." |
| Check A **fails** on **older months** (not just the most recent) for either slide | **RED FLAG** | "WARNING — DO NOT PROCEED. Historical data for months that should be stable has changed between this run and the previous run. There may be a data discrepancy. Investigation required." Then help the user investigate (compare row counts, check for duplicates, filter mismatches, table schema changes). |
| Check A passes BUT Check B exceeds ±10% tolerance for either slide | **YELLOW** | "Historical data is consistent, but cross-validation results differ from `<reference table name>` by more than 10%. Not a blocker — the sources are different. Proceed with awareness." |

**Key distinction**: The most recent month's data often changes between runs as the base table refreshes with late-arriving records. This is normal. Only flag as RED if **older, already-stable months** show deltas.

Present the verdict and wait for the user to acknowledge. Once acknowledged, **immediately continue to Step 3** — do NOT wait for a manual mode switch.

---

### Step 3A — Build HTML (Slide 9) ⚡ PARALLEL with 3B

**Read [template.html](template.html) and replace `{{PLACEHOLDER}}` tokens ONLY. Do NOT rewrite the HTML/CSS/JS.** Do NOT add any commentary at this stage — only populate the data (chart, table, KPIs).

**Substitute these placeholders** with query results:

| Placeholder | Source |
|---|---|
| `{{MBR_MONTH}}` | MBR month label (e.g. "May 2026") |
| `{{LATEST_MONTH_LABEL}}` | Latest month short name (e.g. "Apr") |
| `{{MONTHS_JSON}}` | JS array of month labels `['Sep-25','Oct-25',...]` |
| `{{BARS_JSON}}` | JS array of band objects with `n`, `v[]`, `c` |
| `{{APPROVAL_JSON}}` | JS array of approval rate values (null for gaps) |
| `{{KPI_*}}` | Individual KPI values and deltas (see delta color rule below) |
| `{{TABLE_ROWS}}` | HTML `<tr>` rows for the data table |
| `{{TABLE_COLGROUP}}` | `<col>` elements for each month column |
| `{{TABLE_HEADERS}}` | `<th>` elements for month headers |
| `{{DATA_DATE}}` | Same date as Question **2** (`{{CUTOFF_DATE}}`), formatted for slide footers — must match the SQL cutoff |
| `{{SOURCE_TABLE}}` | Base table name |

**Slide 9 table format — STRICT, do NOT change**:

The table below the chart has exactly **4 rows**. Never show Vantage distribution counts in the table — those are already in the chart. The table rows are:

| Row | Metric | Format |
|-----|--------|--------|
| 1 | Num of Apps | Comma-separated integer |
| 2 | Avg Vantage | Integer |
| 3 | Median Income | `$XXK` |
| 4 | Approval Rate | `XX.X%` |

**KPI delta color rule — NEVER RED**: KPI change indicators must use ONLY two colors:
- **Green** (class `kd`, `#059669`): positive/improving changes (e.g., apps up, approval rate up, vantage up, income up)
- **Neutral gray** (class `kn`, `#94A3B8`): negative, flat, or unchanged metrics

**NEVER use red, orange, or any alarming color for KPI deltas.** The MBR is a factual report, not an alert dashboard. All directional changes are informational. If a metric decreases month-over-month, show it in neutral gray — not red.

**Approval rate in chart**: The dotted line must show approval rate values for **every month that had active applications**, including Sep-25 and Oct-25. For months where the **fixed `{{POLICY_GROUPS}}` cohorts** weren't active, use the **overall approval rate** instead. Only set to `null` for Nov-25 and Dec-25 (program paused).

**Key design rules** (do not change):
- Canvas: 1280×720 (16:9)
- Bar colors: `#1D4E89`, `#19A0AA`, `#F0C929`, `#E07B39`, `#C44536`
- Approval line: dotted black `#0F172A`
- Chart Plotly margins: `l:82, r:50` synced with table columns (`col.lc:82px`, `col.rc:50px`)
- Both y-axes visible with titles
- Header section: light `#F8FAFC` background
- Table: soft rounded corners (`border-radius:10px`)
- Latest month column highlighted (class `hi`)
- **Nov-25 and Dec-25: program was paused** — **Chart only**: force all bar values to `0` (no bar rendered) and set approval rate to `null` (line gap). **Tables keep real data** — show the actual queried values for Nov-25; only Dec-25 shows `—` (class `d`) in tables since it has zero volume.

---

## Slide 10 — Funded Loans Profile

### Step 1B — Data Extraction (Slide 10) ⚡ PARALLEL with 1A

Already dispatched in the same batch as Step 1A. **Single ROLLUP query** from [queries-slide10.md](queries-slide10.md):

- **Single Query (ROLLUP)**: Funded loan metrics by `last_day(lo.originationDate)` — joins `{{BASE_TABLE}}` to `intuit_lending_loanprofiles_dwh.loan_origination` (on `application_id = loanuuid`) and left-joins `tax_dm.agg_auth_id_accepted_refund` (on `authId = auth_id`). Filter: `funded_loan = 1`. Uses `GROUP BY 1 WITH ROLLUP` to produce monthly rows AND the grand-total row (`funded_month = NULL`) in a **single query** (no separate Query B).

Columns returned per month: loans, funded_amount, avg_loan_size, wa_term, wa_apr, wa_vantage, avg_rs, median_income, ck_low_risk_pct, pct_mobile_channel, avg_dti, state_refund_pct.

**In the agent**: split results — `funded_month IS NOT NULL` → monthly columns, `funded_month IS NULL` → "Total" column.

#### Missing Column Handling

**For known tables** (`ga1` / `ga2`): Skip `DESCRIBE` entirely — all columns are documented in [schema-reference.md](schema-reference.md). Proceed directly with queries.

**For custom tables only**: The `DESCRIBE {{BASE_TABLE}}` result (fetched in the Step 1 batch) is used to verify all referenced columns exist.

If **any column is missing**, do NOT silently substitute `NULL`. Instead:

1. **Switch to Plan mode** using `SwitchMode(target_mode_id: "plan")`
2. **Tell the user** which column is missing and which metric it affects
3. **Present options** using `AskQuestion`:

| Option | Action |
|--------|--------|
| `proxy` | Find the best approximate column available in the table — show the candidate and ask for confirmation before using it |
| `blank` | Skip the metric in the query (`NULL`), show "N/A" in the table but keep the row visible |
| `remove` | Eliminate the metric row entirely from the HTML output |
| `custom` | User provides instructions on how to source / compute the metric |

Wait for the user's choice. Apply it, then resume in Agent mode. Repeat for each missing column independently.

### Step 2B — Validation (Slide 10) — IN-MEMORY (no new queries)

> All data was already fetched in Step 1. This step only compares results in memory.

#### Check A — Historical Consistency (RED FLAG)

Compare every previous month's funded loan counts and dollar amounts from this run against last month's saved Google Sheet. **Any delta in historical months is a big red flag** — investigate duplicates, missing filters, or table/join changes before proceeding.

#### Check B — Cross-Reference aig.cg_risk_fnpl_loan_status

Compare Slide 10 monthly funded loan counts and dollar amounts against the AIG results already fetched in Step 1. The AIG query was:

```sql
SELECT last_day(origination_date) AS funded_month,
       COUNT(*) AS loans,
       SUM(loan_amount) AS funded_amount
FROM aig.cg_risk_fnpl_loan_status
WHERE origination_date >= '2025-09-01'
  AND origination_date <= CAST('{{CUTOFF_DATE}}' AS DATE)
GROUP BY funded_month ORDER BY funded_month
```

**±10% tolerance**. This table is funded-loan specific, so it should align more closely with Slide 10 data than the application-level `cg_risk_vendor_rule_data` table.

### Step 3B — Build HTML (Slide 10) ⚡ PARALLEL with 3A

**Read [template-slide10.html](template-slide10.html) and replace `{{PLACEHOLDER}}` tokens ONLY. Do NOT rewrite the HTML/CSS/JS.** Do NOT add any commentary at this stage — only populate the data (table, metrics).

**Substitute these placeholders** with query results:

| Placeholder | Source |
|---|---|
| `{{MBR_MONTH}}` | MBR month label |
| `{{TABLE_MONTH_COLS}}` | `<col>` elements — one per month (same count as Slide 9) |
| `{{TABLE_HEADERS}}` | `<th>` for each month (same months as Slide 9) |
| `{{TABLE_ROWS}}` | 12 `<tr>` rows for funded metrics (see formatting below) |
| `{{COMMENTARY_DATA}}` | JS object with latest/prior/total values for auto-commentary |
| `{{DATA_DATE}}` | Same as Question **2** (`{{CUTOFF_DATE}}`), formatted — must match SQL cutoff |
| `{{SOURCE_TABLE}}` | Base table name |

**Metric row formatting**:

| Metric | Format | Example |
|---|---|---|
| # Loans | Comma-separated integer | `7,773` |
| $ Loans | Millions with 1 decimal | `11.9M` |
| Avg. Loan Size | Dollar + comma | `$1,532` |
| WA Term | 1 decimal | `6.6` |
| WA APR | 2 decimal + % | `19.34%` |
| WA Vantage | Integer | `707` |
| Avg. RS | 1 decimal (N/A if null) | `2.5` |
| Med. Income | Thousands + K | `76K` |
| % $ from CK Low Risk | Integer + % | `51%` |
| % Mobile Channel | Integer + % | `38%` |
| Avg. DTI | Integer + % | `40%` |
| % Had a State Refund | Integer + % | `42%` |

**Commentary data shape** (for auto-generated bullets):
```json
{
  "latest": { "label":"Mar-26", "wa_term":6.6, "wa_apr":19.34, "wa_vantage":707, "ck_low_risk":51, "mobile":38, "avg_dti":40, "loans":7773 },
  "prior":  { "label":"Feb-26", "wa_term":5.9, "wa_apr":19.38, "wa_vantage":693, "ck_low_risk":52, "mobile":40, "avg_dti":41, "loans":5738 },
  "total":  { "ck_low_risk":50 }
}
```

**Key design rules** (do not change):
- Canvas: 1280×720 (16:9), same design system as Slide 9
- Header: `#F8FAFC` background, blue accent bar
- **Layout**: Header → Table → Commentary (clean, no KPI cards or volume chart)
- **TABLE ALIGNED WITH SLIDE 9**: same `margin: 0 40px` viz-wrap, `col.lc:82px` label, `col.tc:50px` Total (replaces Slide 9 `col.rc:50px` spacer). Month columns auto-distribute identically.
- **Only include months that have data** — skip future empty months. Use the same month set as Slide 9.
- Latest month highlighted with class `hi` (blue)
- Total column uses class `total-col` (subtle left border + gray background)
- **Nov-25 and Dec-25: program was paused** — Nov-25 keeps real data values in the table (the pause suppression is **chart-only** in Slide 9). Dec-25 shows `—` (class `d`) in tables since it has zero volume.
- N/A for Avg RS when `mxsPrediction` is null for a month
- Commentary section is initially **empty** — populated in Step 3C below

---

---

## Slide 11 — Monthly Performance

### Step 1C — Data Extraction (Slide 11) ⚡ PARALLEL with 1A + 1B

Already dispatched in the same batch as Steps 1A and 1B. **Single ROLLUP query** from [queries-slide11.md](queries-slide11.md):

- **Single Query (ROLLUP)**: Derived from Databricks notebook cells 22+24, combined via `GROUP BY app_month WITH ROLLUP`. Joins `{{BASE_TABLE}}` (funded_loan=1) to `intuit_lending_loanprofiles_dwh.loan_origination` (on `application_id = loanuuid`) and left-joins `intuit_lending_servicing_capital_dwh.loan_repayment_daily` (as-of **`date_sub(CAST('{{CUTOFF_DATE}}' AS DATE), 3)`** snapshot with carry-through fallback). Produces monthly rows AND the grand-total row (`app_month = NULL`) in a **single query** (no separate Query B).

**Dynamic date**: Servicing snapshot uses **`date_sub(CAST('{{CUTOFF_DATE}}' AS DATE), 3)`** (same role as prior `current_date()-3`, tied to Question **2**). Base table rows are limited with **`app_date <= CAST('{{CUTOFF_DATE}}' AS DATE)`** — see [queries-slide11.md](queries-slide11.md).

**Metrics produced**: `n_loans`, `funded_amount`, `n_paid_off_asof`, `active_loans`, `n_7dpd_plus`, `n_30dpd_plus`, `7dpd_plus_rate`, `30dpd_plus_rate`, `paid_off_rate_asof`, `dollar_7dpd_plus_rate`, `dollar_30dpd_plus_rate`, `charged_off_asof_rate`, `dollar_charged_off_asof_rate`, `outstanding_loans`, `7dpd_elig`, `30dpd_elig`.

**In the agent**: split results — `app_month IS NOT NULL` → monthly columns, `app_month IS NULL` → "Total" column.

### Step 2D — Validation (Slide 11) — IN-MEMORY (no new queries)

> All data was already fetched in Step 1. This step only compares results in memory.

**No historical consistency check for Slide 11** — skip it. Only run the cross-reference validation below.

#### Cross-Reference aig.cg_risk_fnpl_loan_status

Compare Slide 11 monthly metrics against the AIG results already fetched in Step 1. The AIG query was:

```sql
SELECT
    last_day(originationDate) AS app_month,
    COUNT(*) AS n_loans,
    SUM(CAST(originationAmount AS DOUBLE)) AS funded_amount,
    SUM(CASE WHEN intuitStatus = 'PAID_OFF' THEN 1 ELSE 0 END) AS n_paid_off,
    SUM(CASE WHEN intuitStatus = 'CHARGED_OFF' THEN 1 ELSE 0 END) AS n_charged_off,
    SUM(CASE WHEN intuitStatus IN ('LATE_31_TO_60_DAYS','LATE_61_TO_90_DAYS','LATE_91_TO_119_DAYS')
        THEN 1 ELSE 0 END) AS n_30dpd_plus,
    SUM(CASE WHEN daysOnBooks > 60 THEN 1 ELSE 0 END) AS elig_30dob
FROM aig.cg_risk_fnpl_loan_status
WHERE originationDate >= '2025-09-01'
  AND originationDate <= CAST('{{CUTOFF_DATE}}' AS DATE)
GROUP BY 1 ORDER BY 1
```

**Validation rules**:
- **±10% tolerance** on `n_loans` and `funded_amount` for all months **except** the most recent month (current month numbers may differ due to population scope — AIG table includes all loans while the base table has policy group filters).
- **Small mismatches of 1-2 loans are acceptable** — do not flag these.
- **30DPD+ and Charge Off counts**: Compare where `elig_30dob > 0`. AIG's `LATE_31+` bucket aligns well with `daysPastDue >= 30` from the primary query.
- **7DPD+ is NOT validated against AIG** — the AIG table's `LATE_1_TO_30_DAYS` bucket includes DPD 1-6, making it an imprecise proxy. Skip this comparison.

**Include in Step 2C verdict**: Fold Slide 11 validation results into the same GO GREEN / YELLOW verdict. RED FLAG is not applicable for Slide 11 (no historical check).

### Step 3D — Build HTML (Slide 11) ⚡ PARALLEL with 3A + 3B

**Read [template-slide11.html](template-slide11.html) and replace `{{PLACEHOLDER}}` tokens ONLY. Do NOT rewrite the HTML/CSS/JS.** Do NOT add commentary script at this stage — only populate the data table and `{{TABLE_SUBTITLE}}`.

**Canonical table content (MANDATORY):** Follow **[slide11-table-spec.md](slide11-table-spec.md)** end-to-end — metric row order, **section sub-header** titles, **exact** roll-rate labels (`# Roll rate -> 30D to CO` / `$ Roll rate -> 30D to CO`), omission of 1DPD / 60DPD / 90DPD rows in the default deck, and **typography parity** with Slide 10 (`#slide10 .tbl` in [template-slide10.html](template-slide10.html)).

**Substitute these placeholders** with query results:

| Placeholder | Source |
|---|---|
| `{{MBR_MONTH}}` | MBR month label (e.g. "May 2026") |
| `{{AS_OF_DATE}}` | Servicing snapshot date string — **`date_sub(CAST('{{CUTOFF_DATE}}' AS DATE), 3)`** resolved and formatted for the slide subtitle (cutoff from Question **2**) |
| `{{TABLE_SUBTITLE}}` | Short paragraph above the table per [slide11-table-spec.md](slide11-table-spec.md) |
| `{{TABLE_MONTH_COLS}}` | `<col>` elements — one per month (same count as Slide 9) |
| `{{TABLE_HEADERS}}` | `<th>` for each month + Total |
| `{{TABLE_ROWS}}` | Metric rows + `section-row` sub-headers per spec |
| `{{DATA_DATE}}` | Same as Question **2** (`{{CUTOFF_DATE}}`), formatted — must match SQL cutoff |
| `{{SOURCE_TABLE}}` | Base table name |

**Metrics mapping** (summary — full order and SQL fields are in [slide11-table-spec.md](slide11-table-spec.md)):

| Section | Rows |
|---------|------|
| Volume | # Loans, $ Loans |
| 7DPD+ Delinquency | # / $ 7DPD+ Rate |
| 30DPD+ Delinquency | # / $ 30DPD+ Rate |
| Roll to charge-off | `# Roll rate -> 30D to CO`, `$ Roll rate -> 30D to CO` |
| Charge-off | # / $ Charge off rate |
| Target loss | # / $ Target Loss Rate (placeholders until defined) |
| Payoff | % Paid Off |

**Key design rules** (do not change):
- Canvas: 1280×720 (16:9), same design system as Slides 9 & 10
- Header: `#F8FAFC` background, blue accent bar
- **Layout**: Header → **table subtitle** → Table → Commentary
- Table uses **section sub-header** rows (`class="section-row"`) with titles exactly as in [slide11-table-spec.md](slide11-table-spec.md)
- **Table cell typography** must match **Slide 10** (see spec) — do not diverge font sizes or padding for `#slide11 .tbl`
- Latest month highlighted with class `hi` (blue)
- Total column uses class `total-col` (subtle left border + gray background)
- Dec-25 shows `—` (class `d`) — program was paused, zero volume
- DPD rates show `—` when eligible count is 0 (loans too new for that metric)
- Undefined metrics (Target Loss Rate) always show `—` with class `d`
- **Nov-25 keeps real data values** in the table (pause suppression is chart-only in Slide 9)

---

## Slide 12 — DPD30+ by Vintage & Vantage Group

### Step 1D — Data Extraction (Slide 12) ⚡ PARALLEL with 1A + 1B + 1C + 1E

Already dispatched in the same batch as Steps 1A–1C. Query comes from [queries-slide12.md](queries-slide12.md):

- **Single query**: CTE-based query joining `{{BASE_TABLE}}` (funded_loan=1) to `intuit_lending_loanprofiles_dwh.loan_origination` and `intuit_lending_servicing_capital_dwh.loan_repayment_daily`. No `asofDate` filter — joins on **explicit `daysonbooks IN (1, 30, 60, 90, 120, 150, 180)`** values (M0–M6). Substitute **`{{MOB_CAP}}`** (e.g. **Mar → 4**, **Apr → 5**) — same integer in SQL and `template-slide12.html`.

**Vantage Score Groups** (defined in the query CASE statement):
| Group | Vantage Range |
|-------|---------------|
| Super Prime | >= 780 |
| Prime | 660–779 |
| Near Prime | 600–659 |
| Subprime | < 600 or NULL |

**Output columns**: `vantageScoreGroup`, `origination_month`, `mob`, `total_loans`, `loans_7dpd`, `loans_30dpd`, `rate_7dpd`, `rate_30dpd`.

### Step 3E — Build HTML (Slide 12) ⚡ PARALLEL with 3A + 3B + 3D + 3F

**Read [template-slide12.html](template-slide12.html) and replace `{{PLACEHOLDER}}` tokens ONLY. Do NOT rewrite the HTML/CSS/JS.** Do NOT add any commentary at this stage.

**Canonical chart behavior (combined HTML — MANDATORY, same idea as Slide 13):** In a **single-file deck**, `body` and outer wrappers differ from standalone `template-slide12.html`. Plotly’s **`responsive: true`** can measure the four `.chart-div` panels at the wrong time, so charts look **uneven or stretched**. The template therefore mirrors Slide 13’s fix:

1. After the shared legend HTML is injected, run **`void document.getElementById('slide12').offsetHeight`** so the `#slide12` flex/grid layout commits before any chart draws.
2. For each panel (`c12_0` … `c12_3`), read **`chartEl.getBoundingClientRect()`** and pass **`width`** and **`height`** into the Plotly **`layout`** (with floors, e.g. `Math.max(200, rect.width)` / `Math.max(160, rect.height)`).
3. Use **`responsive: false`** in the Plotly config so Plotly does not re-size asynchronously and fight the 2×2 grid.

4. **Shared Y-axis range** across all four Vantage panels: `renderSlide12` computes a single **`yAxisTop`** from the max DPD30+ **%** in the filtered data (`Math.max(1, maxPct * 1.15)`) and sets **`yaxis.range: [0, yAxisTop]`** on every chart. That prevents **per-panel autoscale** (inconsistent tick steps, Y not starting at 0%, one panel looking “empty”).

5. **Spline only when a vintage line has two or more MoBs:** For a single MoB point, the template uses **`line.shape: 'linear'`** (not spline). Plotly **spline + one point** can drop x-axis ticks or corrupt layout in some builds.

The implementation lives in `template-slide12.html` (`renderSlide12`). **Do not swap in ad hoc Plotly options from memory or old HTML** — if chart sizing changes, edit the template and this skill together.

#### Slide 12 — mandatory verification (before merging into combined HTML)

After substitution, **prove the embedded Slide 12 script matches the current template** (not truncated). Use Grep on the built fragment or combined file — these literals **must** be present:

| Marker | Why |
|--------|-----|
| `void document.getElementById('slide12').offsetHeight` | Forces layout before measuring chart divs (same class of fix as Slide 13’s `void row.offsetHeight`) |
| `getBoundingClientRect` | Per-panel width/height for even Plotly canvases |
| `yAxisTop` / `range:[0,yAxisTop]` | Shared Y-axis across all four panels (avoids uneven autoscale) |
| `responsive:false` | Plot config — avoids reflow skewing the 2×2 grid |

If **any** marker is missing, **stop** — re-extract Slide 12 from the current `template-slide12.html` and re-inject placeholders. Do **not** deliver combined HTML that uses bare `responsive:true` for Slide 12 in a multi-slide file.

**Layout — 2×2 chart grid, NO tables**:

The slide displays four Plotly line charts in a **2×2 grid with four equal quadrants** (`grid-template-columns: 1fr 1fr`, `grid-template-rows: 1fr 1fr`, chart boxes `height: 100%`). Tables are **not** shown — data labels are rendered directly on the chart lines instead.

**Chart ordering** (top-left → top-right → bottom-left → bottom-right):
1. Super Prime
2. Prime
3. Near Prime
4. Subprime

**Chart titles**: Uppercase styling via CSS (`.chart-title`); text is set in JS as plain text: `N. {nice name}` — **do NOT append `(N=xxx)` or any cohort count to the panel title**. Cohort size is available in the hover tooltip only (via `n=` in `hovertemplate`). Example title: `1. Super Prime (≥780)`.

**Dynamic vintage color map** (consistent across ALL four charts):

The color palette auto-assigns colors to **every origination month returned by the query**, in chronological order. The palette is:

| Position | Color | Hex | Example (Apr MBR) |
|----------|-------|-----|-------------------|
| 1st vintage | Navy | `#1D4E89` | Sep-25 |
| 2nd vintage | Teal | `#19A0AA` | Oct-25 |
| 3rd vintage | Orange | `#E07B39` | Nov-25 |
| 4th vintage | Red-Brown | `#C44536` | Jan-26 |
| 5th vintage | Gold | `#F0C929` | Feb-26 |
| 6th vintage | Purple | `#7C3AED` | Mar-26 |
| 7th+ vintage | Slate | `#475569` | (future) |

**Build the `vintageColors` map dynamically**: collect all distinct `origination_month` values from the query results, sort chronologically, and assign colors in order from the palette above. **Skip Dec-25** — the program was paused, so no loans were originated. If Dec-25 appears in query results with zero loans, exclude it from the vintage list entirely.

These colors are assigned via the `vintageColors` map and applied to every trace's `line.color`, `marker.color`, and `textfont.color`. All four charts MUST use the same color assignments.

**Shared legend**: A single HTML legend bar (class `shared-legend`) is placed above the 2×2 chart grid, showing one color swatch per vintage (dynamically built from the `vintageColors` map). Individual per-chart Plotly legends are hidden (`showlegend:false` in layout base).

**Symmetry rule**: ALL vintages from the color map MUST appear in every chart, even if a group has zero delinquency for a vintage. For groups with no non-zero data for a vintage, pass the data as all zeros and use `showAll:true` option so the flat line still renders, keeping the color palette consistent across panels.

**Data labels on charts**: Charts use `labels:true` option which renders `mode:'lines+markers+text'` with percentage labels at `textposition:'top center'`. Label font: 9px Inter, colored to match the line. Labels only show for non-zero values.

**Line style**: **Spline** (`shape:'spline', smoothing:1.2`) when a vintage has **two or more** MoB points; **linear** for a **single** MoB (required for stable Plotly rendering). Line width 2.5, marker size 6.

**Chart panel size (Plotly)**: Height/width come from the **measured** `.chart-div` after layout (see canonical chart behavior above), not a single hard-coded pixel height in the combined file — that keeps all four panels even. Data labels still use the template’s font sizes.

**Y-axis (shared)**: All four charts use the **same** `yaxis.range` derived from the **global** max rate in the filtered data (see canonical chart behavior §4), not independent autoscale per panel.

**X-axis**: Category array is **`M0`…`M{MOB_CAP}`** from the template. Embed only rows with **`mob` ≤ `MOB_CAP`**; rows above the cap are filtered out and will **omit vintages** from the legend if that was their only MoB.

**MoB cap — exclude the incomplete current month**: The query returns MoB checkpoints for all available data, but the **current (incomplete) month produces a partial MoB data point** that should NOT be plotted. To determine the cap:
1. Take the oldest vintage's origination month (e.g. Sep 2025)
2. Count complete months between that origination and the **first day of the MBR month** (e.g. Apr 1 2026 → 6 complete months Sep→Mar)
3. The max MoB to display = that count minus 1 (because M0 = origination month itself). For Apr MBR with Sep-25 oldest vintage: max MoB = **M5** (through end of March).
4. **Filter out any data points beyond this cap** before building chart traces.

Rule of thumb: `max_mob = months_between(oldest_vintage, mbr_month_start) - 1`. Example progression: Apr MBR → M5, May MBR → M6, Jun MBR → M7.

**Y-axis**: DPD30+ Rate (%), **`range: [0, yAxisTop]`** shared across panels (see above); not per-chart autoscale.

**Key design rules**:
- Canvas: 1280×720 (16:9), same design system as Slides 9–11
- Header: `#F8FAFC` background, blue accent bar
- Same `hdr-section`, `badge`, `foot` styling as other slides
- Footer shows source table, join tables, and DoB snapshot methodology

---

## Slide 13 — DPD30+ by Vintage & Term

### Step 1E — Data Extraction (Slide 13) ⚡ PARALLEL with 1A + 1B + 1C + 1D

Already dispatched in the same batch as Steps 1A–1D. Query comes from [queries-slide13.md](queries-slide13.md):

- **Single query**: Same CTE structure as Slide 12 (same **`{{MOB_CAP}}`** and explicit `daysonbooks` checkpoints), but segmented by `term` instead of `vantageScoreGroup`. Joins `{{BASE_TABLE}}` (funded_loan=1) to the same loan origination and repayment tables.

**Term groups**: Derived from the `term` column in the base table (e.g., 3, 6, 9 months). Label format: `X-Month Term`.

**Output columns**: `term`, `origination_month`, `mob`, `total_loans`, `loans_7dpd`, `loans_30dpd`, `rate_7dpd`, `rate_30dpd`.

### Step 3F — Build HTML (Slide 13) ⚡ PARALLEL with 3A + 3B + 3D + 3E

**Read [template-slide13.html](template-slide13.html) from this skill directory (Read tool) and replace `{{PLACEHOLDER}}` tokens ONLY. Do NOT rewrite the HTML/CSS/JS.** Do not paste Slide 13 script from an older HTML artifact or from memory. Do NOT add any commentary at this stage.

**Canonical chart behavior (MANDATORY):** **[slide13-chart-spec.md](slide13-chart-spec.md)** — per-term Y-axis range (do not share one scale across terms), **smooth spline** lines with `connectgaps: false`, padded series to full `M0`…`M{MOB_CAP}`, **numeric linear x-axis** with `ticktext` MoB labels and `customdata` hovers, **`responsive: false`** + measured `layout.width`, and **two-phase rendering** (append all term panels → `void row.offsetHeight` → `plotJobs` / per-term `Plotly.newPlot`). The template implements this; **any change to chart logic requires updating the spec and the template together**, not ad hoc edits during a run.

#### Slide 13 — mandatory verification (before merging into combined HTML)

After substitution, **prove the embedded Slide 13 script was not truncated or replaced**. Use Grep (or equivalent) on the built fragment or combined file for these literals (all must be present):

| Marker | Why |
|--------|-----|
| `plotJobs` | Two-phase plot queue — prevents flex single-child width bug |
| `void row.offsetHeight` | Forces layout before measuring chart div width |
| `padSeriesToMobs` | Full MoB horizon with `null` gaps |
| `type:'linear'` | X-axis (inside `xaxis:`) — stable MoB ticks vs category thinning |
| `responsive:false` | Plot config — avoids reflow hiding ticks |

If **any** marker is missing, **stop** — re-extract Slide 13 from the current `template-slide13.html` and re-inject placeholders. Do **not** deliver combined HTML without passing this check.

**Layout**: Charts are arranged side by side in a `chart-row` (flex row, `align-items:flex-start`). Each term group lives inside a `chart-box` div containing:
1. The Plotly chart div (e.g. `c13-t3`)
2. A summary table directly below the chart (`width:100%`, `margin-top:6px`, `font-size:10px`)

This places each table directly beneath its corresponding chart, matching the chart width.

**`{{TERMS_SUBTITLE}}` — build dynamically**: List the included terms and any omitted terms. Format: `Origination month cohort · {X}-Month and {Y}-Month terms shown · {Z}-Month omitted (no DPD30+ data yet)`. If all terms have data, omit the "omitted" clause. Example: `Origination month cohort &middot; 3-Month and 6-Month terms shown &middot; 9-Month omitted (no DPD30+ data yet)`.

**Term inclusion rule**: Only include a term group if it has **at least one non-zero DPD30+ rate** across any vintage and any MoB. If a term has zero delinquency everywhere (all rates = 0), omit its chart, table, and `plotV` call entirely. Add an HTML comment noting it was omitted (e.g. `<!-- 9-Month Term omitted — no delinquency data yet -->`). Re-include it in future months once any DPD30+ > 0.

**Chart titles**: Bold and uppercase (same `plotV` function as Slide 12).

**Same dynamic vintage color map** as Slide 12 (`vintageColors` object). Built from all distinct origination months in the query results, same palette and same color assignments. Colors are consistent across Slides 12 and 13.

**Shared legend**: A single HTML legend bar (class `shared-legend`) is placed above the chart row, showing one color swatch per vintage (dynamically built from the `vintageColors` map — identical to Slide 12). Individual per-chart Plotly legends are hidden (`showlegend:false` in layout base).

**Data labels on charts**: Charts use `mode:'lines+markers+text'` with percentage labels at `textposition:'top center'`. Same general behavior as Slide 12.

**Line style (template)**: **Spline** (`shape:'spline'`, moderate smoothing) for soft curves — see [slide13-chart-spec.md](slide13-chart-spec.md). Y-axis top includes headroom so splines stay in frame; 3-month uses slightly more padding than 6-month.

**Chart height / Y-axis**: Implemented in `template-slide13.html` — **per-term** `yaxis.range` from that term’s data. Do not override with a single global max across terms.

**MoB cap**: Apply the **same MoB cap rule as Slide 12** — exclude the incomplete current month. Use the same `max_mob` calculation and filter out data points beyond it before building chart traces.

**Data tables (transposed format)**: Each term group has a summary table below its chart. The table is **transposed** — metrics are in rows and months are in columns:

| | Sep-25 | Oct-25 | Nov-25 | Jan-26 | Feb-26 | Mar-26 | Apr-26 |
|--------|--------|--------|--------|--------|--------|--------|--------|
| # Loans | … | … | … | … | … | … | … |
| Avg Vantage | … | … | … | … | … | … | … |
| Med. Income | … | … | … | … | … | … | … |

Source metrics:

| Metric | Source | Format |
|--------|--------|--------|
| # Loans | `COUNT(*)` per term × month | Comma-separated integer |
| Avg Vantage | `AVG(vantageScore3)` per term × month | Integer |
| Median Income | `PERCENTILE_APPROX(tt_amountTotalIncome, 0.5)` per term × month | `$XXK` |

These metrics require a **supplementary query** (see queries-slide13.md, Query B) that groups by `term` and `origination_month` from the base table.

**Key design rules**:
- Canvas: 1280×720 (16:9), same design system as other slides
- Header: `#F8FAFC` background, blue accent bar
- `vintage-body` wrapper containing the shared legend, then a `chart-row` with `chart-box` children
- Tables use the same dark header as Slides 9/10/11: `#0F172A` background, `#F1F5F9` text (`.vtbl` class inherits this consistent style)
- Footer shows source table, join tables, and DoB snapshot methodology

---

### Step 3C — Preview, Commentary & Slide 3 Input Collection

This step collects **two things at once**: commentary for data slides (9–13) and executive summary inputs for Slide 3. Both are gathered via a single shared Slack Canvas sent to all contributors.

#### 3C.1 — Preview

1. **Serve the combined HTML** and open it in the browser so the user can preview all slides (data only, no commentary yet; Slide 3 shows placeholders).
2. **Slide 13 spot-check (mandatory):** On **DPD30+ by Vintage & Term**, confirm **each** term panel’s x-axis shows **all** MoB labels from **M0** through **M{MOB_CAP}** (e.g. M0–M5 when `MOB_CAP` is 5), evenly spaced, with **no** clipping of the rightmost tick. If the 3-month panel shows only M0–M2 and a cut-off “M”, the build failed the Step 3F verification — fix before continuing.
3. **Take a full-page screenshot** of the preview (`browser_take_screenshot` with `fullPage: true`) and save it to `~/Downloads/FNPL_MBR_<MonYY>_preview.png`.
4. **Switch to Plan mode** using `SwitchMode(target_mode_id: "plan")`.

#### 3C.2 — Ask the user how to proceed

> **CRITICAL: You MUST use the `AskQuestion` tool here — do NOT improvise a free-form text prompt asking the user to type commentary. Do NOT ask the user to fill in a template. Do NOT skip this question. Use the EXACT tool call below.**

Call `AskQuestion` with this EXACT structure:

```
AskQuestion(questions: [{
  id: "commentary_mode",
  prompt: "How would you like to handle commentary for data slides (9–13) and executive summary inputs for Slide 3?",
  options: [
    { id: "auto", label: "Auto-generate commentary based on data trends (I'll provide Slide 3 inputs separately)" },
    { id: "custom", label: "I'll provide custom commentary — let me type it" },
    { id: "ask_team", label: "Send preview to Sindhu, Gurmeet, and Shan on Slack — collect commentary + Slide 3 executive summary inputs from all contributors" }
  ]
}])
```

**Wait for the user's selection. Then branch based on the answer:**

- **If `auto`**: Generate commentary from the data trends and inject into HTML. Then ask user to provide Slide 3 inputs manually or skip.
- **If `custom`**: Ask them to provide commentary text (which slides) and Slide 3 content.
- **If `ask_team`**: Execute the Slack outreach flow in 3C.3 below.

**Do NOT combine these options into one big text prompt. Do NOT ask users to type into a template. The `AskQuestion` tool provides a structured UI — use it.**

#### 3C.3 — Slack outreach (ask_team flow)

**Contributors**:

| Person | Slack ID | Sections |
|--------|----------|----------|
| Sindhu Bhat | `U0322UD004R` | FNPL exec summary + TTFA exec summary + commentary for Slides 9–13 |
| Gurmeet Arora | `U02TXQELKT8` | PCA exec summary |
| Shan Cong | `U09EXBVQ38C` | RAD exec summary |

**Step A — Create ONE shared Slack Canvas** using `slack_create_canvas`:

- Title: `FNPL MBR {{MBR_MONTH}} — Preview & Inputs`
- Content: Two sections in Canvas-flavored markdown:

  **Section 1 — Data Preview**: Formatted markdown tables with all slide data (Slide 9 KPIs + approval rates, Slide 10 funded metrics, Slide 11 monthly performance metrics, Slide 12 DPD30+ by vantage group, Slide 13 DPD30+ by term). Group by section with headers.

  **Section 2 — Executive Summary Inputs Needed**:

  ```
  ## Executive Summary Inputs Needed

  ### FNPL (Sindhu)
  [Please add your FNPL executive summary here — highlights, risks, key changes]

  ### PCA (Gurmeet)
  [Please add your PCA executive summary here — highlights, risks, key changes]

  ### RAD (Shan)
  [Please add your RAD executive summary here — highlights, risks, key changes]

  ### TTFA (Sindhu)
  [Please add your TTFA executive summary here — highlights, risks, key changes]
  ```

  Include a callout at the bottom: "Please reply to the DM with your inputs or edit this Canvas directly."

**Step B — Send personalized Slack DMs** (all in parallel) with the Canvas link:

1. **Sindhu** (`U0322UD004R`):
   > Hi Sindhu! :wave: Here's the preview for the **FNPL MBR {{MBR_MONTH}}**.
   >
   > **Full preview + input template** :point_down:
   > [FNPL MBR {{MBR_MONTH}} — Preview & Inputs]({{CANVAS_URL}})
   >
   > Could you provide:
   > - **FNPL** executive summary (highlights, risks, key changes)
   > - **TTFA** executive summary
   > - Any **commentary** for Slides 9–13
   >
   > Please reply here or edit the Canvas directly. Thanks! :pray:

2. **Gurmeet** (`U02TXQELKT8`):
   > Hi Gurmeet! :wave: Here's the preview for the **MBR {{MBR_MONTH}}**.
   >
   > **Full preview + input template** :point_down:
   > [FNPL MBR {{MBR_MONTH}} — Preview & Inputs]({{CANVAS_URL}})
   >
   > Could you provide the **PCA** executive summary (highlights, risks, key changes)?
   >
   > Please reply here or edit the Canvas directly. Thanks! :pray:

3. **Shan** (`U09EXBVQ38C`):
   > Hi Shan! :wave: Here's the preview for the **MBR {{MBR_MONTH}}**.
   >
   > **Full preview + input template** :point_down:
   > [FNPL MBR {{MBR_MONTH}} — Preview & Inputs]({{CANVAS_URL}})
   >
   > Could you provide the **RAD** executive summary (highlights, risks, key changes)?
   >
   > Please reply here or edit the Canvas directly. Thanks! :pray:

**Step C — Save all sent message timestamps** for later retrieval (one per DM channel).

**Step D — Notify the running user**:
> "Messages sent to **Sindhu Bhat** (FNPL + TTFA + commentary), **Gurmeet Arora** (PCA), and **Shan Cong** (RAD) with a shared Slack Canvas.
>
> When they reply, come back and tell me **'check replies'** and I'll pick up all responses.
>
> Other options:
> - **'skip slide 3'** — proceed without executive summary
> - **'skip commentary'** — finalize without commentary
> - **'I'll write it'** — provide inputs yourself"

**Step E — Stop and wait.** Do NOT poll. The user will message one of:

| User says | Action |
|-----------|--------|
| `check replies` / `check team` | Read all 3 DM channels (`U0322UD004R`, `U02TXQELKT8`, `U09EXBVQ38C`), find messages newer than saved timestamps, present a status table (see below). |
| `skip slide 3` | Build Slide 3 with "Pending input" placeholders. Proceed to save. |
| `skip commentary` | Finalize without commentary. Still collect Slide 3 inputs if available. |
| `I'll write it` / provides text | Treat as `custom` — ask for slide-specific commentary + Slide 3 content. |

**Step F — Parse replies** (read from all 3 DM channels):

Present a status table to the user:

| Product | Contributor | Status | Input |
|---------|------------|--------|-------|
| FNPL | Sindhu | Received / Pending | (preview of text) |
| PCA | Gurmeet | Received / Pending | (preview of text) |
| RAD | Shan | Received / Pending | (preview of text) |
| TTFA | Sindhu | Received / Pending | (preview of text) |
| Commentary | Sindhu | Received / Pending | (preview of text) |

If all inputs received: present for confirmation, then build Slide 3 and inject commentary.

If partial: ask the user how to handle missing inputs:

| Option | Action |
|--------|--------|
| `wait` | "I'll check again later — tell me when to check" |
| `proceed` | Build with available inputs, leave missing sections as placeholders |
| `I'll fill in` | User provides the missing section content |

**Step G** — Once all confirmed, **switch back to Agent mode**, build Slide 3 from the inputs using the reference HTML template, inject commentary into data slides, and save.

---

## Step 4 — Store Queries & Results ⚡ PARALLEL with Step 5

Run Step 4 and Step 5 simultaneously — they are independent outputs.

Create a **new** Google Sheet each month (never overwrite):

| Sheet | Naming |
|-------|--------|
| Queries + Data | `FNPL MBR <Month Year> - Slides 9–13 Queries (<table_name>)` |
| Validation | `FNPL MBR <Month Year> - Validation` |

Tabs:
- **Slide 9 Raw Results** — Vantage distribution + KPI query results
- **Slide 10 Raw Results** — Funded loan metrics (monthly + total)
- **Slide 11 Raw Results** — Monthly performance metrics (monthly + total)
- **Slide 12 Raw Results** — DPD30+ by vantage group × origination month × MoB
- **Slide 13 Raw Results** — DPD30+ by term × origination month × MoB
- **SQL Queries** — All queries used (Slides 9–13)
- **Validation** — Historical consistency (Slides 9 & 10) + cross-reference results (Slides 9–11)

## Step 5 — Combined HTML Output ⚡ PARALLEL with Step 4

Generate a **single** HTML file: `~/Downloads/FNPL_MBR_<MonYY>.html`

**Git archive (MANDATORY when the agent has repo access):** Copy the same final HTML into the **Consumer Credit Risk** repo and commit:

- **Remote:** `https://github.intuit.com/SBG-Risk-Analytics-Insight/cg-credit-risk`
- **Path:** `exports/fnpl-mbr/FNPL_MBR_<MonYY>.html` (same filename as Downloads)
- **Logo:** Ensure `exports/fnpl-mbr/intuit-ecosystem-white.svg` exists beside the HTML (copy from this skill folder if the folder is new; do not duplicate per month — one SVG shared in that directory).
- **Branch:** Use a short-lived `feat/fnpl-mbr-<MonYY>-html` branch or team convention; open a PR if required. Do **not** overwrite prior months’ files in `exports/fnpl-mbr/`.
- **Pages index:** Add a list entry in `exports/fnpl-mbr/index.html` linking to the new `FNPL_MBR_<MonYY>.html` so the **GitHub Pages** home page stays current (see `exports/fnpl-mbr/README.md`).

**Personal GitHub Pages (preferred for browsing / sharing — use when the user asks to use their personal repo):** Live site **`https://namrataverma-rgb.github.io/fnpl-funnel-dashboard/mbr/`** — source **`https://github.com/namrataverma-rgb/fnpl-funnel-dashboard`**, folder **`mbr/`** (landing `mbr/index.html`, decks `FNPL_MBR_<MonYY>.html` + `intuit-ecosystem-white.svg` beside it). After each monthly build, copy the same files from `~/Downloads/` into `mbr/`, update `mbr/index.html` if adding a new month, commit and push to **`main`**. This is independent of the Intuit archive above; use personal Pages when the user wants a quick public URL or Add Slide / viewer workflow tied to that repo.

If git push is blocked (permissions, VPN, user asks to skip), note it in the run summary and still deliver `~/Downloads/` output.

### Combined HTML verification (automated)

Before considering the combined file final, run the verifier bundled with this skill (substitute your output path):

`python3 ~/.cursor/skills/fnpl-mbr-slide9/verify_fnpl_mbr_html.py ~/Downloads/FNPL_MBR_<MonYY>.html`

It checks Slide 9 chart/table wiring (`#chart9`, metric column alignment), Slide 12/13 **template markers** (layout + Plotly fixes from [template-slide12.html](template-slide12.html) / [template-slide13.html](template-slide13.html)), and that **`SLIDE12_DATA` embeds `tl` on every row** (required for hovers and panel titles — see [queries-slide12.md](queries-slide12.md) `DATA_JSON` section). Exit code **0** = pass; non-zero lists failures. Agents should run this after every build; fix failures by re-reading templates and data contracts, not by patching the combined file ad hoc.

The file contains all slides stacked vertically in this order:

**Cover → Agenda → Exec Summary → Agenda (FNPL) → [GA 2.0 if Apr 2026] → Slide 9 → Slide 10 → Slide 11 → Slide 12 → Slide 13**

with label dividers between them. Each slide is a 1280×720 card on a gray background. The cover slide uses a dark navy background; all other slides use white. No screenshots needed — the HTML itself is the deliverable. The `intuit-ecosystem-white.svg` file must be in the same directory as the HTML for the cover logo to render. The Agenda slide's product order is dynamic based on user selection at Step 0 (Question 3). The Exec Summary slide's content is dynamic based on Slack inputs collected at Step 3C. Slide 4 (Agenda FNPL) highlights FNPL as the active section. Slide 5 (GA 2.0) is **only included for April 2026 MBR** — skip it for all other months.

### Interactive deck viewer: slide feel, Add Slide, Export HTML

Teams may host the combined MBR file with a **browser-based deck shell** (for example GitHub Pages under paths like `team-docs/fnpl-mbr/`, or the user’s personal site **`https://namrataverma-rgb.github.io/fnpl-funnel-dashboard/mbr/`**). That **viewer layer** is separate from the Databricks build in this skill, but agents must treat it as **part of the product** so deliverables stay compatible and colleagues can reproduce the same experience.

#### Presentation-style layout (“slide feel”)

- The **combined HTML shell** (outer `<head>` / body styles from the build) uses a **gray page background** and stacks each slide as a **centered 1280×720 card** with **shadow** and **vertical spacing** (e.g. `.slide` / `.slide-fixed` with `margin: 0 auto 32px`, `box-shadow`, fixed width/height). This makes scrolling feel like a **vertical deck**, not one long unbroken page.
- **Slide templates** in this skill already assume **1280×720**; the shell only adds **page-level** chrome. Do **not** remove slide shadows or fixed dimensions when merging CSS unless the user explicitly changes the design system.

#### Toolbar — Add Slide (“Add New Slide” modal)

- **Add Slide** opens a modal titled **Add New Slide** with **Cancel** and **Create Slide**.
- The user chooses **one** of **six** templates. New slides must follow **FNPL deck conventions** (Inter/Poppins, 16:9 card, **ID-scoped** CSS and scripts — same discipline as [CSS Scoping Rule](#css-scoping-rule)).

**Canonical “Add New Slide” template catalog** (names and subtitles are stable for UX and training):

| Template | Subtitle (shown in UI) | Purpose |
|----------|------------------------|---------|
| **Key Takeaway** | Callout with icon + styled bullets | Executive callout / highlights |
| **Comparison** | Side-by-side metrics with deltas | Two-column KPI comparison |
| **Data Table** | Paste CSV or tab-separated data | Table from pasted delimited data |
| **Commentary** | Title + free-text content slide | Narrative / bullets |
| **Risk Flag** | Issue → Impact → Action format | Structured risk escalation |
| **Bar / Line Chart** | Auto-generates a Plotly chart | Chart slide (Plotly, aligned with Slides 9–13 CDN usage) |

**Relationship to this skill’s build:** Slides produced **by this workflow** (Cover, static slides, **9–13** from SQL + `template*.html`) are **not** created through this modal. The modal is for **additional** slides the team inserts **around** the core pack. When the user asks to “add a **Key Takeaway**” or “match **Add New Slide → Comparison**,” implement that **pattern and subtitle**, not a generic blank slide.

#### Toolbar — Export HTML

- **Export HTML** writes or downloads the **current deck** as a **single static HTML file** for sharing, archiving, or publishing without the live viewer.
- **Authoritative** metrics and charts for **Slides 9–13** still come from this skill’s monthly build; export captures the **post-edit** state if users added slides or text in the viewer.

#### Compatibility rules (agents)

1. **Do not** rename or merge [core data slide IDs](#template-registry) (`#slide9` … `#slide13`) or flatten their CSS — the scoping rule applies in the viewer and in exports.
2. If the repo splits **viewer** (`index.html` / shell) vs **generated** `FNPL_MBR_<MonYY>.html`, **document which file the build overwrites** in the repo README so teammates do not lose Add Slide edits.
3. Prefer the **same Plotly version** as the data slides when implementing **Bar / Line Chart** ad-hoc slides (see combined HTML `<script src="…plotly…">`).

## Monthly Artifact Preservation

**NEVER overwrite** previous months. Each run produces:

| Artifact | File/Name |
|---|---|
| Google Sheet (queries) | `FNPL MBR <Month Year> - Slides 9–13 Queries` |
| Google Sheet (validation) | `FNPL MBR <Month Year> - Validation` |
| Combined HTML (local) | `~/Downloads/FNPL_MBR_<MonYY>.html` |
| Combined HTML (Git archive) | `cg-credit-risk` repo → `exports/fnpl-mbr/FNPL_MBR_<MonYY>.html` (+ `intuit-ecosystem-white.svg` in that folder) |

## Additional Resources

- **Combined HTML verifier:** [verify_fnpl_mbr_html.py](verify_fnpl_mbr_html.py) — run on `~/Downloads/FNPL_MBR_<MonYY>.html` before handoff (see [Step 5 — Combined HTML verification](#combined-html-verification-automated)).
- **Interactive deck viewer** (slide chrome, **Add New Slide** six templates, **Export HTML**): [Step 5 — Interactive deck viewer](#interactive-deck-viewer-slide-feel-add-slide-export-html) (subsection under Combined HTML Output)
- Slide 9 SQL queries: [queries.md](queries.md)
- Slide 10 SQL queries: [queries-slide10.md](queries-slide10.md)
- Slide 11 SQL queries: [queries-slide11.md](queries-slide11.md)
- **Slide 11 table (rows, labels, sub-headers, typography):** [slide11-table-spec.md](slide11-table-spec.md)
- Slide 12 SQL queries: [queries-slide12.md](queries-slide12.md)
- Slide 13 SQL queries: [queries-slide13.md](queries-slide13.md)
- **Slide 13 term charts (Y-axis, lines):** [slide13-chart-spec.md](slide13-chart-spec.md)
- Slide 9 HTML template: [template.html](template.html)
- Slide 10 HTML template: [template-slide10.html](template-slide10.html)
- Slide 11 HTML template: [template-slide11.html](template-slide11.html)
- Slide 12 HTML template: [template-slide12.html](template-slide12.html)
- Slide 13 HTML template: [template-slide13.html](template-slide13.html)
- Cover slide logo (white/reversed): [intuit-ecosystem-white.svg](~/Downloads/intuit-ecosystem-white.svg)
- Schema reference (column mappings & table quirks): [schema-reference.md](schema-reference.md)
- Run history (for table suggestions): [run-history.json](run-history.json)

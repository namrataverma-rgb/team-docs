# Cursor Feature Scout — Week of 2026-04-14 to 2026-04-20

> Scout: [rotating teammate] · Generated: 2026-04-20
> Sources this week: Cursor changelog, Claude Code release notes, Anthropic news, #codeassist-support
> Prior briefing: — · [INDEX](../briefings/INDEX.md)

## TL;DR

- Cursor Composer ships inline HTML editing on rendered output.
- Claude Code adds `plan mode` (read-only review step before execution).
- Intuit Plugin Marketplace opens beta submissions.
- Two new MCPs land: Tableau v2 and a lightweight `github-enterprise-mcp` fork.

---

## 1. Cursor — what changed

### Inline HTML editing in Composer
**Feature:** Composer renders HTML artifacts with an "Edit Mode" toggle allowing inline text edits directly on the rendered page; edits sync back to source.
**Source:** https://cursor.com/changelog
**Status:** Rolling out to pro users.
**Practical implication:** Rendered HTML artifacts become editable in place rather than requiring regeneration from source.

### Composer tabs (parallel conversations)
**Feature:** Multiple Composer threads can run in parallel tabs and share context.
**Source:** https://cursor.com/changelog
**Status:** GA.
**Practical implication:** Keeps long-running threads open while running ad-hoc investigations in another tab without context loss.

## 2. Claude Code — what changed

### `plan mode`
**Feature:** New execution mode where Claude Code outlines intended changes and waits for approval before executing file writes or shell commands.
**Source:** https://docs.claude.com/en/release-notes/claude-code
**Status:** GA.
**Practical implication:** Adds a structured review step before execution. Useful for sensitive or irreversible operations.

### Installable skills (`npx`) stabilizing
**Feature:** Skills published to npm can be installed via `npx @scope/skill-name`. Discovery and versioning working end-to-end.
**Source:** Anthropic engineering blog.
**Status:** Pattern stable.
**Practical implication:** Standard distribution channel for Claude Code skills. Pairs with Intuit's Plugin Marketplace rollout.

## 3. Anthropic product news

### Example announcement
**Feature:** [Product or SDK change].
**Source:** https://www.anthropic.com/news/...
**Practical implication:** [neutral factual sentence].

---

## 4. Intuit AI ecosystem — Slack signal

- **Plugin Marketplace early-trial submission form opens.** Trial users can submit skills for inclusion. Submission template mirrors the SKILL.md spec. (Channel: `#codeassist-support`.)
- **Tableau MCP v2 announced.** Adds dashboard-parameter access, resolves a prior gap. Rollout guide posted. (Channel: `#ds-agentic-dev-mcp-support`.)
- **CG Data Scientist guide updated.** `pydatalake` now the recommended Databricks alternative; Podman-free. (Channel: `#gen-ai-curious`.)
- **finriskai:** Chargeback skill live in Omni V2; lending-specific skills still a gap.

---

## 5. Specifically tracked capabilities

### 5.1 Live editing in HTML pages
New: Cursor Composer Edit Mode — see §1. Rendered HTML is directly editable.

### 5.2 Inline commenting in HTML
No change this week.

### 5.3 Dashboard-level HTML capabilities
Incremental: Tableau MCP v2 exposes dashboard parameters, indirectly improving the quality of HTML dashboards that can be generated from agent output.

### 5.4 New MCPs relevant to analytics work
- Tableau MCP v2 — parameterized dashboard queries.
- Community `github-enterprise-mcp` fork — smaller footprint than codegen-based install.
- No new MCPs targeting Databricks, DDE, or Camunda.

### 5.5 New Cursor chat / compose features
- Composer tabs (GA) — see §1.
- No new rules / hooks features this week.

### 5.6 New Claude Code modes
- `plan mode` — see §2.

---

## 6. Recommended actions (generic)

- Anyone using Claude Code: try `plan mode` once this week to evaluate for your own workflows.
- Anyone on Cursor Composer: the new Edit Mode is worth one test run on any HTML artifact you already generate.
- Upgrade Claude Code CLI to the latest version before using plan mode.

---

## 7. Demo candidate for the monthly bi-weekly

- **Demo candidate:** Cursor Composer Edit Mode applied to any tabular / HTML artifact the team already uses.
- **Owner:** Scout of the month.
- **Why worth 10 minutes:** concrete before/after for a capability many teammates haven't yet seen.

---

*Illustrative example. All release-note details in this sample are not real — run the skill to get live content. Briefing is intentionally team-neutral.*

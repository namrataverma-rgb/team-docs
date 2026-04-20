# Cursor Feature Scout — Week of 2026-04-14 to 2026-04-20

> Scout: nverma14 (rotating teammate) · Generated: 2026-04-20
> Sources this week: Cursor changelog, Claude Code release notes, Anthropic engineering, #codeassist-support, #ds-agentic-dev-mcp-support, #gen-ai-curious
> Prior briefing: — · [INDEX](../briefings/INDEX.md)

## TL;DR

- **Cursor `composer` now supports inline HTML editing** directly on rendered output — immediately useful for our fnpl-mbr-slide9 viewer.
- **Claude Code ships `plan mode`** — a read-only review step before execution. Maps cleanly to our MBR QC review pattern.
- **Intuit Plugin Marketplace opens submission form for beta users** — our `ai-adoption-report` skill is a candidate for first risk-analytics submission.
- **Two new MCPs landed:** Tableau v2 (adds dashboard parameter access) and a lightweight `github-enterprise-mcp` fork.
- **Try this week:** Claude Code's plan mode on the next cohort rebuild; Cursor live HTML edit on one MBR slide.

---

## 1. Cursor — what changed

### Inline HTML editing in Composer
**Feature:** Cursor Composer now renders HTML artifacts with an "Edit Mode" toggle that allows inline text edits directly on the rendered page; edits sync back to source.
**Source:** https://cursor.com/changelog (fictional example)
**Status:** Rolling out to pro users.
**Risk-analytics gloss:** Directly solves a pain in our fnpl-mbr-slide9 viewer — presenters currently regenerate HTML when typos surface mid-review. Worth piloting on April MBR before May rebuild.

### Composer tabs (parallel conversations)
**Feature:** Multiple Composer threads can run in parallel tabs, share context.
**Source:** https://cursor.com/changelog
**Status:** GA.
**Risk-analytics gloss:** Lets us keep a long-running cohort-QC thread open while running ad-hoc investigations in another tab without context loss. Minor quality-of-life win.

## 2. Claude Code — what changed

### `plan mode`
**Feature:** New execution mode where Claude Code outlines intended changes and waits for approval before executing file writes / shell commands.
**Source:** https://docs.claude.com/en/release-notes/claude-code
**Status:** GA on Claude Code CLI v1.0.14+.
**Risk-analytics gloss:** Mirrors our current manual MBR QC rhythm (plan → review → apply). Useful for sensitive script edits like the FNPL build script conversions we did last month. First candidate: use plan mode for the May MBR rebuild.

### Installable skills (`npx`) stabilizing
**Feature:** Skills published to npm can be installed via `npx @scope/skill-name`. Discovery and versioning working end-to-end.
**Source:** Anthropic engineering blog (fictional example link).
**Status:** Pattern stable; Prashant Asthana (per AI Scout briefing) has early examples.
**Risk-analytics gloss:** Our path to Plugin Marketplace parity. When we package `ai-adoption-report`, this is the distribution channel.

## 3. Intuit AI ecosystem — Slack signal

- **Plugin Marketplace early-trial submission form opens** (`#codeassist-support`, mid-week): trial users can now submit a skill for inclusion in the internal marketplace. Submission template mirrors the SKILL.md spec. *Action:* our ai-adoption-report skill is a first-mover candidate.
- **Tableau MCP v2 announced** (`#ds-agentic-dev-mcp-support`): adds dashboard-parameter access, resolves a prior gap for teams querying embedded viz. Rollout guide posted.
- **Ben Stenhaug / CG Data Scientist guide updated** (`#gen-ai-curious`): `pydatalake` is now the recommended Databricks alternative; `Podman`-free.
- **finriskai-agent-all**: Chargeback skill is live in Omni V2; lending-specific skills still a gap — opportunity flagged again by finriskai leads.

---

## 4. Specifically tracked capabilities

### 4.1 Live editing in HTML pages
New: **Cursor Composer Edit Mode** — see §1. Directly applicable to fnpl-mbr-slide9 viewer. **Try this week.**

### 4.2 Inline commenting in HTML
No change this week.

### 4.3 Dashboard-level HTML capabilities
Incremental: Tableau MCP v2 (see §3) exposes dashboard parameters, indirectly improving the quality of HTML dashboards we can generate from agent output.

### 4.4 New MCPs relevant to risk analytics
- Tableau MCP v2 — see §3. Relevant for parameterized dashboard queries.
- A community `github-enterprise-mcp` fork surfaced in `#ds-agentic-dev-mcp-support` — smaller footprint than codegen-based install. Worth testing.
- No new MCPs this week targeting Databricks, DDE, or Camunda.

### 4.5 New Cursor chat / compose features
- Composer tabs (GA) — see §1.
- No new rules / hooks features this week.

### 4.6 New Claude Code modes
- `plan mode` — see §2. **High relevance for our QC-heavy workflows.**

---

## 5. Recommended actions for the team

- **Namrata** should pilot Cursor Composer Edit Mode on the fnpl-mbr-slide9 presenter view by **April 25** and report back in the bi-weekly.
- **Any teammate** who runs MBR rebuilds should try Claude Code `plan mode` once this week — low risk, high learning.
- **Akash** (Playbook owner) should add "when to use Claude Code plan mode vs. Cursor Composer" to the prompt-patterns section of the Playbook.
- Upgrade Claude Code CLI to v1.0.14+ before using plan mode.

---

## 6. For the monthly demo

- **Demo candidate:** Cursor Composer Edit Mode applied to a real MBR slide.
- **Owner:** nverma14 (April scout).
- **Why:** Directly visible "before/after" value; shows how a feature that landed this week immediately unblocks a team pain point.
- **Prep needed:** 10 min to set up; have April MBR Slide 11 ready with one intentional typo to fix inline.

---

*Generated by the `cursor-feature-scout` skill. See `sources.json` for what was checked. All release-note details in this sample are illustrative; run the skill to get live content.*

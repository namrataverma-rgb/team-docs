# AI Adoption Report — alice

> **Generated:** 2026-04-17T15:16:52 · **Host:** macos-HKP9P0QGCT · **OS:** Darwin 24.6.0
> **Transcript window:** last 60 days · **Sessions:** 99

## Executive Summary
Alice maintains a focused set of three custom skills oriented around monthly
business reviews, Intuit-internal AI intelligence, and (meta) AI adoption
tracking itself. Her Cursor environment is deeply integrated with data tooling:
Databricks, Tableau, Atlassian, Google Drive, and a custom data-discovery MCP
are all enabled. Transcript themes over the last 60 days cluster around risk
reporting, MBR automation, and exploratory SQL work. A standout unique
capability is the FNPL MBR skill, which end-to-end generates five presentation
slides from Databricks with deterministic validation.

---

## 1. Custom Skills Inventory

Total skills: **3**

### fnpl-mbr-slide9
- **Path:** `~/.cursor/skills/fnpl-mbr-slide9/SKILL.md`
- **Created / Last modified:** 2026-03-21 → 2026-04-16
- **Purpose:** Generate FNPL Monthly Business Review slides 1 and 9–13 (cover,
  application profile, funded loans profile, monthly performance, DPD30+ by
  Vantage, DPD30+ by term) directly from Databricks.
- **Value add:** Removes ~2 days of manual slide assembly per cycle, enforces
  month-over-month validation against AIG reference tables, and yields
  presentation-quality HTML slides with Edit/Present modes and GitHub commit.
- **Key features:**
  - Pulls curated queries per slide (queries-slide10.md through slide13.md)
  - Validates numbers against prior-month cohorts before rendering
  - Emits high-resolution HTML using deterministic templates
  - Preserves every month's artifacts for audit
- **Limitations:** None documented in SKILL.md — owner should add a Limitations
  section.
- **Challenges:** None documented.
- **Invocation triggers:** MBR, monthly business review, FNPL slide 9–13, DPD30+
  by vantage, DPD30+ by term, Add New Slide, Save for Everyone.

### slack-ai-scout
- **Path:** `~/.cursor/skills/slack-ai-scout/SKILL.md`
- **Created / Last modified:** 2026-03-10 → 2026-04-16
- **Purpose:** Scout how Intuit is adopting AI, filtered for lending, consumer
  credit risk, and financial services teams.
- **Value add:** Gives the risk team a single up-to-date briefing on internal AI
  patterns (Omni Skills V2, Plugin Marketplace, finriskai) alongside
  competitor/regulatory signal — replacing ad-hoc Slack trawling.
- **Key features:**
  - Monthly briefing file (briefing-april-2026.md) with canonical summary
  - Separate reference.md with deeper architecture notes
  - Trigger phrases cover "AI scout", "what's new in AI", "risk AI updates"
- **Limitations:** None documented.
- **Challenges:** None documented.
- **Invocation triggers:** AI scout, what's new in AI, how is Intuit using AI.

### ai-adoption-report
- **Path:** `~/.cursor/skills/ai-adoption-report/SKILL.md`
- **Created / Last modified:** 2026-04-17 → 2026-04-17
- **Purpose:** Auto-generate per-person and team-level AI adoption docs by
  scanning the Cursor environment.
- **Value add:** Eliminates manual team documentation — each teammate runs the
  skill locally, results roll up into a single team report.
- **Key features:**
  - Deterministic environment scanner (skills + rules + hooks + MCP + transcript
    titles) with secret redaction
  - Aggregator that produces team roster, shared-skill registry, unique-skill
    highlights, MCP adoption, and hook adoption
  - Markdown output with optional Google Drive upload
- **Limitations:** Only reads first user message of each transcript (by design,
  for privacy). Does not currently pick up project-level rules.
- **Challenges:** Section extraction depends on SKILL.md headings — skills
  without explicit Limitations/Challenges headings show "None documented".
- **Invocation triggers:** AI documentation, AI adoption report, team AI
  inventory, cursor skills inventory.

---

## 2. Rules & Coding Standards
No custom global rules configured.

## 3. Hooks Automation
Three events are wired to a single audit-logger script:
- `beforeSubmitPrompt` → audit logging before prompts
- `afterFileEdit` → audit logging after file edits
- `afterMCPExecution` → audit logging after MCP calls

All point at `~/.cursor/codeassist/hooks-scripts/audit-logger.sh`.

## 4. MCP Server Footprint

Total enabled servers: **11**

| Server | Purpose (inferred) |
|---|---|
| fetch | Generic URL fetching |
| filesystem | Local file reads/writes |
| google-drive-mcp | Drive upload / doc export |
| tableau | Tableau workbook access |
| data-discovery-mcp | Internal dataset catalog |
| databricks-mcp | SQL execution on Databricks warehouses |
| atlassian | Jira + Confluence |
| dde-access-mcp | Internal DDE access |
| camunda-cockpit | Workflow inspection |
| intuit-github-mcp | Internal GitHub |
| plugin-slack-slack | Slack access |

---

## 5. AI-Assisted Work — Recent Themes

Based on the first user message of **99** agent sessions over the last 60 days
(full conversation bodies are NOT analyzed or shared).

### Theme Clusters
- **MBR slide automation** (~22 sessions): generating, validating, and updating
  FNPL slides 9–13 against Databricks.
- **Risk analytics & Vantage cohort work** (~18 sessions): DPD30+ bucketing,
  cohort pulls, backtesting.
- **AI tooling meta-work** (~12 sessions): authoring skills, tuning hooks,
  experimenting with Cursor features.
- **Slack/Intuit AI intelligence** (~10 sessions): monthly briefing refreshes.
- **Ad-hoc data exploration** (~15 sessions): exploratory SQL and dataset
  discovery.
- **Documentation & process** (~10 sessions): Confluence/Google Doc drafts.
- **Other** (~12 sessions): miscellaneous.

### Standout Unique Tasks
- Built the FNPL MBR slide generator end-to-end with deterministic validation.
- Authored the Slack AI Scout skill to consolidate internal AI intel.
- Built this AI Adoption Report skill itself (meta!).
- Ran month-over-month variance investigation on DPD30+ by term.

---

## 6. Self-Assessment

- **What's working well:** TODO: owner to fill in.
- **Biggest gaps / limitations I hit:** TODO: owner to fill in.
- **Skills I'd like to build next:** TODO: owner to fill in.

---

*Generated by the `ai-adoption-report` skill.*

# Slide 12 — DPD30+ by Vintage and Vantage Group

> Source: Databricks notebook **SLIDE 17** ("Vantage Vintage with origination Month").
> Only substitute **`{{BASE_TABLE}}`** and **`{{MOB_CAP}}`** — no cutoff date needed.
> **No `asofDate` filter** — `loan_repayment_daily` is joined on `daysonbooks` values only (all historical snapshots).
> **Cohort base:** all `funded_loan = 1` loans in `{{BASE_TABLE}}`.
> **Charge-off:** `intuitstatus = 'CHARGED_OFF'` counts as delinquent at every MoB threshold.

---

## Query — DPD30+ by Vantage Group × Origination Month × MoB

Replace `{{BASE_TABLE}}` with your table (e.g. `sandbox_risk_7216.fnpl_base_alpha_ga1`) and `{{MOB_CAP}}` with the highest MoB index to show (e.g. `4` for Mar 2026, `5` for Apr 2026).

```sql
WITH base_loans AS (
  SELECT
    s.application_id AS loanid,
    CASE
      WHEN s.vantageScore3 IS NULL OR s.vantageScore3 < 600 THEN '1. Subprime'
      WHEN s.vantageScore3 >= 780                           THEN '4. Super Prime'
      WHEN s.vantageScore3 >= 660                           THEN '3. Prime'
      WHEN s.vantageScore3 >= 600                           THEN '2. Near Prime'
      ELSE '1. Subprime'
    END AS vantageScoreGroup,
    last_day(lo.originationDate) AS origination_month
  FROM {{BASE_TABLE}} s
  JOIN intuit_lending_loanprofiles_dwh.loan_origination lo
    ON s.application_id = lo.loanuuid
  WHERE s.funded_loan = 1
),

cohort_size AS (
  SELECT
    vantageScoreGroup,
    origination_month,
    COUNT(loanid) AS total_loans
  FROM base_loans
  GROUP BY 1, 2
),

-- M0 = day 1; M1 = day 30; M2 = day 60; ... M{{MOB_CAP}} = day {{MOB_CAP}}*30
-- Add more WHEN lines if {{MOB_CAP}} increases (e.g. WHEN 150 THEN 'M5' for M5)
dob_snapshots AS (
  SELECT
    lrd.applicationid AS loanid,
    lrd.daysonbooks,
    lrd.dayspastdue,
    lrd.intuitstatus,
    CASE
      WHEN lrd.daysonbooks = 1   THEN 'M0'
      WHEN lrd.daysonbooks = 30  THEN 'M1'
      WHEN lrd.daysonbooks = 60  THEN 'M2'
      WHEN lrd.daysonbooks = 90  THEN 'M3'
      WHEN lrd.daysonbooks = 120 THEN 'M4'
      WHEN lrd.daysonbooks = 150 THEN 'M5'
      WHEN lrd.daysonbooks = 180 THEN 'M6'
    END AS mob
  FROM intuit_lending_servicing_capital_dwh.loan_repayment_daily lrd
  WHERE lrd.daysonbooks IN (1, 30, 60, 90, 120, 150, 180)
),

mob_performance AS (
  SELECT
    b.vantageScoreGroup,
    b.origination_month,
    d.mob,
    SUM(CASE WHEN d.dayspastdue >= 7  OR d.intuitstatus = 'CHARGED_OFF' THEN 1 ELSE 0 END) AS loans_7dpd,
    SUM(CASE WHEN d.dayspastdue >= 30 OR d.intuitstatus = 'CHARGED_OFF' THEN 1 ELSE 0 END) AS loans_30dpd
  FROM base_loans b
  LEFT JOIN dob_snapshots d ON b.loanid = d.loanid
  GROUP BY 1, 2, 3
)

SELECT
  p.vantageScoreGroup,
  p.origination_month,
  p.mob,
  c.total_loans,
  p.loans_7dpd,
  p.loans_30dpd,
  p.loans_7dpd  / NULLIF(c.total_loans, 0) AS rate_7dpd,
  p.loans_30dpd / NULLIF(c.total_loans, 0) AS rate_30dpd
FROM mob_performance p
JOIN cohort_size c
  ON  p.vantageScoreGroup = c.vantageScoreGroup
  AND p.origination_month = c.origination_month
WHERE p.mob IS NOT NULL
ORDER BY 1, 2, 3
```

---

## `{{MOB_CAP}}` per MBR month

The `IN (1, 30, 60, …)` list already includes up to M6 (180 days). The `WHERE p.mob IS NOT NULL` at the end ensures only rows matching a `CASE` label are returned. Use **`{{MOB_CAP}}`** (set once in the template and build script) to filter/cap in the chart — SQL returns everything it has, chart renders only up to the cap.

| MBR month | `{{MOB_CAP}}` | MoB range shown |
|-----------|---------------|-----------------|
| Mar 2026  | `4`           | M0–M4           |
| Apr 2026  | `5`           | M0–M5           |
| May 2026  | `6`           | M0–M6           |

---

## Tables Involved

| Table | Role |
|---|---|
| `{{BASE_TABLE}}` | Funded loans base (parameterized) |
| `intuit_lending_loanprofiles_dwh.loan_origination` | Origination date, loan UUID join |
| `intuit_lending_servicing_capital_dwh.loan_repayment_daily` | All DoB snapshots at explicit `daysonbooks` values — no `asofDate` filter |

## Output Columns

| Column | Description |
|---|---|
| `vantageScoreGroup` | Vantage band: 1. Subprime, 2. Near Prime, 3. Prime, 4. Super Prime |
| `origination_month` | Last day of origination month |
| `mob` | MoB checkpoint: M0, M1, … (only non-null rows returned) |
| `total_loans` | Cohort size — constant denominator per vantage group × origination month |
| `loans_7dpd` | Count of loans with DPD ≥ 7 **or** charged off at that MoB |
| `loans_30dpd` | Count of loans with DPD ≥ 30 **or** charged off at that MoB |
| `rate_7dpd` | 7DPD+ rate = loans_7dpd / total_loans |
| `rate_30dpd` | 30DPD+ rate = loans_30dpd / total_loans |

## `DATA_JSON` for [template-slide12.html](template-slide12.html) (mandatory)

Each row embedded in `SLIDE12_DATA` **must** include:

| Field | Source | Notes |
|--------|--------|--------|
| `vg` | `vantageScoreGroup` | Exact strings: `1. Subprime` … `4. Super Prime` |
| `om` | `origination_month` | ISO date string, e.g. `2025-10-31` |
| `mob` | `mob` | `M0`, `M1`, … |
| `r` | `rate_30dpd` | Decimal 0–1 |
| **`tl`** | **`total_loans`** | **Required.** For hovers and panel `(N=…)` title. |

**Alignment with `{{MOB_CAP}}` (mandatory):** Use the same integer in `template-slide12.html` (`SLIDE12_MOB_CAP`) and the build script. The template renders only rows where `mob ≤ MOB_CAP`; rows beyond the cap are ignored.

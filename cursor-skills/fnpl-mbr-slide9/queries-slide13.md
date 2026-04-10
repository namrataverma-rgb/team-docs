# Slide 13 — DPD30+ by Vintage and Term

> Source: Databricks notebook **SLIDE 18** ("Term Vintage with origination Month").
> Only substitute **`{{BASE_TABLE}}`** and **`{{MOB_CAP}}`** — no cutoff date needed.
> **No `asofDate` filter** — same approach as Slide 12: join on explicit `daysonbooks` values only.
> **Cohort base:** all `funded_loan = 1` loans in `{{BASE_TABLE}}`.
> **Charge-off:** `intuitstatus = 'CHARGED_OFF'` counts as delinquent at every MoB threshold.

---

## Query A — DPD30+ by Term × Origination Month × MoB

```sql
WITH base_loans AS (
  SELECT
    s.application_id AS loanid,
    s.term,
    last_day(lo.originationDate) AS origination_month
  FROM {{BASE_TABLE}} s
  JOIN intuit_lending_loanprofiles_dwh.loan_origination lo
    ON s.application_id = lo.loanuuid
  WHERE s.funded_loan = 1
),

cohort_size AS (
  SELECT
    term,
    origination_month,
    COUNT(loanid) AS total_loans
  FROM base_loans
  GROUP BY 1, 2
),

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
    b.term,
    b.origination_month,
    d.mob,
    SUM(CASE WHEN d.dayspastdue >= 7  OR d.intuitstatus = 'CHARGED_OFF' THEN 1 ELSE 0 END) AS loans_7dpd,
    SUM(CASE WHEN d.dayspastdue >= 30 OR d.intuitstatus = 'CHARGED_OFF' THEN 1 ELSE 0 END) AS loans_30dpd
  FROM base_loans b
  LEFT JOIN dob_snapshots d
    ON b.loanid = d.loanid
  GROUP BY 1, 2, 3
)

SELECT
  p.term,
  p.origination_month,
  p.mob,
  c.total_loans,
  p.loans_7dpd,
  p.loans_30dpd,
  p.loans_7dpd  / NULLIF(c.total_loans, 0) AS rate_7dpd,
  p.loans_30dpd / NULLIF(c.total_loans, 0) AS rate_30dpd
FROM mob_performance p
JOIN cohort_size c
  ON p.term = c.term
  AND p.origination_month = c.origination_month
WHERE p.mob IS NOT NULL
ORDER BY 1, 2, 3
```

---

## Query B — Cohort Summary (for data tables under charts)

```sql
SELECT
  s.term,
  last_day(lo.originationDate) AS origination_month,
  COUNT(*) AS n_loans,
  ROUND(AVG(CAST(s.vantageScore3 AS DOUBLE)), 0) AS avg_vantage,
  ROUND(PERCENTILE_APPROX(CAST(s.tt_amountTotalIncome AS DOUBLE), 0.5) / 1000, 0) AS median_income_k
FROM {{BASE_TABLE}} s
JOIN intuit_lending_loanprofiles_dwh.loan_origination lo
  ON s.application_id = lo.loanuuid
WHERE s.funded_loan = 1
GROUP BY 1, 2
ORDER BY 1, 2
```

---

## `{{MOB_CAP}}` per MBR month

Same rule as [queries-slide12.md](queries-slide12.md). SQL returns all available MoB rows; the template renders only up to `{{MOB_CAP}}`.

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

## Output Columns (Query A)

| Column | Description |
|---|---|
| `term` | Loan term (e.g., 3, 6, 9 months) |
| `origination_month` | Last day of origination month |
| `mob` | MoB checkpoint: M0, M1, … (only non-null rows returned) |
| `total_loans` | Cohort size (constant denominator per term × month) |
| `loans_7dpd` | Count of loans with DPD ≥ 7 **or** charged off at that MoB |
| `loans_30dpd` | Count of loans with DPD ≥ 30 **or** charged off at that MoB |
| `rate_7dpd` | 7DPD+ rate = loans_7dpd / total_loans |
| `rate_30dpd` | 30DPD+ rate = loans_30dpd / total_loans |

### Output Columns (Query B)

| Column | Description |
|---|---|
| `term` | Loan term |
| `origination_month` | Last day of origination month |
| `n_loans` | Number of funded loans in the cohort |
| `avg_vantage` | Average Vantage 3.0 score |
| `median_income_k` | Median total income ($K) from `tt_amountTotalIncome` |

---

## Slide Focus

Vintage DPD30+ curves per term (charts); cohort summary table below each chart (Query B). Term inclusion rule: only include a term if it has at least one non-zero `rate_30dpd` row — omit entirely otherwise and note it in `{{TERMS_SUBTITLE}}`.

## MoB cap

Use the same `{{MOB_CAP}}` integer in this SQL (via `WHERE p.mob IS NOT NULL` + template filtering) and in [template-slide13.html](template-slide13.html) (`SLIDE13_MOB_CAP`).

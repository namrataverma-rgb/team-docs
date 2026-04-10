# Slide 11 — Monthly Performance Query (ROLLUP)

> Source: Databricks notebook, based on origination month (not application month).
> Combined into a **single ROLLUP query** — monthly rows + grand total in one round-trip.
> Servicing snapshot uses **`date_sub(CAST('{{CUTOFF_DATE}}' AS DATE), 3)`** (same role as prior `current_date()-3`, tied to Question 3 cutoff).
> Replace `{{BASE_TABLE}}` and `{{CUTOFF_DATE}}` from Step 0.
>
> **Not vintage MoB slides:** Explicit `loan_repayment_daily.daysonbooks IN (1, 30, 60, …)` checkpoint logic lives in **[queries-slide12.md](queries-slide12.md)** / **[queries-slide13.md](queries-slide13.md)** with **`{{MOB_CAP}}`** — not in this Slide 11 query.
>
> **HTML table (default MBR deck):** Which metrics appear in Slide 11 is defined in **[slide11-table-spec.md](slide11-table-spec.md)** (reduced row set: no 1DPD / 60DPD / 90DPD unless the user asks for an expanded table). The query below still computes full metrics for validation and optional use.
>
> **Key change vs prior version**: eligibility flags (`1dob`, `7dob`, `30dob`, `60dob`, `90dob`) now use
> `datediff(date_sub(CAST('{{CUTOFF_DATE}}' AS DATE), 3), lo.originationDate)` (calendar days since funding) rather than `dob_asof`
> from the servicing table. DPD+ flags now include `CHARGED_OFF` status so charged-off loans
> always count as delinquent regardless of reported DPD.

---

## Single Query — Monthly Performance + Total (ROLLUP)

> Uses `GROUP BY 1 WITH ROLLUP` to produce monthly rows AND a grand-total row (`app_month = NULL`) in a single query.

```sql
WITH base AS (
  SELECT
      s.application_id                                           AS loanid,
      last_day(lo.originationDate)                              AS app_month,
      s.amount,
      s.vantageScore3,
      datediff(date_sub(CAST('{{CUTOFF_DATE}}' AS DATE), 3), lo.originationDate) AS days_since_funded
  FROM {{BASE_TABLE}} s
  JOIN intuit_lending_loanprofiles_dwh.loan_origination lo
    ON s.application_id = lo.loanuuid
  WHERE s.funded_loan = 1
    AND s.app_date <= CAST('{{CUTOFF_DATE}}' AS DATE)
),

asof_snap AS (
  SELECT * FROM (
    SELECT
        lrd.applicationid                                        AS loanid,
        lrd.intuitstatus                                         AS intuit_status_asof,
        lrd.dayspastdue                                          AS dpd_asof,
        lrd.principalbalance                                     AS principal_balance_asof,
        lrd.asofDate                                             AS asofDate,
        CAST(lrd.chargeoff.chargeOffDate AS DATE)                AS charge_off_date,
        CAST(lrd.chargeoff.chargeOffPrincipalBalance AS DOUBLE)  AS charge_off_principal_bal,
        CAST(lrd.chargeoff.chargeOffBalance AS DOUBLE)           AS charge_off_balance,
        ROW_NUMBER() OVER (
            PARTITION BY lrd.applicationid
            ORDER BY
              CASE
                WHEN lrd.asofDate       = date_sub(CAST('{{CUTOFF_DATE}}' AS DATE), 3) THEN 1
                WHEN lrd.carryThroughDate = '3008-01-01'   THEN 2
                ELSE 3
              END ASC
        ) AS record_priority
    FROM intuit_lending_servicing_capital_dwh.loan_repayment_daily lrd
    WHERE lrd.asofDate        = date_sub(CAST('{{CUTOFF_DATE}}' AS DATE), 3)
       OR lrd.carryThroughDate = '3008-01-01'
  )
  WHERE record_priority = 1
),

final_loan AS (
  SELECT
      b.app_month,
      b.loanid,
      b.amount,
      s.intuit_status_asof,
      COALESCE(s.principal_balance_asof, 0.0)  AS principal_balance_asof,
      COALESCE(s.dpd_asof, 0)                   AS dayspastdue,
      s.charge_off_date,
      s.charge_off_principal_bal,
      s.charge_off_balance,
      s.asofDate,
      b.vantageScore3,

      /* ── eligibility flags: calendar days since origination ── */
      CASE WHEN COALESCE(b.days_since_funded, 0) >  30 THEN 1 ELSE 0 END AS `1dob`,
      CASE WHEN COALESCE(b.days_since_funded, 0) >  37 THEN 1 ELSE 0 END AS `7dob`,
      CASE WHEN COALESCE(b.days_since_funded, 0) >  60 THEN 1 ELSE 0 END AS `30dob`,
      CASE WHEN COALESCE(b.days_since_funded, 0) >  90 THEN 1 ELSE 0 END AS `60dob`,
      CASE WHEN COALESCE(b.days_since_funded, 0) > 120 THEN 1 ELSE 0 END AS `90dob`,

      /* ── delinquency flags: charged-off loans always count ── */
      CASE WHEN COALESCE(s.dpd_asof, 0) >=  1 OR s.intuit_status_asof = 'CHARGED_OFF' THEN 1 ELSE 0 END AS `1dpd_plus`,
      CASE WHEN COALESCE(s.dpd_asof, 0) >=  7 OR s.intuit_status_asof = 'CHARGED_OFF' THEN 1 ELSE 0 END AS `7dpd_plus`,
      CASE WHEN COALESCE(s.dpd_asof, 0) >= 30 OR s.intuit_status_asof = 'CHARGED_OFF' THEN 1 ELSE 0 END AS `30dpd_plus`,
      CASE WHEN COALESCE(s.dpd_asof, 0) >= 60 OR s.intuit_status_asof = 'CHARGED_OFF' THEN 1 ELSE 0 END AS `60dpd_plus`,
      CASE WHEN COALESCE(s.dpd_asof, 0) >= 90 OR s.intuit_status_asof = 'CHARGED_OFF' THEN 1 ELSE 0 END AS `90dpd_plus`,

      /* ── status flags ── */
      CASE WHEN s.intuit_status_asof = 'PAID_OFF'    THEN 1 ELSE 0 END AS is_paid_off_asof,
      CASE WHEN s.intuit_status_asof = 'CHARGED_OFF' THEN 1 ELSE 0 END AS is_charged_off_asof,
      CASE WHEN s.intuit_status_asof NOT IN ('PAID_OFF','CHARGED_OFF') THEN 1 ELSE 0 END AS active_loan,
      CASE
        WHEN s.intuit_status_asof NOT IN ('PAID_OFF','CHARGED_OFF') THEN 1
        WHEN s.intuit_status_asof = 'CHARGED_OFF'
             AND s.charge_off_date IS NOT NULL
             AND last_day(s.charge_off_date) = last_day(s.asofDate) THEN 1
        ELSE 0
      END AS outstanding_loan

  FROM base b
  LEFT JOIN asof_snap s ON b.loanid = s.loanid
)

SELECT
    app_month,

    /* ── volume ── */
    COUNT(*)                  AS n_loans,
    SUM(amount)               AS funded_amount,
    SUM(is_paid_off_asof)     AS n_paid_off_asof,
    SUM(active_loan)          AS active_loans,

    /* ── count-based delinquency rates ── */
    SUM(`1dpd_plus`)  / NULLIF(SUM(`1dob`),  0)  AS `1dpd_plus_rate`,
    SUM(`7dpd_plus`)  / NULLIF(SUM(`7dob`),  0)  AS `7dpd_plus_rate`,
    SUM(`30dpd_plus`) / NULLIF(SUM(`30dob`), 0)  AS `30dpd_plus_rate`,
    SUM(`60dpd_plus`) / NULLIF(SUM(`60dob`), 0)  AS `60dpd_plus_rate`,
    SUM(`90dpd_plus`) / NULLIF(SUM(`90dob`), 0)  AS `90dpd_plus_rate`,

    /* ── roll rate: 30DPD → charge-off ── */
    SUM(is_charged_off_asof) / NULLIF(SUM(`30dpd_plus`), 0) AS rollrate_30_to_co,

    /* ── dollar-based delinquency rates (balance + charge-off principal / orig balance) ── */
    SUM(CASE WHEN `1dpd_plus`  = 1 AND `1dob`  = 1
             THEN principal_balance_asof + charge_off_principal_bal ELSE 0 END)
      / NULLIF(SUM(CASE WHEN `1dob`  = 1 THEN amount ELSE 0 END), 0)  AS dollar_1dpd_plus_rate,

    SUM(CASE WHEN `7dpd_plus`  = 1 AND `7dob`  = 1
             THEN principal_balance_asof + charge_off_principal_bal ELSE 0 END)
      / NULLIF(SUM(CASE WHEN `7dob`  = 1 THEN amount ELSE 0 END), 0)  AS dollar_7dpd_plus_rate,

    SUM(CASE WHEN `30dpd_plus` = 1 AND `30dob` = 1
             THEN principal_balance_asof + charge_off_principal_bal ELSE 0 END)
      / NULLIF(SUM(CASE WHEN `30dob` = 1 THEN amount ELSE 0 END), 0)  AS dollar_30dpd_plus_rate,

    SUM(CASE WHEN `60dpd_plus` = 1 AND `60dob` = 1
             THEN principal_balance_asof + charge_off_principal_bal ELSE 0 END)
      / NULLIF(SUM(CASE WHEN `60dob` = 1 THEN amount ELSE 0 END), 0)  AS dollar_60dpd_plus_rate,

    SUM(CASE WHEN `90dpd_plus` = 1 AND `90dob` = 1
             THEN principal_balance_asof + charge_off_principal_bal ELSE 0 END)
      / NULLIF(SUM(CASE WHEN `90dob` = 1 THEN amount ELSE 0 END), 0)  AS dollar_90dpd_plus_rate,

    /* ── dollar roll rate: 30DPD → charge-off (denominator includes CO principal) ── */
    SUM(CASE WHEN is_charged_off_asof = 1 THEN charge_off_principal_bal ELSE 0 END)
      / NULLIF(SUM(CASE WHEN `30dpd_plus` = 1 THEN principal_balance_asof + charge_off_principal_bal ELSE 0 END), 0)
                                                                        AS dollar_rollrate_30_to_co,

    /* ── status rates ── */
    SUM(is_paid_off_asof)    / COUNT(*)           AS paid_off_rate_asof,
    SUM(is_charged_off_asof) / COUNT(*)           AS charged_off_asof_rate,
    SUM(CASE WHEN is_charged_off_asof = 1
             THEN charge_off_principal_bal ELSE 0 END)
      / NULLIF(SUM(amount), 0)                    AS dollar_charged_off_asof_rate,

    /* ── raw counts ── */
    SUM(`1dpd_plus`)  AS n_1dpd_plus,
    SUM(`7dpd_plus`)  AS n_7dpd_plus,
    SUM(`30dpd_plus`) AS n_30dpd_plus,
    SUM(`60dpd_plus`) AS n_60dpd_plus,
    SUM(`90dpd_plus`) AS n_90dpd_plus,
    SUM(`1dob`)       AS `1dpd_elig`,
    SUM(`7dob`)       AS `7dpd_elig`,
    SUM(`30dob`)      AS `30dpd_elig`,
    SUM(`60dob`)      AS `60dpd_elig`,

    /* ── dollar balance breakdowns ── */
    SUM(CASE WHEN `1dpd_plus`  = 1 AND `1dob`  = 1
             THEN principal_balance_asof + charge_off_principal_bal ELSE 0 END) AS dollar_1dpd_plus_balance,
    SUM(CASE WHEN `1dob`  = 1 THEN amount ELSE 0 END)                           AS dollar_1dpd_elig_amount,
    SUM(CASE WHEN `7dpd_plus`  = 1 AND `7dob`  = 1
             THEN principal_balance_asof + charge_off_principal_bal ELSE 0 END) AS dollar_7dpd_plus_balance,
    SUM(CASE WHEN `7dob`  = 1 THEN amount ELSE 0 END)                           AS dollar_7dpd_elig_amount,
    SUM(CASE WHEN `30dpd_plus` = 1 AND `30dob` = 1
             THEN principal_balance_asof + charge_off_principal_bal ELSE 0 END) AS dollar_30dpd_plus_balance,
    SUM(CASE WHEN `30dob` = 1 THEN amount ELSE 0 END)                           AS dollar_30dpd_elig_amount,
    SUM(CASE WHEN `60dpd_plus` = 1 AND `60dob` = 1
             THEN principal_balance_asof + charge_off_principal_bal ELSE 0 END) AS dollar_60dpd_plus_balance,
    SUM(CASE WHEN `60dob` = 1 THEN amount ELSE 0 END)                           AS dollar_60dpd_elig_amount,

    SUM(outstanding_loan) AS outstanding_loans

FROM final_loan
GROUP BY 1 WITH ROLLUP
ORDER BY app_month NULLS LAST
```

### How to interpret results

| `app_month` | Meaning |
|---|---|
| A date value (e.g. `2025-10-31`) | Monthly row |
| `NULL` | **Total row** — grand totals across all months |

In the agent, split the results: rows where `app_month IS NOT NULL` → monthly columns, row where `app_month IS NULL` → "Total" column.

---

## Key Adaptations from Original Notebook

| Original (hardcoded) | Adapted (dynamic) |
|---|---|
| `sandbox_risk_7216.fnpl_base_alpha_ga2` | `{{BASE_TABLE}}` (user-selected) |
| `datediff('2026-04-03', ...)` | `datediff(date_sub(CAST('{{CUTOFF_DATE}}' AS DATE), 3), ...)` |
| `lrd.asofDate = '2026-04-03'` | `lrd.asofDate = date_sub(CAST('{{CUTOFF_DATE}}' AS DATE), 3)` |
| `WHEN lrd.asofDate = '2026-04-03' THEN 1` | `WHEN lrd.asofDate = date_sub(CAST('{{CUTOFF_DATE}}' AS DATE), 3) THEN 1` |
| `dob_asof` from servicing table for eligibility | `days_since_funded` = calendar days since origination |
| 7DPD/30DPD = `dpd_asof >= N` only | 7DPD/30DPD = `dpd_asof >= N OR CHARGED_OFF` |

## Tables Involved

| Table | Role |
|---|---|
| `{{BASE_TABLE}}` | Funded loans base (parameterized) |
| `intuit_lending_loanprofiles_dwh.loan_origination` | Origination date, loan UUID join |
| `intuit_lending_servicing_capital_dwh.loan_repayment_daily` | Servicing snapshot — DPD, charge-off, principal balance |

## Metrics Produced (single ROLLUP query)

| Metric | Column | Format |
|---|---|---|
| # Loans | `n_loans` | Comma integer |
| $ Funded | `funded_amount` | `$X.XM` |
| # Paid Off | `n_paid_off_asof` | Comma integer |
| # Active Loans | `active_loans` | Comma integer |
| 1DPD+ Rate | `1dpd_plus_rate` | `X.X%` |
| 7DPD+ Rate (count) | `7dpd_plus_rate` | `X.X%` |
| 30DPD+ Rate (count) | `30dpd_plus_rate` | `X.X%` |
| 60DPD+ Rate (count) | `60dpd_plus_rate` | `X.X%` |
| 90DPD+ Rate (count) | `90dpd_plus_rate` | `X.X%` |
| Roll Rate 30→CO (count) | `rollrate_30_to_co` | `X.X%` |
| $ 1DPD+ Rate | `dollar_1dpd_plus_rate` | `X.X%` |
| $ 7DPD+ Rate | `dollar_7dpd_plus_rate` | `X.X%` |
| $ 30DPD+ Rate | `dollar_30dpd_plus_rate` | `X.X%` |
| $ 60DPD+ Rate | `dollar_60dpd_plus_rate` | `X.X%` |
| $ 90DPD+ Rate | `dollar_90dpd_plus_rate` | `X.X%` |
| $ Roll Rate 30→CO | `dollar_rollrate_30_to_co` | `X.X%` |
| % Paid Off | `paid_off_rate_asof` | `X.X%` |
| # Charge Off Rate | `charged_off_asof_rate` | `X.X%` |
| $ Charge Off Rate | `dollar_charged_off_asof_rate` | `X.X%` |
| Outstanding Loans | `outstanding_loans` | Comma integer |
| 1DPD Eligible | `1dpd_elig` | Comma integer |
| 7DPD Eligible | `7dpd_elig` | Comma integer |
| 30DPD Eligible | `30dpd_elig` | Comma integer |
| 60DPD Eligible | `60dpd_elig` | Comma integer |
| Raw counts | `n_1dpd_plus` … `n_90dpd_plus` | Comma integer |
| Dollar balance breakdowns | `dollar_Xdpd_plus_balance`, `dollar_Xdpd_elig_amount` | Dollar |

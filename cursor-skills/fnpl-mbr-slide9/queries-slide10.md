# FNPL MBR Slide 10 — SQL Query (Funded Loans Profile)

Replace `{{BASE_TABLE}}` and `{{CUTOFF_DATE}}` with the confirmed base table and data cutoff (ISO `YYYY-MM-DD`) from Step 0.

## Single Query — Funded Loans by Month + Total (ROLLUP)

Uses `last_day(lo.originationDate)` as the funded month (not application month).
Joins to `loan_origination` for origination date and `agg_auth_id_accepted_refund` for state refund %.

**ROLLUP** produces monthly rows AND a grand-total row (`funded_month = NULL`) in a single query, eliminating the need for a separate Total query.

```sql
SELECT
  last_day(lo.originationDate) AS funded_month,
  COUNT(*) AS loans,
  SUM(s.amount) AS funded_amount,
  SUM(s.amount) / COUNT(*) AS avg_loan_size,
  SUM(s.term * s.amount) / SUM(s.amount) AS wa_term,
  SUM(s.apr * s.amount) / SUM(s.amount) AS wa_apr,
  SUM(s.vantageScore3 * s.amount) / SUM(s.amount) AS wa_vantage,
  AVG(CASE WHEN s.mxsPrediction IS NOT NULL THEN s.final_risk_segment END) AS avg_rs,
  PERCENTILE_APPROX(CAST(s.tt_amountTotalIncome AS DOUBLE), 0.5) AS median_income,
  SUM(CASE WHEN s.ck_placement = 'Prominent' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS ck_low_risk_pct,
  SUM(CASE WHEN s.app_type LIKE '%Mobile%' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS pct_mobile_channel,
  ROUND(AVG(s.DTI_ExclPmt), 2) AS avg_dti,
  COUNT(r.auth_id) * 1.0 / COUNT(*) AS state_refund_pct
FROM {{BASE_TABLE}} s
JOIN intuit_lending_loanprofiles_dwh.loan_origination lo
  ON s.application_id = lo.loanuuid
LEFT JOIN tax_dm.agg_auth_id_accepted_refund r
  ON s.authId = r.auth_id
  AND r.tax_year = YEAR(lo.originationDate) - 1
  AND r.avg_state_refund_amount > 0
WHERE s.funded_loan = 1
  AND s.app_date <= CAST('{{CUTOFF_DATE}}' AS DATE)
GROUP BY 1 WITH ROLLUP
ORDER BY 1 NULLS LAST
```

### How to interpret results

| `funded_month` | Meaning |
|---|---|
| A date value (e.g. `2025-10-31`) | Monthly row |
| `NULL` | **Total row** — grand totals across all months |

In the agent, split the results: rows where `funded_month IS NOT NULL` → monthly columns, row where `funded_month IS NULL` → "Total" column.

> **Note**: `MEDIAN` is replaced with `PERCENTILE_APPROX(..., 0.5)` which is ROLLUP-compatible in Databricks. It produces an approximate median that is functionally equivalent for presentation purposes.

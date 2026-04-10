# FNPL MBR Slide 9 — SQL Queries

Replace `{{BASE_TABLE}}` and `{{CUTOFF_DATE}}` from Step 0 (Questions **4** and **2**). **`{{POLICY_GROUPS}}`** is **fixed** in the skill (not asked): `('Alpha/Beta','Beta2.0','GA1.0','GA1.1','GA2.0')`. `{{CUTOFF_DATE}}` = ISO `YYYY-MM-DD` from Question **2** (Data Cutoff Date).

## Query 1 — Vantage Score Distribution (Cell 15)

```sql
SELECT
  app_month,
  SUM(CASE WHEN vantageScore3 >= 780 THEN 1 ELSE 0 END) AS super_prime,
  SUM(CASE WHEN vantageScore3 >= 660 AND vantageScore3 < 780 THEN 1 ELSE 0 END) AS prime,
  SUM(CASE WHEN vantageScore3 >= 600 AND vantageScore3 < 660 THEN 1 ELSE 0 END) AS near_prime,
  SUM(CASE WHEN vantageScore3 < 600 THEN 1 ELSE 0 END) AS subprime,
  SUM(CASE WHEN vantageScore3 IS NULL THEN 1 ELSE 0 END) AS invalid,
  COUNT(*) AS total_apps
FROM {{BASE_TABLE}}
WHERE app_number2 = 1
  AND la_status != 'OFFER_PENDING'
  AND app_date <= CAST('{{CUTOFF_DATE}}' AS DATE)
GROUP BY app_month
ORDER BY app_month
```

## Query 2 — KPIs & Contingent Approval Rate (Cell 16)

```sql
SELECT
  app_month,
  COUNT(*) AS num_apps,
  ROUND(AVG(vantageScore3), 0) AS avg_vantage,
  PERCENTILE_APPROX(tt_amountTotalIncome, 0.5) AS median_income,
  ROUND(
    SUM(CASE WHEN Contingent_Approved = 1
              AND policy_test_group IN {{POLICY_GROUPS}}
         THEN 1 ELSE 0 END) * 100.0 /
    NULLIF(SUM(CASE WHEN policy_test_group IN {{POLICY_GROUPS}} THEN 1 ELSE 0 END), 0)
  , 2) AS contingent_approval_rate,
  SUM(CASE WHEN vantageScore3 >= 780 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS super_prime_share
FROM {{BASE_TABLE}}
WHERE app_number2 = 1
  AND la_status != 'OFFER_PENDING'
  AND app_date <= CAST('{{CUTOFF_DATE}}' AS DATE)
GROUP BY app_month
ORDER BY app_month
```

## Validation Query A — Historical Consistency

Run Query 1 and Query 2 above, then compare each historical month's row against the corresponding row from the **previous month's saved Google Sheet**. Any non-zero delta in a historical month is a red flag.

## Validation Query B — Cross-Reference

```sql
SELECT
  last_day(application_submit_date) AS app_month,
  COUNT(*) AS apps,
  SUM(funded_amount) AS total_funded
FROM aig.cg_risk_vendor_rule_data
WHERE (is_test_app = 0 OR is_test_app IS NULL)
  AND application_status != 'OFFER_PENDING'
  AND app_rank_desc = 1
  AND application_submit_date >= '2025-09-18'
  AND application_submit_date <= CAST('{{CUTOFF_DATE}}' AS DATE)
GROUP BY last_day(application_submit_date)
ORDER BY app_month
```

Compare `apps` per month against Query 1 `total_apps`. Tolerance: ±10%.

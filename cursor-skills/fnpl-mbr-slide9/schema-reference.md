# Schema Reference — Known Column Mappings & Table Quirks

> This file caches column name discoveries and cross-table differences found during previous runs.
> The agent should consult this BEFORE running DESCRIBE or attempting column lookups to avoid trial-and-error delays.

---

## Base Table (`sandbox_risk_7216.fnpl_base_alpha_ga*`)

| Expected Column | Actual Column Name | Notes |
|---|---|---|
| `annualIncome` | `tt_amountTotalIncome` | Income field; use `CAST(tt_amountTotalIncome AS DOUBLE)` for median calculations |
| `vantageScore3` | `vantageScore3` | Exists as-is; CAST to DOUBLE for AVG |
| `funded_loan` | `funded_loan` | 1 = funded, filter for Slides 10–13 |
| `application_id` | `application_id` | Join key to `loan_origination.loanuuid` |
| `app_number2` | `app_number2` | Must = 1 for Slide 9 |
| `la_status` | `la_status` | Filter: `!= 'OFFER_PENDING'` |
| `application_submit_date` | `application_submit_date` | Date filter for Slide 9 (`>= '2025-09-18'`) |
| `is_test_app` | `is_test_app` | Filter: `= 0 OR IS NULL` |
| `app_rank_desc` | `app_rank_desc` | Filter: `= 1` (deduplicate) |
| `mxsPrediction` | `mxsPrediction` | Risk score; may be NULL for some months → show "N/A" for Avg RS |
| `term` | `term` | Loan term in months (3, 6, 9); used for Slide 13 grouping |

## Loan Origination (`intuit_lending_loanprofiles_dwh.loan_origination`)

| Column | Notes |
|---|---|
| `loanuuid` | Join key to base table `application_id` |
| `originationDate` | Funded loan origination date; use `last_day(originationDate)` for monthly grouping |
| `originationAmount` | Funded dollar amount |
| `authId` | Join key to tax refund table |

## Loan Repayment (`intuit_lending_servicing_capital_dwh.loan_repayment_daily`)

| Column | Notes |
|---|---|
| `loanId` | Join key — **NOT `loan_id`** (camelCase, no underscore) |
| `asOfDate` | Snapshot date — **NOT `as_of_date`** (camelCase) |
| `daysPastDue` | DPD value — **NOT `max_dpd_as_of`** (different naming from AIG tables) |
| `outstandingBalance` | Balance for dollar-weighted DPD rates |

**Carry-through logic**: Use **`date_sub(CAST('{{CUTOFF_DATE}}' AS DATE), 3)`** as the as-of date (same as Slide 11 `asof_snap`; replaces ad hoc `current_date()-3`). If a loan has no row for that exact date, fall back to the most recent prior row using `ROW_NUMBER() ... ORDER BY asOfDate DESC`.

## AIG Reference Tables

### `aig.cg_risk_vendor_rule_data` (Slide 9 cross-ref)

| Column | Notes |
|---|---|
| `application_submit_date` | Exists — use for monthly grouping |
| `is_test_app` | Filter: `= 0 OR IS NULL` |
| `application_status` | Filter: `!= 'OFFER_PENDING'` |
| `app_rank_desc` | Filter: `= 1` |
| ~~`originationDate`~~ | **DOES NOT EXIST** in this table — only in `cg_risk_fnpl_loan_status` |

### `aig.cg_risk_fnpl_loan_status` (Slide 10 & 11 cross-ref)

| Column | Notes |
|---|---|
| `originationDate` | Exists here (not in vendor_rule_data); use `last_day(originationDate)` |
| `originationAmount` | Loan amount — use `CAST(...AS DOUBLE)` |
| `origination_date` | **Also exists** as a separate column (snake_case) — prefer `originationDate` (camelCase) for consistency with the join query |
| `intuitStatus` | Loan status values: `PAID_OFF`, `CHARGED_OFF`, `LATE_31_TO_60_DAYS`, `LATE_61_TO_90_DAYS`, `LATE_91_TO_119_DAYS`, etc. |
| `daysOnBooks` | Use `> 60` for 30DPD eligibility filter |

### Key Cross-Table Gotchas

1. **Column naming is inconsistent**: Repayment table uses camelCase (`loanId`, `asOfDate`, `daysPastDue`), AIG tables mix camelCase and snake_case, base table uses mostly snake_case.
2. **Slide 9 AIG validation** uses `cg_risk_vendor_rule_data` which has application-level data only. No origination columns.
3. **Slide 10 AIG validation** uses `cg_risk_fnpl_loan_status` which has funded-loan-level data with `originationDate`.
4. **The three mandatory Slide 9 base filters** that must ALWAYS be applied: `is_test_app = 0 OR IS NULL`, `application_status != 'OFFER_PENDING'`, `app_rank_desc = 1`.
5. **7DPD+ is NOT validated** against AIG because `LATE_1_TO_30_DAYS` in AIG includes DPD 1–6 (too broad).

## Tax Refund Table (`tax_dm.agg_auth_id_accepted_refund`)

| Column | Notes |
|---|---|
| `auth_id` | Join key to `loan_origination.authId` |
| `state_refund_amount` | Used to derive `% Had a State Refund` |

# Slide 11 — Monthly Performance table (canonical)

**Status: MANDATORY for all FNPL MBR runs using this skill.**  
Agents MUST build `{{TABLE_ROWS}}` to match this document. The SQL in [queries-slide11.md](queries-slide11.md) may return additional fields; **only the metrics below appear in the HTML table** unless the user explicitly requests an expanded row set.

## Template placeholders

| Placeholder | Required |
|-------------|----------|
| `{{TABLE_SUBTITLE}}` | **Yes** — one short paragraph above the table (inside `.table-subtitle`). Explain funded-loan performance by origination month, what “Total” means, and that `—` = not applicable. |
| `{{TABLE_ROWS}}` | **Yes** — rows below, including section sub-headers. |
| Others | Per [SKILL.md](SKILL.md) template registry (`template-slide11.html`). |

## Typography and layout (match Slide 10)

Table **font sizes, cell padding, and column widths** for `#slide11 .tbl` MUST mirror **`#slide10 .tbl`** in [template-slide10.html](template-slide10.html):

- Table `font-size: 10px`; first column metric labels `8.5px`; body cells `10px`; header `9px`; total column `9px`; `col.lc` **82px**, `col.tc` **50px**; thead/tbody padding rules identical to Slide 10.

Do not “invent” new table CSS — only populate placeholders in `template-slide11.html`.

## Section sub-headers

Insert one full-width row **before each group** using:

```html
<tr class="section-row"><td colspan="10">SECTION TITLE</td></tr>
```

(`10` = Metrics + 8 month columns + Total.)

Use these **exact** section titles:

| Order | Section title |
|-------|----------------|
| 1 | `Volume` |
| 2 | `7DPD+ Delinquency` |
| 3 | `30DPD+ Delinquency` |
| 4 | `Roll to charge-off` |
| 5 | `Charge-off` |
| 6 | `Target loss` |
| 7 | `Payoff` |

## Data rows (exact order and labels)

After **Volume**:

| Label | Typical SQL / field | Format |
|-------|---------------------|--------|
| `# Loans` | `n_loans` | Comma integer |
| `$ Loans` | `funded_amount` | `$X.XM` |

After **7DPD+ Delinquency**:

| Label | Field | Format |
|-------|-------|--------|
| `# 7DPD+ Rate` | `7dpd_plus_rate` | `X.X%` or `—` |
| `$ 7DPD+ Rate` | `dollar_7dpd_plus_rate` | `X.X%` or `—` |

After **30DPD+ Delinquency**:

| Label | Field | Format |
|-------|-------|--------|
| `# 30DPD+ Rate` | `30dpd_plus_rate` | `X.X%` or `—` |
| `$ 30DPD+ Rate` | `dollar_30dpd_plus_rate` | `X.X%` or `—` |

After **Roll to charge-off** — **labels MUST match exactly** (do not use “Roll Rate 30→CO” or “from 30 to charge off” in the deck):

| Label | Field | Format |
|-------|-------|--------|
| `# Roll rate -> 30D to CO` | `rollrate_30_to_co` | `X.X%` or `—` |
| `$ Roll rate -> 30D to CO` | `dollar_rollrate_30_to_co` | `X.X%` or `—` |

After **Charge-off**:

| Label | Field | Format |
|-------|-------|--------|
| `# Charge off rate` | `charged_off_asof_rate` | `X.X%` or `—` |
| `$ Charge off rate` | `dollar_charged_off_asof_rate` | `X.X%` or `—` |

After **Target loss**:

| Label | Field | Format |
|-------|-------|--------|
| `# Target Loss Rate` | — | Always `—` until defined |
| `$ Target Loss Rate` | — | Always `—` until defined |

After **Payoff**:

| Label | Field | Format |
|-------|-------|--------|
| `% Paid Off` | `paid_off_rate_asof` | `X.X%` |

## Omitted from default deck (do not add unless user asks)

Do **not** include rows for: 1DPD+, 60DPD+, 90DPD+ — the default MBR table is the reduced set above.

## Row styling (unchanged)

- Latest month column: class `hi` on cells where applicable.
- Total column: `total-col`.
- Missing / N/A: class `d` and em dash `—`.
- Dec-25: `—` for paused month.

## Related files

- [template-slide11.html](template-slide11.html) — structure and CSS (including `.section-row`, `.table-subtitle`).
- [template-slide10.html](template-slide10.html) — reference for table typography parity.

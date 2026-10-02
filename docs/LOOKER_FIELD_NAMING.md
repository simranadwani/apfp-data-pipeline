# Looker Studio calculated-field naming (v0.1.11)

The field name says what the field is. One prefix per kind, then plain words, `snake_case`.

| Prefix | Meaning | Example |
|---|---|---|
| `distinct_` | `COUNT_DISTINCT(...)` | `distinct_grantees` |
| `sum_` | `SUM(...)` | `sum_approved` |
| `max_` | `MAX(...)` (one value per organisation / year) | `max_annual_budget` |
| `avg_` | average or per-unit ratio of sums | `avg_cost_per_beneficiary` |
| `pct_` | percentage (stored as a fraction, formatted as %) | `pct_active_grants_on_track` |
| `inr_` | rupee amount as text, Indian digit grouping (unchanged) | `inr_approved` |
| `txt_` | other text built in Looker | `txt_due_date` |
| `ord_` | helper used only to sort a text dimension | `ord_due_window` |
| `link_` | hyperlink | `link_grantee_360` |

Rules for any new field: pick the prefix from the formula (not from where it is used); add the unit when it is not rupees (`_lakh`); a field that appears in the all-years data source keeps the same name there. Pipeline columns (the Google Sheet headers, e.g. `financial_year`) are never renamed in Looker Studio.

## Old name to new name

**fct1_grant_portfolio  (and its "all years" copy where the field exists there)**

| Old name | New name |
|---|---|
| `m_active_orgs` | `distinct_active_orgs` |
| `m_active_grants` | `distinct_active_grants` |
| `m_on_track_grants` | `distinct_on_track_grants` |
| `m_off_track_grants` | `distinct_off_track_grants` |
| `m_pct_on_track` | `pct_active_grants_on_track` |
| `m_grantees` | `distinct_grantees` |
| `m_beneficiaries` | `sum_beneficiaries` |
| `m_funded_grantees` | `distinct_funded_grantees` |
| `m_approved` | `sum_approved` |
| `m_proposed` | `sum_proposed` |
| `m_annual_budget` | `max_annual_budget` |
| `m_cost_per_beneficiary` | `avg_cost_per_beneficiary` |
| `m_pending` | `distinct_pending_grants` |
| `m_overdue` | `distinct_overdue_grants` |
| `m_due30` | `distinct_due_30_days_grants` |
| `m_proposed_renewal` | `sum_proposed_renewal` |
| `m_pct_achieved` | `pct_outcomes_achieved` |
| `m_disbursed_if_different` | `sum_disbursed_lakh_if_different` |
| `m_approved_lakh` | `sum_approved_lakh` |
| `m_disbursed_lakh` | `sum_disbursed_lakh` |
| `m_committed_lakh` | `sum_committed_lakh` |
| `due_date_text` | `txt_due_date` |
| `annual_report_link_text` | `link_annual_report` |
| `link_360` | `link_grantee_360` |
| `grant_period_text` | `txt_grant_period` |
| `grant_status_line` | `txt_grant_status_line` |
| `sub_category_line` | `txt_sub_category_line` |
| `funding_range_order` | `ord_funding_range` |
| `due_window_order` | `ord_due_window` |

**fct2_outcome_progress**

| Old name | New name |
|---|---|
| `m_outcomes_latest` | `distinct_latest_outcomes` |
| `m_outcomes_latest_on_track` | `distinct_latest_outcomes_on_track` |
| `m_pct_outcomes_on_track` | `pct_outcomes_on_track` |
| `status_q1` | `txt_status_q1` |
| `status_q2` | `txt_status_q2` |
| `status_q3` | `txt_status_q3` |
| `status_q4` | `txt_status_q4` |
| `m_annual_pct` | `pct_annual_achievement` |

**fct3_support_activity**

| Old name | New name |
|---|---|
| `m_open_needs` | `distinct_open_needs` |
| `m_needs` | `distinct_needs` |
| `m_responses` | `distinct_responses` |

**fct4_budget_year**

| Old name | New name |
|---|---|
| `n_available` | `sum_available_budget` |
| `n_dividends` | `sum_dividends` |
| `n_carry_forward` | `sum_carry_forward` |
| `n_committed_current` | `sum_committed_current_fy` |
| `n_next_q1` | `sum_committed_next_fy_q1` |
| `n_committed_total` | `sum_committed_total` |
| `n_disbursed` | `sum_disbursed_funding` |
| `n_unallocated` | `sum_unallocated_balance` |

**fct5_maturity_rag**

| Old name | New name |
|---|---|
| `m_assessed` | `distinct_assessed_grantees` |
| `aspect_order` | `ord_aspect` |

## Deleted (not used by any chart)

`m_committed`, `m_disbursed` (charts use the `_lakh` fields), `m_apfp_share`, `m_team_size`, `m_attrition`, `m_foreign_share`, `core_policies_text` (4.02 now reads `fct6_grantee_annual_info`), `fy_label` (the pipeline's `financial_year` is already `FY 26-27`), `recommendation_copy` (3.06 is single-series), `m_support_grantees`. Any other field that no chart, filter, sort, conditional format, control or other formula uses is also deleted. Formulas of everything are kept in `docs/looker_calculated_fields.txt`.

## Financial year

One format everywhere: `FY 26-27`. The pipeline writes it (`financial_year`, `previous_financial_year`); the dashboard shows the value as it is. All-years charts use `financial_year_all`.

# Looker Studio calculated fields: naming and the "one metric per meaning" rule (v0.1.12)

## The rule

1. **One metric per meaning.** A count of grantees is `distinct_grantees` everywhere, in every data source that has `organization_id`. A count of grants is `distinct_grants`; a count of support requests is `distinct_needs`.
2. **Context is a chart-level filter, not a new field.** "Active grantees" = `distinct_grantees` + filter `is_active_grant`. "Pending decisions" = `distinct_grants` + filter `is_pending_decision`. "Open support needs" = `distinct_needs` + filter `is_open_support_need`.
3. **Plain sums and maxima need no calculated field.** Use the column with the built-in Sum or Max aggregation and rename it in the chart.
4. **A calculated field is only for:** ratios (`pct_*`, `avg_*`), text formatting that needs an aggregate (`inr_*`), links, and formulas with several terms (`sum_*_lakh`). A value that is derived per row (display text, a sort helper) is a **pipeline column**, not a Looker field.
5. Before creating a field, look at the list below. Same meaning means same field.

## Syntax in this report

The `is_*` flags are text in Looker Studio: compare them as `is_active_grant = "TRUE"` (chart filters: *equals TRUE*). `ROUND` takes two arguments: `ROUND(x, 0)`. `docs/looker_calculated_fields.txt` already uses both.

## Prefixes

| Prefix | Meaning | Example |
|---|---|---|
| `distinct_` | `COUNT_DISTINCT(...)` | `distinct_grantees` |
| `sum_` | `SUM(...)` with a unit conversion | `sum_committed_lakh` |
| `avg_` | per-unit ratio of sums | `avg_cost_per_beneficiary` |
| `pct_` | percentage (a fraction shown as %) | `pct_active_grants_on_track` |
| `inr_` | rupee amount as text, Indian digit grouping | `inr_approved` |
| `txt_` | other text | `txt_due_date` |
| `ord_` | sort helper for a text dimension (only when the pipeline has no order column) | none left |
| `link_` | hyperlink | `link_grantee_360` |

Pipeline columns (Google Sheet headers, for example `financial_year`) are never renamed in Looker Studio.

## The complete list of calculated fields

**fct1_grant_portfolio** (the "all years" copy gets only what its charts use: `distinct_grantees`, `sum_committed_lakh`, `sum_disbursed_lakh`, `sum_approved_lakh`, `inr_cost_per_beneficiary` and `avg_cost_per_beneficiary`)

| Field | What it is | Used by |
|---|---|---|
| `distinct_grantees` | COUNT_DISTINCT(organization_id) | 1.01, 1.07, 1.08, 1.10, 1.16, 2.07 (+ filters) |
| `distinct_grants` | COUNT_DISTINCT(grant_id) | 1.03, 1.05, 1.06, 3.01, 3.02, 3.03, 3.05, 3.06 (+ filters) |
| `pct_active_grants_on_track` | on-track active grants / active grants | 1.02 |
| `pct_outcomes_achieved` | achieved outcomes / total outcomes | 3.07 |
| `avg_cost_per_beneficiary` | approved amount / beneficiaries | feeds `inr_cost_per_beneficiary` |
| `sum_approved_lakh`, `sum_committed_lakh`, `sum_disbursed_lakh` | amounts in rupee lakh | 2.05, 2.06, 2.08, 4.03 |
| `inr_annual_budget`, `inr_approved`, `inr_cost_per_beneficiary`, `inr_proposed` | rupee text | 1.11, 3.04 (`inr_proposed` + filters), 3.07, 4.01, 4.05, 4.08 |
| `txt_due_date` | date as `31 Mar 2027` text | 3.07, 4.08 |
| `link_annual_report`, `link_grantee_360` | hyperlinks | 4.08, 3.07 |
| (pipeline columns, no Looker field) `grant_period`, `grant_status_type_amount`, `sub_category_line`, `due_window_order`, `funding_range_order` | display text and sort helpers written by the pipeline | 4.01, 3.05, 2.07 |

**fct2_outcome_progress:** `pct_outcomes_on_track` (1.12), `txt_status_q1` to `txt_status_q4` (4.06).
**fct3_support_activity:** `distinct_needs` (1.04, 1.14, 1.15 + filters).
**fct4_budget_year:** `inr_available`, `inr_dividends`, `inr_carry_forward`, `inr_committed_total`, `inr_committed_current`, `inr_next_q1`, `inr_disbursed`, `inr_unallocated` (tiles 2.01 to 2.04 and 2.09 to 2.12), each with `SUM(column)` written inside the formula.
**fct5_maturity_rag:** `distinct_grantees` (1.13). Sort helpers are pipeline columns now (`aspect_order`, `status_order`).
**fct6_grantee_annual_info:** none.

## Chart and tile map (metric + chart-level filters)

| Chart | Metric | Chart-level filters |
|---|---|---|
| 1.01 Grantees | `distinct_grantees` | `is_active_grant` is TRUE |
| 1.02 On track | `pct_active_grants_on_track` | none |
| 1.03 Off-track | `distinct_grants` | `is_off_track_active_grant` is TRUE |
| 1.04 Open support needs | `distinct_needs` (fct3) | `is_open_support_need` is TRUE |
| 1.05, 1.06 | `distinct_grants` | `is_active_grant` is TRUE |
| 1.07 | `distinct_grantees` | `is_active_grant` is TRUE |
| 1.08 | `distinct_grantees` | `thematic_area` = Education |
| 1.09, 1.11, 4.05 reach | built-in Sum of `primary_beneficiary_count` | none |
| 1.10 | `distinct_grantees` | none |
| 1.13 | `distinct_grantees` (fct5) | `status` in Red, Amber, Green |
| 1.14 | `distinct_needs` | none |
| 1.15 | `distinct_needs` | `response_category` is not empty |
| 1.16 | `distinct_grantees` (all years) | `is_active_grant` is TRUE |
| 2.05, 2.06, 2.08 | `sum_committed_lakh`, `sum_disbursed_lakh` | none |
| 2.07 | `distinct_grantees` | `is_funded_grantee` is TRUE, `funding_range` is not empty |
| 3.01 | `distinct_grants` | `is_pending_decision` is TRUE |
| 3.02 | `distinct_grants` | `is_overdue_decision` is TRUE |
| 3.03 | `distinct_grants` | `is_due_within_30_days` is TRUE |
| 3.04 | `inr_proposed` | `is_pending_decision` is TRUE, `recommendation` = Renew |
| 3.05, 3.06 | `distinct_grants` | `is_pending_decision` is TRUE (3.05 also `recommendation` in Renew, Close) |
| 3.07 | `pct_outcomes_achieved`, `inr_proposed` | existing |
| 4.03 | `sum_approved_lakh`, `sum_disbursed_lakh` | none |
| 4.06 Annual | built-in Max of `annual_achievement_pct` (percent) | none |

## Deleted (replaced by the rule above)

v0.1.11: `m_committed`, `m_disbursed`, `m_apfp_share`, `m_team_size`, `m_attrition`, `m_foreign_share`, `core_policies_text`, `fy_label`, `recommendation_copy`, `m_support_grantees`.
v0.1.14 (moved into the pipeline as columns): `txt_grant_period`, `txt_grant_status_line`, `txt_sub_category_line`, `ord_due_window`, `ord_funding_range`.
v0.1.12: `distinct_active_orgs`, `distinct_active_grants`, `distinct_on_track_grants`, `distinct_off_track_grants`, `distinct_funded_grantees`, `distinct_pending_grants`, `distinct_overdue_grants`, `distinct_due_30_days_grants`, `sum_beneficiaries`, `sum_approved`, `sum_proposed`, `max_annual_budget`, `sum_proposed_renewal`, `sum_disbursed_lakh_if_different`, `distinct_latest_outcomes`, `distinct_latest_outcomes_on_track`, `pct_annual_achievement`, `txt_notes_last` (the pipeline column `latest_notes` does this), `distinct_open_needs`, `distinct_responses`, the eight fct4 `sum_*` helpers, `distinct_assessed_grantees`, `inr_proposed_renewal`, `ord_aspect`.

## Financial year

One format everywhere: `FY 26-27`. The pipeline writes it; the dashboard shows it as it is. All-years charts use `financial_year_all`.

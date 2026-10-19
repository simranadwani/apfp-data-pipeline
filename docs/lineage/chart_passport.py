"""
Chart passport: for every dashboard chart or tile, what it shows, the filter applied in plain words, and the final-table
columns it reads ("table.column"). Source tabs are worked out from these columns through lineage_model.FINAL, so the
passport can never name a source tab that the columns do not come from.
export_catalog.py turns this into LineageData.js (read by the Data_Dictionary and Chart_Passport tabs).
"""
PAGES = {'1': 'Portfolio', '2': 'Funding', '3': 'Decision Queue', '4': 'Grantee 360'}
F1, F2, F3, F4, F5, F6 = ('fct1_grant_portfolio', 'fct2_outcome_progress', 'fct3_support_activity',
                          'fct4_budget_year', 'fct5_maturity_rag', 'fct6_grantee_annual_info')


def c(table, *cols): return [f'{table}.{x}' for x in cols]


# id: (final table, what the chart shows, filter in plain words, columns it reads)
CHARTS = {
    '1.01': (F1, 'Number of different organisations that have an active grant', 'Active grants only', c(F1, 'organization_id', 'is_active_grant')),
    '1.02': (F1, 'Share of active grants that are on track', 'Active grants', c(F1, 'grant_id', 'is_active_grant', 'is_on_track_active_grant')),
    '1.03': (F1, 'Number of active grants that are off track', 'Active grants that are off track', c(F1, 'grant_id', 'is_off_track_active_grant')),
    '1.04': (F3, 'Number of support requests that are still open', 'Open requests only', c(F3, 'support_id', 'is_open_support_need')),
    '1.05': (F1, 'Active grants by how many years the organisation has been funded', 'Active grants only', c(F1, 'grant_id', 'is_active_grant', 'duration_of_support_bucket')),
    '1.06': (F1, 'Active grants by grant type', 'Active grants only', c(F1, 'grant_id', 'is_active_grant', 'grant_type')),
    '1.07': (F1, 'Organisations with an active grant, by thematic area', 'Active grants only', c(F1, 'organization_id', 'is_active_grant', 'thematic_area')),
    '1.08': (F1, 'Education organisations by sub-category', 'Thematic area is Education', c(F1, 'organization_id', 'thematic_area', 'education_sub_category')),
    '1.09': (F1, 'Beneficiaries reached, by beneficiary group', 'None (page filters apply)', c(F1, 'primary_beneficiary_count', 'primary_beneficiary_group')),
    '1.10': (F1, 'Organisations by proximity to the children they serve', 'None (page filters apply)', c(F1, 'organization_id', 'proximity_to_children_beneficiary')),
    '1.11': (F1, 'One row per organisation: budget, approved amount, beneficiaries, cost per beneficiary and the three maturity ratings', 'None (page filters apply)',
             c(F1, 'organisation', 'annual_budget', 'approved_amount', 'primary_beneficiary_count', 'cost_per_beneficiary', 'clarity_status', 'capacity_status', 'compliance_status')),
    '1.12': (F2, 'Share of outcomes that are on track, and status by quarter', 'Latest update of each outcome', c(F2, 'outcome_id', 'quarter', 'status', 'is_latest_update')),
    '1.13': (F5, 'Share of organisations rated Red, Amber or Green for each maturity aspect', 'Rated indicators only', c(F5, 'organization_id', 'aspect', 'status', 'aspect_order', 'status_order')),
    '1.14': (F3, 'Support requests raised, open and closed', 'None (page filters apply)', c(F3, 'support_id', 'support_status')),
    '1.15': (F3, 'Support requests by the support APFP provided', 'Requests with a support provided only', c(F3, 'support_id', 'response_category')),
    '1.16': (F1, 'Organisations with an active grant, year on year', 'Active grants only; all financial years', c(F1, 'organization_id', 'is_active_grant', 'financial_year')),
    '2.01': (F4, 'Budget available in the year: dividends plus carry forward', 'Selected financial year', c(F4, 'available_budget')),
    '2.02': (F4, 'Funding committed: this year plus next year Q1', 'Selected financial year', c(F4, 'annual_committed_funding', 'next_year_q1_committed_funding')),
    '2.03': (F4, 'Funding actually paid out in the year', 'Selected financial year', c(F4, 'annual_disbursed_funding')),
    '2.04': (F4, 'Budget still free to commit', 'Selected financial year', c(F4, 'unallocated_balance')),
    '2.05': (F1, 'Committed and disbursed funding by thematic area', 'None (page filters apply)', c(F1, 'thematic_area', 'committed_amount', 'disbursed_amount')),
    '2.06': (F1, 'Committed and disbursed funding by grant type', 'None (page filters apply)', c(F1, 'grant_type', 'committed_amount', 'disbursed_amount')),
    '2.07': (F1, 'Organisations by the total funding they received in the year', 'Funded organisations only', c(F1, 'organization_id', 'is_funded_grantee', 'funding_range', 'funding_range_order')),
    '2.08': (F1, 'Committed and disbursed funding year on year', 'All financial years', c(F1, 'financial_year', 'committed_amount', 'disbursed_amount')),
    '2.09': (F4, 'Dividend income of the year', 'Selected financial year', c(F4, 'dividend_income')),
    '2.10': (F4, 'Budget carried forward from the previous year', 'Selected financial year', c(F4, 'prior_year_carry_forward')),
    '2.11': (F4, 'Funding committed for the current year', 'Selected financial year', c(F4, 'annual_committed_funding')),
    '2.12': (F4, 'Funding reserved for next year Q1', 'Selected financial year', c(F4, 'next_year_q1_committed_funding')),
    '3.01': (F1, 'Number of grants waiting for a decision', 'Pending decisions only', c(F1, 'grant_id', 'is_pending_decision')),
    '3.02': (F1, 'Pending decisions already past their due date', 'Pending and overdue', c(F1, 'grant_id', 'is_overdue_decision')),
    '3.03': (F1, 'Pending decisions due within 30 days', 'Pending and due within 30 days', c(F1, 'grant_id', 'is_due_within_30_days')),
    '3.04': (F1, 'Total proposed amount of pending renewals', 'Pending decisions with recommendation Renew', c(F1, 'proposed_amount', 'is_pending_decision', 'recommendation')),
    '3.05': (F1, 'Pending Renew and Close decisions by how soon they are due', 'Pending; recommendation Renew or Close', c(F1, 'grant_id', 'is_pending_decision', 'recommendation', 'due_window', 'due_window_order')),
    '3.06': (F1, 'Pending decisions by recommendation', 'Pending decisions only', c(F1, 'grant_id', 'is_pending_decision', 'recommendation')),
    '3.07': (F1, 'List of decisions: organisation, recommendation, due date, proposed amount, reason, outcomes achieved, report link',
             'Pending decisions', c(F1, 'organisation', 'recommendation', 'decision_due_date', 'proposed_amount', 'reason_for_recommendation', 'achieved_outcomes_count', 'total_outcomes_count', 'annual_report_link')),
    '4.01': (F1, 'Profile of the selected organisation: mission, thematic area, sub-category, grant period, status, type and amount', 'Selected organisation',
             c(F1, 'organisation', 'mission', 'thematic_area', 'sub_category_line', 'grant_period', 'grant_status_type_amount')),
    '4.02': (F6, 'Annual information of the selected organisation: this year next to the year before', 'Selected organisation and financial year',
             c(F6, 'financial_year', 'previous_financial_year', 'metric', 'metric_order', 'current_value', 'previous_value')),
    '4.03': (F1, 'Approved and disbursed funding by year for the selected organisation', 'Selected organisation; all financial years', c(F1, 'financial_year', 'approved_amount', 'disbursed_amount')),
    '4.04': (F5, 'Maturity rating of each indicator for the selected organisation', 'Selected organisation', c(F5, 'aspect_display', 'indicator', 'status')),
    '4.05': (F1, 'Beneficiaries reached and cost per beneficiary by year', 'Selected organisation; all financial years', c(F1, 'financial_year', 'primary_beneficiary_count', 'cost_per_beneficiary')),
    '4.06': (F2, 'Outcomes with status by quarter, annual achievement and latest notes', 'Selected organisation', c(F2, 'outcome_indicator', 'quarter', 'status', 'annual_achievement_pct', 'latest_notes')),
    '4.07': (F3, 'Support requests of the selected organisation and the support provided', 'Selected organisation',
             c(F3, 'quarter', 'support_category', 'request_description', 'support_status', 'response_category', 'response_notes')),
    '4.08': (F1, 'Latest decision for the selected organisation', 'Selected organisation', c(F1, 'recommendation', 'reason_for_recommendation', 'decision_due_date', 'proposed_amount', 'annual_report_link')),
}

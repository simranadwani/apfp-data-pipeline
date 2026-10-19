"""
Hand-editable lineage model for the APFP pipeline (column level).

This file is the single place where "which column comes from which" and the plain-language rule are written.
build_drawio.py turns it, together with code_columns.json (the real column lists exported from the scripts),
into the draw.io diagram. tests/lineage_check.js checks that nothing in the code is missing from the diagram.

Edge categories:  copy  = taken as entered            join = looked up from another table by a key
                  calc  = calculated                  const = fixed value        run = date of the pipeline run
                  blank = column kept empty on purpose (placeholder)
Upstream names are "table.column".
"""

# ---------------------------------------------------------------- plain-language table information
TABLE_INFO = {
    # source tab -> (plain name, what it holds)
    '8. Grant Registry': ('Grant register', 'One row per grant: organisation, amount, dates, status, team and budget'),
    '9. Organisation Registry': ('Organisation register', 'One row per organisation: mission, policies, FCRA registration'),
    '4. Decision Tracker': ('Decision tracker', 'One row per grant under review: recommendation, due date, proposed amount'),
    '2. Outcome Progress': ('Outcome progress', 'One row per grant and outcome: target and Q1 to Q4 progress'),
    '7. Organisation Maturity': ('Organisation maturity', 'One row per grant and maturity indicator: Red, Amber or Green'),
    '3. Support': ('Support requests', 'One row per support request raised by a grantee'),
    '6. Committed & Spent Tracker': ('Committed and spent tracker', 'One row per payment tranche: planned and actual amounts'),
    '5. Dividends': ('Dividends', 'One row per financial year: dividend income'),
    # staging tables
    'stg_grants': ('Grants (cleaned)', 'Cleaned copy of the grant register'),
    'stg_organisations': ('Organisations (cleaned)', 'Cleaned copy of the organisation register'),
    'stg_decisions': ('Decisions (cleaned)', 'Cleaned copy of the decision tracker'),
    'stg_outcome_progress': ('Outcome progress (cleaned)', 'Cleaned copy of outcome progress; quarters still side by side'),
    'stg_maturity': ('Maturity (cleaned)', 'Cleaned copy of organisation maturity'),
    'stg_support': ('Support requests (cleaned)', 'Cleaned copy of support requests'),
    'stg_disbursements': ('Payments (cleaned)', 'Cleaned copy of the committed and spent tracker'),
    'stg_dividends': ('Dividends (cleaned)', 'Cleaned copy of dividends'),
    # final tables
    'fct1_grant_portfolio': ('Grant portfolio', 'One row per grant: everything about a grant, its organisation, funding, decision and maturity'),
    'fct2_outcome_progress': ('Outcome progress by quarter', 'One row per grant, outcome and reported quarter'),
    'fct3_support_activity': ('Support activity', 'One row per support request, with the response provided'),
    'fct4_budget_year': ('Budget by year', 'One row per financial year: dividends, commitments, payments, balance'),
    'fct5_maturity_rag': ('Maturity ratings', 'One row per grant, maturity aspect and indicator'),
    'fct6_grantee_annual_info': ('Annual information, selected and previous year', 'One row per grant and measure; this year and last year side by side'),
}

# charts each final table feeds (chart id + short name)
FEEDS = {
    'fct1_grant_portfolio': ['1.01 Grantees', '1.02 On track', '1.03 Off-track', '1.05 Duration of support', '1.06 Grant type', '1.07 Thematic area',
                             '1.08 Education sub-categories', '1.09 Beneficiaries reached', '1.10 Beneficiary type', '1.11 Comparative metrics',
                             '1.16 Year on year', '2.05 Funding by theme', '2.06 Funding by grant type', '2.07 Funding range', '2.08 Funding year on year',
                             '3.01 to 3.04 Decision tiles', '3.05 Due window', '3.06 Recommendations', '3.07 Decision list',
                             '4.01 Profile', '4.03 Funding history', '4.05 Beneficiaries', '4.08 Latest decision'],
    'fct2_outcome_progress': ['1.12 Quarterly outcome status', '4.06 Outcome status table'],
    'fct3_support_activity': ['1.04 Open support needs', '1.14 Support needs raised', '1.15 Support provided', '4.07 Support requests'],
    'fct4_budget_year': ['2.01 Available budget', '2.02 Committed funding', '2.03 Disbursed funding', '2.04 Unallocated balance',
                         '2.09 Dividends', '2.10 Carry forward', '2.11 Current year', '2.12 Next year Q1'],
    'fct5_maturity_rag': ['1.13 Maturity level', '4.04 Maturity assessment'],
    'fct6_grantee_annual_info': ['4.02 Annual information'],
}

# ---------------------------------------------------------------- final columns: (column, category, upstream list, plain rule)
G, O, D, OP, M, S, DV, DS = ('stg_grants', 'stg_organisations', 'stg_decisions', 'stg_outcome_progress', 'stg_maturity',
                             'stg_support', 'stg_dividends', 'stg_disbursements')


def g(c): return f'stg_grants.{c}'
def o(c): return f'stg_organisations.{c}'
def d(c): return f'stg_decisions.{c}'
def op(c): return f'stg_outcome_progress.{c}'
def m(c): return f'stg_maturity.{c}'
def s(c): return f'stg_support.{c}'
def dv(c): return f'stg_dividends.{c}'
def ds(c): return f'stg_disbursements.{c}'
def f1(c): return f'fct1_grant_portfolio.{c}'


QSTATUS = [op(f'q{i}_status') for i in range(1, 5)]
QPROG = [op(f'q{i}_progress') for i in range(1, 5)]
QNOTES = [op(f'q{i}_notes') for i in range(1, 5)]
QEVID = [op(f'q{i}_evidence_link') for i in range(1, 5)]
POLICIES = [o('has_code_of_conduct_policy'), o('has_posh_policy'), o('has_child_protection_policy'), o('has_data_protection_policy')]

FINAL = {
    'fct1_grant_portfolio': [
        ('financial_year', 'copy', [g('financial_year')], 'Copied, in the form FY 26-27'),
        ('grant_id', 'copy', [g('grant_id')], 'Copied. Unique for every row'),
        ('organization_id', 'copy', [g('organization_id')], 'Copied'),
        ('organisation', 'copy', [g('organisation')], 'Copied'),
        ('mission', 'join', [o('mission_statement')], 'Looked up from the organisation register by organisation ID'),
        ('thematic_area', 'copy', [g('thematic_area')], 'Copied'),
        ('education_sub_category', 'copy', [g('thematic_sub_area')], 'Copied (NA for non-education grants)'),
        ('proximity_to_children_beneficiary', 'copy', [g('proximity_to_children_beneficiary')], 'Copied'),
        ('grant_status', 'copy', [g('grant_status')], 'Copied: Active, Complete or Discontinued'),
        ('grant_type', 'copy', [g('grant_type')], 'Copied'),
        ('grant_performance_status', 'calc', QSTATUS, 'Latest quarter with a status: Off Track if any outcome is Off Track, else On Track'),
        ('grant_start_date', 'copy', [g('grant_start_date')], 'Copied'),
        ('grant_end_date', 'copy', [g('grant_end_date')], 'Copied'),
        ('funding_year', 'calc', [g('organization_id'), g('financial_year')], 'Year 1, Year 2 ...: how many years this organisation has been funded up to this year'),
        ('duration_of_support_bucket', 'calc', [g('organization_id'), g('financial_year')], 'Funding year grouped: Year 1, Years 2-5, Years 6-10, Years 11+'),
        ('primary_beneficiary_group', 'copy', [g('primary_beneficiary_group')], 'Copied'),
        ('primary_beneficiary_count', 'copy', [g('primary_beneficiary_count')], 'Copied'),
        ('clarity_status', 'calc', [m('aspect'), m('status')], 'Worst rating (Red, then Amber, then Green) across the Clarity indicators'),
        ('capacity_status', 'calc', [m('aspect'), m('status')], 'Worst rating across the Capacity indicators'),
        ('compliance_status', 'calc', [m('aspect'), m('status')], 'Worst rating across the Compliance indicators'),
        ('fcra_registration', 'join', [o('fcra_registration_status')], 'Looked up from the organisation register'),
        ('has_completed_program_lifecycle', 'calc', [g('grant_status')], 'True when the grant is Complete'),
        ('annual_budget', 'copy', [g('annual_budget')], 'Copied'),
        ('team_size', 'copy', [g('team_size')], 'Copied'),
        ('attrition_rate', 'copy', [g('attrition_rate')], 'Copied, as a fraction (8% is 0.08)'),
        ('foreign_contribution_rate', 'copy', [g('foreign_contribution_rate')], 'Copied, as a fraction'),
        ('core_policies_met_count', 'calc', POLICIES, 'How many of the four core policies are answered Yes'),
        ('core_policies_total_count', 'const', [], 'Always 4'),
        ('approved_amount', 'copy', [g('approved_amount')], 'Copied'),
        ('committed_amount', 'calc', [ds('planned_amount'), ds('status')], 'Sum of planned amounts for the grant where status is Committed or Disbursed'),
        ('disbursed_amount', 'calc', [ds('actual_amount'), ds('status')], 'Sum of actual amounts for the grant where status is Disbursed'),
        ('funding_range', 'calc', [ds('actual_amount'), ds('status'), g('organization_id'), g('financial_year')], 'Band of the total disbursed to the organisation in the year'),
        ('decision_type', 'calc', [d('decision_type')], 'Closure when the recommendation is Close, otherwise Renewal'),
        ('decision_status', 'calc', [d('decision_status')], 'Pending, Decided or as entered'),
        ('due_window', 'calc', [d('decision_status'), d('decision_due_date')], 'For pending decisions: Overdue, 0-30, 31-60 or 61+ days from the run date'),
        ('recommendation', 'copy', [d('decision_type')], 'Copied: Renew, Modify, Defer or Close'),
        ('decision_due_date', 'copy', [d('decision_due_date')], 'Copied'),
        ('reason_for_recommendation', 'copy', [d('decision_rationale')], 'Copied'),
        ('grantee_360_link', 'blank', [], 'Kept empty (the dashboard builds its own link)'),
        ('proposed_amount', 'copy', [d('proposed_amount')], 'Copied'),
        ('total_outcomes_count', 'calc', [op('outcome_id')], 'Number of different outcomes for the grant'),
        ('achieved_outcomes_count', 'calc', [op('target_text'), op('final_actual_text')], 'Outcomes where the final actual reaches the target'),
        ('annual_report_link', 'join', [d('annual_report_link'), o('latest_annual_report_link')], 'Decision tracker link, else the organisation register link'),
        ('grant_period', 'calc', [g('grant_start_date'), g('grant_end_date')], 'Ready-to-show text: 01 Apr 2026 - 31 Mar 2027'),
        ('grant_status_type_amount', 'calc', [g('grant_status'), g('grant_type'), g('approved_amount')], 'Ready-to-show text: Active, Restricted, rupee amount'),
        ('cost_per_beneficiary', 'calc', [g('approved_amount'), g('primary_beneficiary_count')], 'Approved amount divided by beneficiaries'),
        ('is_active_grant', 'calc', [g('grant_status')], 'True when the grant is Active'),
        ('is_funded_grantee', 'calc', [ds('actual_amount'), ds('status')], 'True when something has been disbursed'),
        ('is_pending_decision', 'calc', [d('decision_status')], 'True when the decision is pending'),
        ('is_overdue_decision', 'calc', [d('decision_status'), d('decision_due_date')], 'Pending and the due date is before the run date'),
        ('is_due_within_30_days', 'calc', [d('decision_status'), d('decision_due_date')], 'Pending and due within 30 days of the run date'),
        ('is_on_track_active_grant', 'calc', [g('grant_status')] + QSTATUS, 'Active grant whose performance status is On Track'),
        ('is_off_track_active_grant', 'calc', [g('grant_status')] + QSTATUS, 'Active grant whose performance status is Off Track'),
        ('as_of_date', 'run', [], 'Date the pipeline was run'),
        ('sub_category_line', 'calc', [g('thematic_sub_area'), g('proximity_to_children_beneficiary')], 'Ready-to-show text: sub-category and intervention model'),
        ('due_window_order', 'calc', [d('decision_status'), d('decision_due_date')], 'Sort number for the due window (Overdue 1 ... 61+ days 4)'),
        ('funding_range_order', 'calc', [ds('actual_amount'), ds('status'), g('organization_id'), g('financial_year')], 'Sort number for the funding range (1 to 5)'),
    ],
    'fct2_outcome_progress': [
        ('financial_year', 'copy', [op('financial_year')], 'Copied, in the form FY 26-27'),
        ('grant_id', 'copy', [op('grant_id')], 'Copied'),
        ('organization_id', 'join', [g('organization_id')], 'Looked up from the grants by grant ID'),
        ('organisation', 'join', [g('organisation')], 'Looked up from the grants by grant ID'),
        ('thematic_area', 'join', [g('thematic_area')], 'Looked up from the grants'),
        ('grant_status', 'join', [g('grant_status')], 'Looked up from the grants'),
        ('outcome_id', 'copy', [op('outcome_id')], 'Copied'),
        ('outcome_indicator', 'copy', [op('outcome_indicator')], 'Copied'),
        ('quarter', 'calc', QPROG + QSTATUS + QNOTES, 'Q1 to Q4 turned into rows: one row per reported quarter'),
        ('status', 'calc', QSTATUS, 'The status of that quarter (On Track or Off Track)'),
        ('target_text', 'copy', [op('target_text')], 'Copied'),
        ('target_value', 'calc', [op('target_text')], 'The number found in the target text'),
        ('achieved_value', 'calc', QPROG, 'The number found in that quarter\'s progress text'),
        ('outcome_achievement_pct', 'calc', [op('target_text')] + QPROG, 'Quarter progress divided by the target'),
        ('final_actual_value', 'calc', [op('final_actual_text')], 'The number found in the final actual text'),
        ('annual_achievement_pct', 'calc', [op('target_text'), op('final_actual_text')], 'Final actual divided by the target'),
        ('outcome_notes', 'calc', QNOTES, 'That quarter\'s notes'),
        ('latest_notes', 'calc', QNOTES + QSTATUS + QPROG, 'Notes of the latest reported quarter'),
        ('evidence_link', 'calc', QEVID, 'That quarter\'s evidence link'),
        ('is_latest_update', 'calc', QSTATUS + QPROG + QNOTES, 'True for the latest reported quarter of the outcome'),
    ],
    'fct3_support_activity': [
        ('financial_year', 'copy', [s('financial_year')], 'Copied, in the form FY 26-27'),
        ('grant_id', 'copy', [s('grant_id')], 'Copied'),
        ('organization_id', 'join', [g('organization_id')], 'Looked up from the grants by grant ID'),
        ('organisation', 'join', [g('organisation')], 'Looked up from the grants'),
        ('thematic_area', 'join', [g('thematic_area')], 'Looked up from the grants'),
        ('grant_status', 'join', [g('grant_status')], 'Looked up from the grants'),
        ('support_id', 'calc', [s('grant_id'), s('quarter')], 'Made up: SUP, grant ID, quarter and a running number'),
        ('quarter', 'copy', [s('quarter')], 'Copied'),
        ('support_category', 'copy', [s('support_type')], 'Copied'),
        ('request_description', 'copy', [s('support_required')], 'Copied'),
        ('support_status', 'calc', [s('status')], 'In Progress is shown as Open; other values as entered'),
        ('is_open_support_need', 'calc', [s('status')], 'True when the status is Open'),
        ('response_notes', 'copy', [s('notes')], 'Copied'),
        ('response_date', 'blank', [], 'Kept empty (the source has no response date yet)'),
        ('evidence_link', 'copy', [s('evidence_link')], 'Copied'),
        ('response_category', 'copy', [s('support_provided')], 'Copied'),
    ],
    'fct4_budget_year': [
        ('financial_year', 'calc', [dv('financial_year'), ds('financial_year')], 'Every year that appears in dividends or payments'),
        ('dividend_income', 'calc', [dv('dividend_income'), dv('financial_year')], 'Dividends for the year'),
        ('prior_year_carry_forward', 'calc', [dv('dividend_income'), ds('planned_amount'), ds('status')], 'Last year\'s available budget minus last year\'s commitments'),
        ('available_budget', 'calc', [dv('dividend_income'), ds('planned_amount'), ds('status')], 'Dividends plus carry forward'),
        ('annual_committed_funding', 'calc', [ds('planned_amount'), ds('status'), ds('financial_year')], 'Planned amounts of the year where status is Committed or Disbursed'),
        ('next_year_q1_committed_funding', 'calc', [ds('planned_amount'), ds('status'), ds('quarter'), ds('financial_year')], 'Next year\'s Q1 commitments (reserved, not yet spent)'),
        ('annual_disbursed_funding', 'calc', [ds('actual_amount'), ds('status'), ds('financial_year')], 'Actual amounts of the year where status is Disbursed'),
        ('unallocated_balance', 'calc', [dv('dividend_income'), ds('planned_amount'), ds('status'), ds('quarter')], 'Available budget minus commitments minus next year\'s Q1 reserve'),
    ],
    'fct5_maturity_rag': [
        ('financial_year', 'copy', [m('financial_year')], 'Copied, in the form FY 26-27'),
        ('grant_id', 'copy', [m('grant_id')], 'Copied'),
        ('organization_id', 'join', [g('organization_id')], 'Looked up from the grants by grant ID'),
        ('organisation', 'join', [g('organisation')], 'Looked up from the grants'),
        ('thematic_area', 'join', [g('thematic_area')], 'Looked up from the grants'),
        ('grant_status', 'join', [g('grant_status')], 'Looked up from the grants'),
        ('aspect', 'copy', [m('aspect')], 'Copied: Clarity, Capacity or Compliance'),
        ('indicator', 'copy', [m('indicator')], 'Copied'),
        ('status', 'copy', [m('status')], 'Copied: Red, Amber or Green'),
        ('aspect_display', 'calc', [m('grant_id'), m('aspect')], 'The aspect on the first row of each block, empty after it'),
        ('aspect_order', 'calc', [m('aspect')], 'Sort number: Clarity 1, Capacity 2, Compliance 3'),
        ('status_order', 'calc', [m('status')], 'Sort number: Red 1, Amber 2, Green 3'),
    ],
    'fct6_grantee_annual_info': [
        ('financial_year', 'copy', [f1('financial_year')], 'Copied from the grant portfolio'),
        ('previous_financial_year', 'calc', [f1('financial_year')], 'The year before (FY 26-27 gives FY 25-26)'),
        ('grant_id', 'copy', [f1('grant_id')], 'Copied'),
        ('organization_id', 'copy', [f1('organization_id')], 'Copied'),
        ('organisation', 'copy', [f1('organisation')], 'Copied'),
        ('grant_status', 'copy', [f1('grant_status')], 'Copied'),
        ('metric_order', 'const', [], '1 to 8: position of the measure in the table'),
        ('metric', 'const', [], 'Eight fixed measures, for example Annual budget, Team size'),
        ('current_value', 'calc', [f1('financial_year'), f1('annual_budget'), f1('approved_amount'), f1('team_size'), f1('attrition_rate'),
                                   f1('core_policies_met_count'), f1('core_policies_total_count'), f1('fcra_registration'), f1('foreign_contribution_rate')],
         'The measure for this grant\'s year, ready to show'),
        ('previous_value', 'calc', [f1('financial_year'), f1('annual_budget'), f1('approved_amount'), f1('team_size'), f1('attrition_rate'),
                                    f1('core_policies_met_count'), f1('core_policies_total_count'), f1('fcra_registration'), f1('foreign_contribution_rate')],
         'The same measure for the same organisation one year earlier; a dash if none'),
    ],
}

# ---------------------------------------------------------------- dashboard metrics (page "From columns to dashboard numbers")
# (field name, plain label, plain definition, upstream columns, charts, chart-level filter in plain words)
METRICS = [
    ('distinct_grantees', 'Grantees', 'Number of different organisations', [f1('organization_id'), 'fct5_maturity_rag.organization_id'], ['1.01', '1.07', '1.08', '1.10', '1.16', '2.07', '1.13'], 'e.g. active grants only'),
    ('distinct_grants', 'Grants', 'Number of different grants', [f1('grant_id')], ['1.03', '1.05', '1.06', '3.01', '3.02', '3.03', '3.05', '3.06'], 'e.g. pending decisions only'),
    ('distinct_needs', 'Support needs', 'Number of different support requests', ['fct3_support_activity.support_id'], ['1.04', '1.14', '1.15'], 'e.g. open requests only'),
    ('pct_active_grants_on_track', 'Active grantees on track', 'On-track active grants divided by active grants', [f1('is_active_grant'), f1('is_on_track_active_grant'), f1('grant_id')], ['1.02'], ''),
    ('pct_outcomes_achieved', 'Outcome achieved', 'Achieved outcomes divided by all outcomes', [f1('achieved_outcomes_count'), f1('total_outcomes_count')], ['3.07'], ''),
    ('pct_outcomes_on_track', 'Outcomes on track', 'On-track outcomes (latest update) divided by all outcomes', ['fct2_outcome_progress.status', 'fct2_outcome_progress.is_latest_update', 'fct2_outcome_progress.outcome_id'], ['1.12'], 'latest update only'),
    ('sum_committed_lakh', 'Committed (₹ lakh)', 'Committed amount divided by 100,000', [f1('committed_amount')], ['2.05', '2.06', '2.08'], ''),
    ('sum_disbursed_lakh', 'Disbursed (₹ lakh)', 'Disbursed amount divided by 100,000', [f1('disbursed_amount')], ['2.05', '2.06', '2.08', '4.03'], ''),
    ('sum_approved_lakh', 'Approved (₹ lakh)', 'Approved amount divided by 100,000', [f1('approved_amount')], ['4.03'], ''),
    ('inr_approved / inr_proposed / inr_annual_budget / inr_cost_per_beneficiary', 'Rupee amounts in Indian digit grouping', 'Amount shown as text, for example ₹7,50,000', [f1('approved_amount'), f1('proposed_amount'), f1('annual_budget'), f1('cost_per_beneficiary')], ['1.11', '3.04', '3.07', '4.01', '4.05', '4.08'], ''),
    ('inr_available ... inr_unallocated (8 fields)', 'Budget amounts in Indian digit grouping', 'Budget tiles shown as text', ['fct4_budget_year.available_budget', 'fct4_budget_year.dividend_income', 'fct4_budget_year.prior_year_carry_forward', 'fct4_budget_year.annual_committed_funding', 'fct4_budget_year.next_year_q1_committed_funding', 'fct4_budget_year.annual_disbursed_funding', 'fct4_budget_year.unallocated_balance'], ['2.01', '2.02', '2.03', '2.04', '2.09', '2.10', '2.11', '2.12'], ''),
    ('txt_status_q1 ... txt_status_q4', 'Quarter status', 'On Track or Off Track for each quarter', ['fct2_outcome_progress.quarter', 'fct2_outcome_progress.status'], ['4.06'], ''),
    ('txt_due_date / link fields', 'Due date and links', 'Date as 31 Mar 2027; link to the report and to Grantee 360', [f1('decision_due_date'), f1('annual_report_link'), f1('organisation')], ['3.07', '4.08'], ''),
]

CHART_NAMES = {
    '1.01': 'Grantees', '1.02': 'Active grantees on track', '1.03': 'Off-track active grants', '1.04': 'Open support needs',
    '1.05': 'Grants by duration of support', '1.06': 'Grants by grant type', '1.07': 'Grantees by thematic area',
    '1.08': 'Education sub-categories', '1.09': 'Beneficiaries reached', '1.10': 'Beneficiary type', '1.11': 'Comparative metrics',
    '1.12': 'Quarterly outcome status', '1.13': 'Maturity level', '1.14': 'Support needs raised', '1.15': 'Support provided', '1.16': 'Year on year',
    '2.01': 'Available budget', '2.02': 'Committed funding', '2.03': 'Disbursed funding', '2.04': 'Unallocated balance',
    '2.05': 'Funding by thematic area', '2.06': 'Funding by grant type', '2.07': 'Funding range', '2.08': 'Funding year on year',
    '2.09': 'Dividends', '2.10': 'Carry forward', '2.11': 'Current year', '2.12': 'Next year Q1',
    '3.01': 'Pending decisions', '3.02': 'Overdue', '3.03': 'Due in 30 days', '3.04': 'Proposed renewals',
    '3.05': 'Due window', '3.06': 'Recommendations', '3.07': 'Decision list',
    '4.01': 'Profile', '4.02': 'Annual information', '4.03': 'Funding history', '4.04': 'Maturity assessment',
    '4.05': 'Beneficiaries', '4.06': 'Outcome status', '4.07': 'Support requests', '4.08': 'Latest decision',
}

# ---------------------------------------------------------------- worked examples (page "A number, step by step")
TRACES = [
    {
        'title': 'Grantees (chart 1.01): how many organisations have an active grant',
        'steps': [
            ('Source tab', '8. Grant Registry', 'column: Organisation ID, Grant Status'),
            ('Cleaned copy', 'stg_grants', 'organization_id, grant_status'),
            ('Dashboard-ready table', 'fct1_grant_portfolio', 'organization_id; is_active_grant (true when Active)'),
            ('Dashboard number', 'distinct_grantees', 'counts different organisation IDs, only rows where is_active_grant is true'),
            ('Chart', '1.01 Grantees', 'one number'),
        ],
    },
    {
        'title': 'Unallocated balance (chart 2.04): money still free to commit',
        'steps': [
            ('Source tabs', '5. Dividends; 6. Committed & Spent Tracker', 'Dividends; Planned Amount, Status, Quarter'),
            ('Cleaned copies', 'stg_dividends; stg_disbursements', 'dividend_income; planned_amount, status, quarter'),
            ('Dashboard-ready table', 'fct4_budget_year', 'available_budget minus annual_committed_funding minus next_year_q1_committed_funding'),
            ('Dashboard number', 'inr_unallocated', 'unallocated_balance shown with Indian digit grouping'),
            ('Chart', '2.04 Unallocated balance', 'one number'),
        ],
    },
    {
        'title': 'Previous year (chart 4.02): last year\'s value for the selected organisation',
        'steps': [
            ('Source tab', '8. Grant Registry', 'Annual Budget, Team Size ... for each year'),
            ('Cleaned copy', 'stg_grants', 'annual_budget, team_size ...'),
            ('Dashboard-ready tables', 'fct1_grant_portfolio, then fct6_grantee_annual_info', 'fct6 finds the same organisation\'s row one year earlier'),
            ('Dashboard field', 'previous_value', 'shown as it is, a dash if there is no earlier year'),
            ('Chart', '4.02 Annual information', 'table: Metric, Selected year, Previous year'),
        ],
    },
]

# ---------------------------------------------------------------- blocks: how a final table is split into readable bands
# table -> [(band title, [columns])]. Every column of the table must appear in exactly one band (build_v2.py checks this).
BLOCKS = {
    'fct1_grant_portfolio': [
        ('Grant: identity, status, dates, display text', ['financial_year', 'grant_id', 'organization_id', 'organisation', 'mission', 'thematic_area',
            'education_sub_category', 'proximity_to_children_beneficiary', 'grant_type', 'grant_status', 'grant_start_date', 'grant_end_date',
            'has_completed_program_lifecycle', 'is_active_grant', 'grant_period', 'grant_status_type_amount', 'sub_category_line']),
        ('Organisation profile and years funded', ['fcra_registration', 'funding_year', 'duration_of_support_bucket', 'annual_budget', 'team_size',
            'attrition_rate', 'foreign_contribution_rate', 'core_policies_met_count', 'core_policies_total_count']),
        ('Beneficiaries and money', ['primary_beneficiary_group', 'primary_beneficiary_count', 'approved_amount', 'committed_amount', 'disbursed_amount',
            'cost_per_beneficiary', 'funding_range', 'funding_range_order', 'is_funded_grantee']),
        ('Decision', ['decision_type', 'decision_status', 'recommendation', 'decision_due_date', 'reason_for_recommendation', 'proposed_amount',
            'annual_report_link', 'due_window', 'due_window_order', 'is_pending_decision', 'is_overdue_decision', 'is_due_within_30_days']),
        ('Performance and maturity', ['grant_performance_status', 'is_on_track_active_grant', 'is_off_track_active_grant', 'total_outcomes_count',
            'achieved_outcomes_count', 'clarity_status', 'capacity_status', 'compliance_status']),
        ('Housekeeping', ['grantee_360_link', 'as_of_date']),
    ],
}

// How each numeric / date column in the output tabs should be formatted in Google Sheets.
// The pipeline never sets formats itself: the Table column types (and the custom number
// formats below) own them. A test keeps this list in step with the real output columns,
// and tests/generate_table_formats.js turns it into docs/TABLE_FORMATS.md.
//
//   rupee        whole rupees                 → Indian rupee format
//   rupee_paise  rupees with paise            → Indian rupee format, 2 decimals
//   percent      stored as a fraction (0.08)  → Percent
//   count        whole number                 → Indian number format (no ₹)
//   quantity     mixed: a fraction when the target is a % (0.7), a count otherwise → Automatic
//   date         real dates                   → Date
const FORMATS = {
  stg_grants: {
    date: ['grant_start_date', 'grant_end_date'],
    rupee: ['approved_amount', 'annual_budget'],
    percent: ['attrition_rate', 'foreign_contribution_rate'],
    count: ['years_implemented', 'team_size', 'primary_beneficiary_count'],
  },
  stg_organisations: { date: ['fcra_registration_expiry_date'] },
  stg_outcome_progress: {},
  stg_support: {},
  stg_decisions: { date: ['decision_due_date'], rupee: ['proposed_amount'] },
  stg_dividends: { rupee: ['dividend_income'] },
  stg_disbursements: { date: ['planned_date', 'actual_date'], rupee: ['planned_amount', 'actual_amount'] },
  stg_maturity: {},
  fct1_grant_portfolio: {
    date: ['grant_start_date', 'grant_end_date', 'decision_due_date', 'as_of_date'],
    rupee: ['annual_budget', 'approved_amount', 'committed_amount', 'disbursed_amount', 'proposed_amount'],
    rupee_paise: ['cost_per_beneficiary'],
    percent: ['attrition_rate', 'foreign_contribution_rate'],
    count: ['primary_beneficiary_count', 'team_size', 'core_policies_met_count', 'core_policies_total_count', 'total_outcomes_count', 'achieved_outcomes_count'],
  },
  fct2_outcome_progress: {
    percent: ['outcome_achievement_pct', 'annual_achievement_pct'],
    quantity: ['target_value', 'achieved_value', 'final_actual_value'],
  },
  fct3_support_activity: {},
  fct4_budget_year: {
    rupee: ['dividend_income', 'prior_year_carry_forward', 'available_budget', 'annual_committed_funding', 'next_year_q1_committed_funding', 'annual_disbursed_funding', 'unallocated_balance'],
  },
  fct5_maturity_rag: {},
};

// Google Sheets custom number formats (Format → Number → Custom number format).
const NUMBER_FORMATS = {
  rupee: '[>=10000000]"₹"##\\,##\\,##\\,##0;[>=100000]"₹"##\\,##\\,##0;"₹"##,##0',
  rupee_paise: '[>=10000000]"₹"##\\,##\\,##\\,##0.00;[>=100000]"₹"##\\,##\\,##0.00;"₹"##,##0.00',
  count: '[>=10000000]##\\,##\\,##\\,##0;[>=100000]##\\,##\\,##0;##,##0',
  percent: '0%',
  date: 'yyyy-mm-dd',
  quantity: 'Automatic',
};

module.exports = { FORMATS, NUMBER_FORMATS };

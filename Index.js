/**
 * Index.gs — sheet names are read from the Index tab at runtime (SoP 1.2, 2.4).
 * Renaming a tab only needs an Index edit, never a script change.
 */

const INDEX_SHEET_NAME = 'Index';
const INDEX_HEADERS = ['key', 'sheet_name', 'layer', 'cardinality', 'description'];

// Defaults written by setupIndex(). After the first run, the Index tab is maintained manually.
// src_ rows point at tabs in the SOURCE workbook; every other row is a tab in the pipeline workbook.
const INDEX_DEFAULTS = [
  ['SRC_GRANT_REGISTRY', '8. Grant Registry', 'src', 'One row per grant', 'Grant master data synced from each approved Grant Setup workbook'],
  ['SRC_ORGANISATION_REGISTRY', '9. Organisation Registry', 'src', 'One row per organisation', 'Organisation master data: mission, policies, FCRA and compliance documents'],
  ['SRC_OUTCOME_PROGRESS', '2. Outcome Progress', 'src', 'One row per grant x outcome', 'Outcome targets with Q1–Q4 progress, status and notes'],
  ['SRC_SUPPORT', '3. Support', 'src', 'One row per support request', 'Support requests raised by grantees and their status'],
  ['SRC_DECISION_TRACKER', '4. Decision Tracker', 'src', 'One row per grant under decision', 'Renewal / closure recommendations, due dates and proposed amounts'],
  ['SRC_DIVIDENDS', '5. Dividends', 'src', 'One row per financial year', 'Dividend income entered manually'],
  ['SRC_DISBURSEMENTS', '6. Committed & Spent Tracker', 'src', 'One row per disbursement tranche', 'Planned (committed) and actual (disbursed) tranches'],
  ['SRC_MATURITY', '7. Organisation Maturity', 'src', 'One row per grant x maturity indicator', 'Red / Amber / Green maturity assessment per indicator'],

  ['STG_GRANTS', 'stg_grants', 'stg', 'One row per grant_id', 'Cleaned Grant Registry: pipeline columns only, bank and narrative fields dropped'],
  ['STG_ORGANISATIONS', 'stg_organisations', 'stg', 'One row per organization_id', 'Cleaned Organisation Registry: mission, FCRA status, core policies, annual report link'],
  ['STG_OUTCOME_PROGRESS', 'stg_outcome_progress', 'stg', 'One row per grant_id x outcome_id', 'Cleaned Outcome Progress, still wide (Q1–Q4 as columns)'],
  ['STG_SUPPORT', 'stg_support', 'stg', 'One row per support request', 'Cleaned Support requests'],
  ['STG_DECISIONS', 'stg_decisions', 'stg', 'One row per grant_id under decision', 'Cleaned Decision Tracker'],
  ['STG_DIVIDENDS', 'stg_dividends', 'stg', 'One row per financial_year', 'Dividend income with FY normalised to the YYYY-YY format'],
  ['STG_DISBURSEMENTS', 'stg_disbursements', 'stg', 'One row per disbursement_id', 'Cleaned Committed & Spent Tracker'],
  ['STG_MATURITY', 'stg_maturity', 'stg', 'One row per grant_id x aspect x indicator', 'Cleaned Organisation Maturity RAG ratings'],

  ['FCT1_GRANT_PORTFOLIO', 'fct1_grant_portfolio', 'fct', 'One row per grant_id', 'Grant-level portfolio, funding, decision and organisation profile for all dashboard views'],
  ['FCT2_OUTCOME_PROGRESS', 'fct2_outcome_progress', 'fct', 'One row per grant_id x outcome_id x quarter (reported quarters only)', 'Quarterly outcome progress and status'],
  ['FCT3_SUPPORT_ACTIVITY', 'fct3_support_activity', 'fct', 'One row per support_id', 'Support needs raised and APFP responses'],
  ['FCT4_BUDGET_YEAR', 'fct4_budget_year', 'fct', 'One row per financial_year', 'Dividends, carry-forward, commitments, disbursements and unallocated balance'],
  ['FCT5_MATURITY_RAG', 'fct5_maturity_rag', 'fct', 'One row per grant_id x aspect x indicator', 'Maturity RAG at indicator level for portfolio and Grantee 360 views'],
  ['FCT6_GRANTEE_ANNUAL_INFO', 'fct6_grantee_annual_info', 'fct', 'One row per grant_id x metric', 'Annual organisational information as metric rows with the selected and previous financial year side by side (Grantee 360)'],

  ['REF_SOURCE_HEADER_BASELINE', 'ref_source_header_baseline', 'ref', 'One row per source tab x column', 'Expected source headers used by the Source Header Check'],
  ['UTIL_SOURCE_HEADER_AUDIT', 'Source_Header_Audit', 'util', 'One row per header issue per run', 'Result of the latest Source Header Check'],
  ['UTIL_PIPELINE_LOG', 'Pipeline Log', 'util', 'One row per log entry', 'Execution log for every build function'],
  ['UTIL_CARDINALITY_TESTS', 'Cardinality Test Results', 'util', 'One row per test', 'Result of the latest runCardinalityTests()'],
];

/** Creates (or resets) the Index tab with the defaults above. Run once, then edit the tab by hand. */
function setupIndex() {
  const ss = getPipelineSpreadsheet();
  const rows = INDEX_DEFAULTS.map(function (r) { return r.slice(); });
  writeSheet(ss, INDEX_SHEET_NAME, INDEX_HEADERS, rows);
  return rows.length;
}

/** Returns { KEY: sheet_name } read from the Index tab. Creates the tab on first use. */
function getSheetIndex(ss) {
  if (!ss.getSheetByName(INDEX_SHEET_NAME)) setupIndex();
  const rows = readSheet(ss, INDEX_SHEET_NAME);
  const idx = {};
  rows.forEach(function (r) {
    if (r.key) idx[r.key] = r.sheet_name;
  });
  const missing = INDEX_DEFAULTS.filter(function (r) { return !idx[r[0]]; });
  if (missing.length) {
    // A release added tabs: append their default rows, keep every existing row (and any renamed tab) as it is.
    const kept = rows.map(function (r) { return INDEX_HEADERS.map(function (h) { return r[h]; }); });
    writeSheet(ss, INDEX_SHEET_NAME, INDEX_HEADERS, kept.concat(missing.map(function (r) { return r.slice(); })));
    missing.forEach(function (r) { idx[r[0]] = r[1]; });
  }
  return idx;
}

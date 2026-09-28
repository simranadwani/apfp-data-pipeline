/**
 * Staging.gs — one buildStg*() per source tab (SoP 3, Step 3).
 * Each function reads a source tab from the SOURCE workbook, keeps only the columns the
 * pipeline uses (bank details, narratives and QA columns are dropped), renames them to
 * snake_case, normalises types, and writes a stg_ tab in the PIPELINE workbook.
 * Category values are kept exactly as they appear in the source.
 *
 * Column spec: [stg_column, source header, type]
 *   text   → trimmed string
 *   number → number ('' when blank; commas, ₹ and spaces are stripped)
 *   rate   → number; "8%" becomes 0.08, numbers are kept as they are
 *   date   → Date at midnight ('' when blank or unparseable)
 *   fy     → financial year in the source format YYYY-YY ("April 25-March 26" → "2025-26")
 */

const STAGING_SPECS = {
  STG_GRANTS: {
    src: 'SRC_GRANT_REGISTRY',
    required: ['grant_id'],
    columns: [
      ['grant_id', 'Grant ID', 'text'],
      ['financial_year', 'Financial Year', 'fy'],
      ['grant_start_quarter', 'Grant Start Quarter', 'text'],
      ['organization_id', 'Organisation ID', 'text'],
      ['organisation', 'Organisation Name', 'text'],
      ['thematic_area', 'Thematic Area', 'text'],
      ['thematic_sub_area', 'Thematic Sub-area', 'text'],
      ['proximity_to_children_beneficiary', 'Proximity to Children / Beneficiary', 'text'],
      ['project_title', 'Project Title', 'text'],
      ['grant_start_date', 'Grant Start Date', 'date'],
      ['grant_end_date', 'Grant End Date', 'date'],
      ['grant_type', 'Grant Type', 'text'],
      ['approved_amount', 'Amount Approved', 'number'],
      ['grant_status', 'Grant Status', 'text'],
      ['programme_status', 'Programme Status', 'text'],
      ['years_implemented', 'Years Implemented', 'number'],
      ['team_size', 'Team Size — Current FY', 'number'],
      ['attrition_rate', 'Employee Attrition — Current Snapshot', 'rate'],
      ['annual_budget', 'Annual Budget — Current FY', 'number'],
      ['primary_beneficiary_group', 'Primary Beneficiary Group', 'text'],
      ['primary_beneficiary_count', 'Primary Beneficiary Count', 'number'],
      ['foreign_contribution_rate', 'Foreign Funding — Percentage of Total Annual Funding', 'rate'],
      ['record_status', 'Record Status', 'text'],
    ],
  },
  STG_ORGANISATIONS: {
    src: 'SRC_ORGANISATION_REGISTRY',
    required: ['organization_id'],
    columns: [
      ['organization_id', 'Organisation ID', 'text'],
      ['organisation', 'Organisation Name', 'text'],
      ['mission_statement', 'Mission Statement', 'text'],
      ['has_code_of_conduct_policy', 'Code of Conduct Policy?', 'text'],
      ['has_posh_policy', 'POSH Policy?', 'text'],
      ['has_child_protection_policy', 'Child Protection Policy?', 'text'],
      ['has_data_protection_policy', 'Data Protection Policy?', 'text'],
      ['latest_annual_report_link', 'Latest Annual Report Link', 'text'],
      ['fcra_registration_status', 'FCRA Registration Status', 'text'],
      ['fcra_registration_expiry_date', 'FCRA Registration Expiry Date', 'date'],
      ['record_status', 'Record Status', 'text'],
    ],
  },
  STG_OUTCOME_PROGRESS: {
    src: 'SRC_OUTCOME_PROGRESS',
    required: ['grant_id', 'outcome_id'],
    columns: [
      ['financial_year', 'Financial Year', 'fy'],
      ['grant_id', 'Grant ID', 'text'],
      ['organisation', 'Organisation Name', 'text'],
      ['outcome_id', 'Outcome ID', 'text'],
      ['outcome_indicator', 'Outcome / Indicator', 'text'],
      ['target_text', 'End-of-Program Cycle Target', 'text'],
      ['q1_progress', 'Q1 Progress', 'text'],
      ['q1_evidence_link', 'Q1 Evidence Link', 'text'],
      ['q1_status', 'Q1 Status', 'text'],
      ['q1_notes', 'Q1 Anagha Notes', 'text'],
      ['q2_progress', 'Q2 Progress', 'text'],
      ['q2_evidence_link', 'Q2 Evidence Link', 'text'],
      ['q2_status', 'Q2 Status', 'text'],
      ['q2_notes', 'Q2 Anagha Notes', 'text'],
      ['q3_progress', 'Q3 Progress', 'text'],
      ['q3_evidence_link', 'Q3 Evidence Link', 'text'],
      ['q3_status', 'Q3 Status', 'text'],
      ['q3_notes', 'Q3 Anagha Notes', 'text'],
      ['q4_progress', 'Q4 Progress', 'text'],
      ['q4_evidence_link', 'Q4 Evidence Link', 'text'],
      ['q4_status', 'Q4 Status', 'text'],
      ['q4_notes', 'Q4 Anagha Notes', 'text'],
      ['final_actual_text', 'Final Actual', 'text'],
    ],
  },
  STG_SUPPORT: {
    src: 'SRC_SUPPORT',
    required: ['grant_id'],
    columns: [
      ['financial_year', 'Financial Year', 'fy'],
      ['grant_id', 'Grant ID', 'text'],
      ['organisation', 'Organisation Name', 'text'],
      ['outcome_id', 'Outcome ID', 'text'],
      ['quarter', 'Quarter', 'text'],
      ['support_type', 'Support Type', 'text'],
      ['support_required', 'Support Required', 'text'],
      ['evidence_link', 'Evidence Link', 'text'],
      ['status', 'Status', 'text'],
      ['notes', 'Anagha Notes', 'text'],
    ],
  },
  STG_DECISIONS: {
    src: 'SRC_DECISION_TRACKER',
    required: ['grant_id'],
    columns: [
      ['decision_for_fy', 'Decision For FY', 'fy'],
      ['previous_grant_fy', 'Previous Grant FY', 'fy'],
      ['grant_id', 'Grant ID', 'text'],
      ['organisation', 'Organisation Name', 'text'],
      ['grant_type', 'Grant Type', 'text'],
      ['decision_type', 'Decision Type', 'text'],
      ['decision_status', 'Decision Status', 'text'],
      ['decision_rationale', 'Decision Rationale', 'text'],
      ['proposed_amount', 'Proposed Amount', 'number'],
      ['decision_due_date', 'Decision Due Date', 'date'],
      ['annual_report_link', 'Annual Report Link', 'text'],
    ],
  },
  STG_DIVIDENDS: {
    src: 'SRC_DIVIDENDS',
    required: ['financial_year'],
    columns: [
      ['financial_year', 'FY', 'fy'],
      ['dividend_income', 'Dividends', 'number'],
    ],
  },
  STG_DISBURSEMENTS: {
    src: 'SRC_DISBURSEMENTS',
    required: ['disbursement_id'],
    columns: [
      ['disbursement_id', 'Disbursement ID', 'text'],
      ['financial_year', 'Financial Year', 'fy'],
      ['quarter', 'Quarter', 'text'],
      ['grant_id', 'Grant ID', 'text'],
      ['organisation', 'Organisation Name', 'text'],
      ['planned_date', 'Planned Date', 'date'],
      ['planned_amount', 'Planned Amount', 'number'],
      ['status', 'Status', 'text'],
      ['actual_date', 'Actual Date', 'date'],
      ['actual_amount', 'Actual Amount', 'number'],
    ],
  },
  STG_MATURITY: {
    src: 'SRC_MATURITY',
    required: ['grant_id'],
    columns: [
      ['financial_year', 'Financial Year', 'fy'],
      ['grant_id', 'Grant ID', 'text'],
      ['organisation', 'Organisation Name', 'text'],
      ['aspect', 'Aspect', 'text'],
      ['indicator', 'Indicator', 'text'],
      ['status', 'Status', 'text'],
    ],
  },
};

function buildStgGrants(ss, idx) { return stageTable(ss, idx, 'STG_GRANTS'); }
function buildStgOrganisations(ss, idx) { return stageTable(ss, idx, 'STG_ORGANISATIONS'); }
function buildStgOutcomeProgress(ss, idx) { return stageTable(ss, idx, 'STG_OUTCOME_PROGRESS'); }
function buildStgSupport(ss, idx) { return stageTable(ss, idx, 'STG_SUPPORT'); }
function buildStgDecisions(ss, idx) { return stageTable(ss, idx, 'STG_DECISIONS'); }
function buildStgDividends(ss, idx) { return stageTable(ss, idx, 'STG_DIVIDENDS'); }
function buildStgDisbursements(ss, idx) { return stageTable(ss, idx, 'STG_DISBURSEMENTS'); }
function buildStgMaturity(ss, idx) { return stageTable(ss, idx, 'STG_MATURITY'); }

/** Shared body of every buildStg*(): read source tab → select, rename, cast → write stg_ tab. */
function stageTable(ss, idx, stgKey) {
  const spec = STAGING_SPECS[stgKey];
  const srcSheetName = idx[spec.src];
  const src = readSheetWithHeaders(getSourceSpreadsheet(), srcSheetName);

  const missing = spec.columns.filter(function (c) { return src.headers.indexOf(c[1]) === -1; });
  if (missing.length) {
    throw new Error('"' + srcSheetName + '" is missing columns: ' + missing.map(function (c) { return c[1]; }).join(', '));
  }

  const headers = spec.columns.map(function (c) { return c[0]; });
  const problems = [];
  let skipped = 0;
  const rows = [];
  src.rows.forEach(function (srcRow, i) {
    const out = {};
    spec.columns.forEach(function (c) {
      const res = castValue(srcRow[c[1]], c[2]);
      if (res.error) problems.push('row ' + (i + 1) + ' ' + c[1] + ': "' + srcRow[c[1]] + '" is not a valid ' + c[2]);
      out[c[0]] = res.value;
    });
    if (spec.required.some(function (col) { return isBlank(out[col]); })) {
      skipped++;
      return;
    }
    rows.push(out);
  });

  if (skipped) {
    log(ss, idx, 'WARN', 'stageTable:' + stgKey, 0,
      skipped + ' row(s) in "' + srcSheetName + '" skipped because ' + spec.required.join(' / ') + ' is blank', null, 'SUCCESS');
  }
  if (problems.length) {
    log(ss, idx, 'WARN', 'stageTable:' + stgKey, 0,
      problems.length + ' value(s) blanked: ' + problems.slice(0, 10).join('; ') + (problems.length > 10 ? ' …' : ''), null, 'SUCCESS');
  }
  return writeSheet(ss, idx[stgKey], headers, rows);
}

/** Returns { value, error } for one source cell. Blank cells always give ''. */
function castValue(v, type) {
  if (isBlank(v)) return { value: '' };
  switch (type) {
    case 'text':
      return { value: v instanceof Date ? formatIsoDate(v) : String(v).trim() };
    case 'number': {
      if (typeof v === 'number') return { value: v };
      const n = Number(String(v).replace(/[₹,\s]/g, ''));
      return isNaN(n) ? { value: '', error: true } : { value: n };
    }
    case 'rate': {
      if (typeof v === 'number') return { value: v };
      const s = String(v).replace(/\s/g, '');
      const pct = /%$/.test(s);
      const n = Number(s.replace(/%$/, ''));
      if (isNaN(n)) return { value: '', error: true };
      return { value: pct ? n / 100 : n };
    }
    case 'date': {
      const d = parseDateValue(v);
      return d ? { value: d } : { value: '', error: true };
    }
    case 'fy': {
      const fy = normaliseFinancialYear(v);
      return fy ? { value: fy } : { value: String(v).trim(), error: true };
    }
    default:
      throw new Error('Unknown column type: ' + type);
  }
}

/** Date objects are kept (time dropped); strings in yyyy-mm-dd or dd/mm/yyyy are parsed. */
function parseDateValue(v) {
  if (v instanceof Date) return isNaN(v.getTime()) ? null : new Date(v.getFullYear(), v.getMonth(), v.getDate());
  const s = String(v).trim();
  let m = /^(\d{4})-(\d{1,2})-(\d{1,2})/.exec(s);
  if (m) return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  m = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(s);
  if (m) return new Date(Number(m[3]), Number(m[2]) - 1, Number(m[1]));
  return null;
}

/**
 * Normalises financial-year labels to the source format "YYYY-YY".
 * Accepts "2026-27", "2026-2027", "FY 26-27", "FY26-27" and the Dividends
 * format "April 25-March 26". Returns '' when the label is not recognised.
 */
function normaliseFinancialYear(v) {
  const s = String(v).trim();
  let m = /^(\d{4})\s*-\s*(\d{2}|\d{4})$/.exec(s);
  if (m) return m[1] + '-' + m[2].slice(-2);
  m = /^FY\s*(\d{2})\s*-\s*(\d{2})$/i.exec(s);
  if (m) return '20' + m[1] + '-' + m[2];
  m = /^April\s*(\d{2}|\d{4})\s*-\s*March\s*(\d{2}|\d{4})$/i.exec(s);
  if (m) {
    const start = m[1].length === 2 ? 2000 + Number(m[1]) : Number(m[1]);
    return start + '-' + m[2].slice(-2);
  }
  return '';
}

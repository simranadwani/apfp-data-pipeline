/**
 * Final.gs — one buildFct*() per dashboard fact table (SoP 3, Step 6).
 * Reads only stg_ tabs. Every derived field is documented in PIPELINE_LOGIC.md.
 * Dashboard metrics (distinct counts, sums, ratios) are Looker Studio calculated
 * fields, not stored columns, so they never double count.
 */

const CORE_POLICY_COLUMNS = ['has_code_of_conduct_policy', 'has_posh_policy', 'has_child_protection_policy', 'has_data_protection_policy'];
const COMMITTED_DISBURSEMENT_STATUSES = ['committed', 'disbursed'];
const QUARTERS = ['Q1', 'Q2', 'Q3', 'Q4'];
const RAG_SEVERITY = { green: 1, amber: 2, red: 3 };

const FCT1_HEADERS = [
  'financial_year', 'grant_id', 'organization_id', 'organisation', 'mission', 'thematic_area',
  'education_sub_category', 'proximity_to_children_beneficiary', 'grant_status', 'grant_type',
  'grant_performance_status', 'grant_start_date', 'grant_end_date', 'funding_year',
  'duration_of_support_bucket', 'primary_beneficiary_group', 'primary_beneficiary_count',
  'clarity_status', 'capacity_status', 'compliance_status', 'fcra_registration',
  'has_completed_program_lifecycle', 'annual_budget', 'team_size', 'attrition_rate',
  'foreign_contribution_rate', 'core_policies_met_count', 'core_policies_total_count',
  'approved_amount', 'committed_amount', 'disbursed_amount', 'funding_range',
  'decision_type', 'decision_status', 'due_window', 'recommendation', 'decision_due_date',
  'reason_for_recommendation', 'grantee_360_link', 'proposed_amount', 'total_outcomes_count',
  'achieved_outcomes_count', 'annual_report_link', 'grant_period', 'grant_status_type_amount',
  'cost_per_beneficiary', 'is_active_grant', 'is_funded_grantee', 'is_pending_decision',
  'is_overdue_decision', 'is_due_within_30_days', 'is_on_track_active_grant',
  'is_off_track_active_grant', 'as_of_date',
];

const FCT2_HEADERS = [
  'financial_year', 'grant_id', 'organization_id', 'organisation', 'thematic_area', 'outcome_id',
  'outcome_indicator', 'quarter', 'status', 'target_value', 'achieved_value',
  'outcome_achievement_pct', 'outcome_notes', 'evidence_link', 'is_latest_update',
];

const FCT3_HEADERS = [
  'financial_year', 'grant_id', 'organization_id', 'organisation', 'thematic_area', 'support_id',
  'quarter', 'support_category', 'request_description', 'support_status', 'is_open_support_need',
  'response_category', 'response_notes', 'response_date', 'evidence_link',
];

const FCT4_HEADERS = [
  'financial_year', 'dividend_income', 'prior_year_carry_forward', 'available_budget',
  'annual_committed_funding', 'next_year_q1_committed_funding', 'annual_disbursed_funding',
  'unallocated_balance',
];

const FCT5_HEADERS = [
  'financial_year', 'grant_id', 'organization_id', 'organisation', 'thematic_area', 'aspect',
  'indicator', 'status',
];

// ---------------------------------------------------------------------------
// fct1_grant_portfolio — one row per grant_id
// ---------------------------------------------------------------------------
function buildFct1GrantPortfolio(ss, idx) {
  const today = pipelineToday();
  const grants = readSheet(ss, idx.STG_GRANTS);
  const orgById = indexBy(readSheet(ss, idx.STG_ORGANISATIONS), 'organization_id');
  const decisionByGrant = indexBy(readSheet(ss, idx.STG_DECISIONS), 'grant_id');
  const disbByGrant = groupBy(readSheet(ss, idx.STG_DISBURSEMENTS), 'grant_id');
  const maturityByGrant = groupBy(readSheet(ss, idx.STG_MATURITY), 'grant_id');
  const outcomesByGrant = groupBy(readSheet(ss, idx.STG_OUTCOME_PROGRESS), 'grant_id');
  warnOrphanGrantIds(ss, idx, 'buildFct1GrantPortfolio', grants, {
    stg_decisions: decisionByGrant, stg_disbursements: disbByGrant,
    stg_maturity: maturityByGrant, stg_outcome_progress: outcomesByGrant,
  });

  // Distinct funded financial years per organisation, for funding_year.
  const fysByOrg = {};
  grants.forEach(function (g) {
    if (isBlank(g.organization_id) || isBlank(g.financial_year)) return;
    (fysByOrg[g.organization_id] = fysByOrg[g.organization_id] || {})[g.financial_year] = true;
  });

  const rows = grants.map(function (g) {
    const org = orgById[g.organization_id] || {};
    const dec = decisionByGrant[g.grant_id] || {};
    const funding = sumDisbursements(disbByGrant[g.grant_id] || []);
    const outcomes = outcomesByGrant[g.grant_id] || [];
    const maturity = maturityByGrant[g.grant_id] || [];
    const performance = grantPerformanceStatus(outcomes);
    const decisionStatus = mapDecisionStatus(dec.decision_status);
    const isPending = decisionStatus === 'Pending';
    const daysToDue = dec.decision_due_date instanceof Date ? daysBetween(today, dec.decision_due_date) : null;
    const fundingYearNumber = fysByOrg[g.organization_id]
      ? Object.keys(fysByOrg[g.organization_id]).filter(function (fy) { return fy <= g.financial_year; }).length
      : null;
    const isActive = String(g.grant_status).trim().toLowerCase() === 'active';

    return {
      financial_year: g.financial_year,
      grant_id: g.grant_id,
      organization_id: g.organization_id,
      organisation: g.organisation,
      mission: org.mission_statement,
      thematic_area: g.thematic_area,
      education_sub_category: g.thematic_sub_area,
      proximity_to_children_beneficiary: g.proximity_to_children_beneficiary,
      grant_status: g.grant_status,
      grant_type: g.grant_type,
      grant_performance_status: performance,
      grant_start_date: g.grant_start_date,
      grant_end_date: g.grant_end_date,
      funding_year: fundingYearNumber ? 'Year ' + fundingYearNumber : '',
      duration_of_support_bucket: durationBucket(fundingYearNumber),
      primary_beneficiary_group: g.primary_beneficiary_group,
      primary_beneficiary_count: g.primary_beneficiary_count,
      clarity_status: worstRag(maturity, 'Clarity'),
      capacity_status: worstRag(maturity, 'Capacity'),
      compliance_status: worstRag(maturity, 'Compliance'),
      fcra_registration: org.fcra_registration_status,
      has_completed_program_lifecycle: String(g.grant_status).trim().toLowerCase() === 'complete',
      annual_budget: g.annual_budget,
      team_size: g.team_size,
      attrition_rate: g.attrition_rate,
      foreign_contribution_rate: g.foreign_contribution_rate,
      core_policies_met_count: orgById[g.organization_id] ? countCorePolicies(org) : '',
      core_policies_total_count: CORE_POLICY_COLUMNS.length,
      approved_amount: g.approved_amount,
      committed_amount: funding.committed,
      disbursed_amount: funding.disbursed,
      funding_range: '', // filled below: needs the organisation × FY total
      decision_type: isBlank(dec.decision_type) ? '' : (String(dec.decision_type).trim().toLowerCase() === 'close' ? 'Closure' : 'Renewal'),
      decision_status: decisionStatus,
      due_window: isPending && daysToDue !== null ? dueWindow(daysToDue) : '',
      recommendation: dec.decision_type,
      decision_due_date: dec.decision_due_date,
      reason_for_recommendation: dec.decision_rationale,
      grantee_360_link: '',
      proposed_amount: dec.proposed_amount,
      total_outcomes_count: countDistinct(outcomes, 'outcome_id'),
      achieved_outcomes_count: countAchievedOutcomes(outcomes),
      annual_report_link: !isBlank(dec.annual_report_link) ? dec.annual_report_link : org.latest_annual_report_link,
      grant_period: (g.grant_start_date instanceof Date && g.grant_end_date instanceof Date)
        ? formatIsoDate(g.grant_start_date) + ' - ' + formatIsoDate(g.grant_end_date) : '',
      grant_status_type_amount: [g.grant_status, g.grant_type, g.approved_amount].join(' - '),
      cost_per_beneficiary: (typeof g.approved_amount === 'number' && typeof g.primary_beneficiary_count === 'number' && g.primary_beneficiary_count > 0)
        ? Math.round((g.approved_amount / g.primary_beneficiary_count) * 100) / 100 : '',
      is_active_grant: isActive,
      is_funded_grantee: funding.disbursed > 0,
      is_pending_decision: isPending,
      is_overdue_decision: isPending && daysToDue !== null && daysToDue < 0,
      is_due_within_30_days: isPending && daysToDue !== null && daysToDue >= 0 && daysToDue <= 30,
      is_on_track_active_grant: isActive && performance === 'On Track',
      is_off_track_active_grant: isActive && performance === 'Off Track',
      as_of_date: today,
    };
  });

  // funding_range: band on total disbursed per organisation × financial year.
  const disbursedByOrgFy = {};
  rows.forEach(function (r) {
    const k = key(r.organization_id, r.financial_year);
    disbursedByOrgFy[k] = (disbursedByOrgFy[k] || 0) + r.disbursed_amount;
  });
  rows.forEach(function (r) {
    r.funding_range = fundingRange(disbursedByOrgFy[key(r.organization_id, r.financial_year)]);
  });

  return writeSheet(ss, idx.FCT1_GRANT_PORTFOLIO, FCT1_HEADERS, rows);
}

// ---------------------------------------------------------------------------
// fct2_outcome_progress — one row per grant_id × outcome_id × reported quarter
// ---------------------------------------------------------------------------
function buildFct2OutcomeProgress(ss, idx) {
  const grantById = indexBy(readSheet(ss, idx.STG_GRANTS), 'grant_id');
  const outcomes = readSheet(ss, idx.STG_OUTCOME_PROGRESS);
  warnOrphanGrantIds(ss, idx, 'buildFct2OutcomeProgress', null, { stg_outcome_progress: groupBy(outcomes, 'grant_id') }, grantById);

  const rows = [];
  outcomes.forEach(function (o) {
    const g = grantById[o.grant_id] || {};
    const target = parseMeasure(o.target_text);
    const latest = latestReportedQuarter(o);
    QUARTERS.forEach(function (q) {
      const p = q.toLowerCase();
      const status = o[p + '_status'];
      const progress = o[p + '_progress'];
      if (isBlank(status) && isBlank(progress) && isBlank(o[p + '_notes'])) return; // quarter not reported yet
      const achieved = parseMeasure(progress);
      rows.push({
        financial_year: o.financial_year,
        grant_id: o.grant_id,
        organization_id: g.organization_id,
        organisation: g.organisation || o.organisation,
        thematic_area: g.thematic_area,
        outcome_id: o.outcome_id,
        outcome_indicator: o.outcome_indicator,
        quarter: q,
        status: status,
        target_value: target === null ? '' : target,
        achieved_value: achieved === null ? '' : achieved,
        outcome_achievement_pct: (target && achieved !== null) ? achieved / target : '',
        outcome_notes: o[p + '_notes'],
        evidence_link: o[p + '_evidence_link'],
        is_latest_update: q === latest,
      });
    });
  });
  return writeSheet(ss, idx.FCT2_OUTCOME_PROGRESS, FCT2_HEADERS, rows);
}

// ---------------------------------------------------------------------------
// fct3_support_activity — one row per support request
// ---------------------------------------------------------------------------
function buildFct3SupportActivity(ss, idx) {
  const grantById = indexBy(readSheet(ss, idx.STG_GRANTS), 'grant_id');
  const support = readSheet(ss, idx.STG_SUPPORT);
  warnOrphanGrantIds(ss, idx, 'buildFct3SupportActivity', null, { stg_support: groupBy(support, 'grant_id') }, grantById);

  const seq = {};
  const rows = support.map(function (s) {
    const g = grantById[s.grant_id] || {};
    const k = key(s.grant_id, s.quarter);
    seq[k] = (seq[k] || 0) + 1;
    const status = String(s.status).trim().toLowerCase() === 'in progress' ? 'Open' : s.status;
    return {
      financial_year: s.financial_year,
      grant_id: s.grant_id,
      organization_id: g.organization_id,
      organisation: g.organisation || s.organisation,
      thematic_area: g.thematic_area,
      support_id: 'SUP-' + s.grant_id + '-' + (s.quarter || 'NQ') + '-' + seq[k],
      quarter: s.quarter,
      support_category: s.support_type,
      request_description: s.support_required,
      support_status: status,
      is_open_support_need: String(status).trim().toLowerCase() === 'open',
      response_category: '', // not captured in the source yet
      response_notes: s.notes,
      response_date: '', // not captured in the source yet
      evidence_link: s.evidence_link,
    };
  });
  return writeSheet(ss, idx.FCT3_SUPPORT_ACTIVITY, FCT3_HEADERS, rows);
}

// ---------------------------------------------------------------------------
// fct4_budget_year — one row per financial_year
// ---------------------------------------------------------------------------
function buildFct4BudgetYear(ss, idx) {
  const dividends = readSheet(ss, idx.STG_DIVIDENDS);
  const disbursements = readSheet(ss, idx.STG_DISBURSEMENTS);

  const fySet = {};
  dividends.forEach(function (d) { if (!isBlank(d.financial_year)) fySet[d.financial_year] = true; });
  disbursements.forEach(function (d) { if (!isBlank(d.financial_year)) fySet[d.financial_year] = true; });
  const fys = Object.keys(fySet).sort();

  let carryForward = 0;
  const rows = fys.map(function (fy) {
    const dividend = sumWhere(dividends, 'dividend_income', function (d) { return d.financial_year === fy; });
    const committed = sumWhere(disbursements, 'planned_amount', function (d) {
      return d.financial_year === fy && isCommittedStatus(d.status);
    });
    const nextFy = nextFinancialYear(fy);
    const nextQ1 = sumWhere(disbursements, 'planned_amount', function (d) {
      return d.financial_year === nextFy && /^Q1\b/i.test(String(d.quarter).trim()) && isCommittedStatus(d.status);
    });
    const disbursed = sumWhere(disbursements, 'actual_amount', function (d) {
      return d.financial_year === fy && String(d.status).trim().toLowerCase() === 'disbursed';
    });
    const available = dividend + carryForward;
    const row = {
      financial_year: fy,
      dividend_income: dividend,
      prior_year_carry_forward: carryForward,
      available_budget: available,
      annual_committed_funding: committed,
      next_year_q1_committed_funding: nextQ1,
      annual_disbursed_funding: disbursed,
      unallocated_balance: available - committed - nextQ1,
    };
    // Next Q1 is only reserved here, not spent: it is counted in next year's own commitments.
    carryForward = available - committed;
    return row;
  });
  return writeSheet(ss, idx.FCT4_BUDGET_YEAR, FCT4_HEADERS, rows);
}

// ---------------------------------------------------------------------------
// fct5_maturity_rag — one row per grant_id × aspect × indicator
// ---------------------------------------------------------------------------
function buildFct5MaturityRag(ss, idx) {
  const grantById = indexBy(readSheet(ss, idx.STG_GRANTS), 'grant_id');
  const maturity = readSheet(ss, idx.STG_MATURITY);
  warnOrphanGrantIds(ss, idx, 'buildFct5MaturityRag', null, { stg_maturity: groupBy(maturity, 'grant_id') }, grantById);

  const rows = maturity.map(function (m) {
    const g = grantById[m.grant_id] || {};
    return {
      financial_year: m.financial_year,
      grant_id: m.grant_id,
      organization_id: g.organization_id,
      organisation: g.organisation || m.organisation,
      thematic_area: g.thematic_area,
      aspect: m.aspect,
      indicator: m.indicator,
      status: m.status,
    };
  });
  return writeSheet(ss, idx.FCT5_MATURITY_RAG, FCT5_HEADERS, rows);
}

// ---------------------------------------------------------------------------
// Helpers used only by the final layer
// ---------------------------------------------------------------------------

/** Today at midnight in the script time zone — the reference date for due windows. */
function pipelineToday() {
  const parts = formatIsoDate(new Date()).split('-').map(Number);
  return new Date(parts[0], parts[1] - 1, parts[2]);
}

function daysBetween(from, to) {
  const a = Date.UTC(from.getFullYear(), from.getMonth(), from.getDate());
  const b = Date.UTC(to.getFullYear(), to.getMonth(), to.getDate());
  return Math.round((b - a) / 86400000);
}

function indexBy(rows, field) {
  const map = {};
  rows.forEach(function (r) { if (!isBlank(r[field])) map[r[field]] = r; });
  return map;
}

function groupBy(rows, field) {
  const map = {};
  rows.forEach(function (r) {
    if (isBlank(r[field])) return;
    (map[r[field]] = map[r[field]] || []).push(r);
  });
  return map;
}

function countDistinct(rows, field) {
  const seen = {};
  rows.forEach(function (r) { if (!isBlank(r[field])) seen[r[field]] = true; });
  return Object.keys(seen).length;
}

function sumWhere(rows, field, predicate) {
  return rows.reduce(function (acc, r) {
    return predicate(r) && typeof r[field] === 'number' ? acc + r[field] : acc;
  }, 0);
}

function isCommittedStatus(status) {
  return COMMITTED_DISBURSEMENT_STATUSES.indexOf(String(status).trim().toLowerCase()) !== -1;
}

function sumDisbursements(rows) {
  return {
    committed: sumWhere(rows, 'planned_amount', function (d) { return isCommittedStatus(d.status); }),
    disbursed: sumWhere(rows, 'actual_amount', function (d) { return String(d.status).trim().toLowerCase() === 'disbursed'; }),
  };
}

/** "70% of annual target" → 0.7, "35% achieved" → 0.35, "732 learners" → 732. null if no number. */
function parseMeasure(text) {
  if (typeof text === 'number') return text;
  const m = /(-?\d+(?:\.\d+)?)\s*(%)?/.exec(String(text || '').replace(/,/g, ''));
  if (!m) return null;
  const n = Number(m[1]);
  return m[2] ? n / 100 : n;
}

/** Latest quarter (Q4 → Q1) with a status for this outcome row, or ''. */
function latestReportedQuarter(outcomeRow) {
  for (let i = QUARTERS.length - 1; i >= 0; i--) {
    if (!isBlank(outcomeRow[QUARTERS[i].toLowerCase() + '_status'])) return QUARTERS[i];
  }
  return '';
}

/**
 * Grant is Off Track if any of its outcomes is Off Track in the latest quarter
 * that has any status for the grant; otherwise On Track. '' when nothing is reported.
 */
function grantPerformanceStatus(outcomes) {
  for (let i = QUARTERS.length - 1; i >= 0; i--) {
    const col = QUARTERS[i].toLowerCase() + '_status';
    const statuses = outcomes.map(function (o) { return String(o[col] || '').trim().toLowerCase(); })
      .filter(function (s) { return s !== ''; });
    if (!statuses.length) continue;
    return statuses.indexOf('off track') !== -1 ? 'Off Track' : 'On Track';
  }
  return '';
}

/** Outcome is achieved when Final Actual ≥ End-of-Program Cycle Target (both parsed as numbers). */
function countAchievedOutcomes(outcomes) {
  return outcomes.filter(function (o) {
    const target = parseMeasure(o.target_text);
    const actual = parseMeasure(o.final_actual_text);
    return target !== null && actual !== null && actual >= target;
  }).length;
}

/** Worst RAG (Red > Amber > Green) across the grant's indicators for one aspect. */
function worstRag(maturityRows, aspect) {
  let worst = '';
  maturityRows.forEach(function (m) {
    if (String(m.aspect).trim().toLowerCase() !== aspect.toLowerCase()) return;
    const sev = RAG_SEVERITY[String(m.status).trim().toLowerCase()];
    if (sev && (!worst || sev > RAG_SEVERITY[worst.toLowerCase()])) worst = String(m.status).trim();
  });
  return worst;
}

function countCorePolicies(org) {
  return CORE_POLICY_COLUMNS.filter(function (c) { return String(org[c]).trim().toLowerCase() === 'yes'; }).length;
}

function durationBucket(n) {
  if (!n) return '';
  if (n === 1) return 'Year 1';
  if (n <= 5) return 'Years 2–5';
  if (n <= 10) return 'Years 6–10';
  return 'Years 11+';
}

function mapDecisionStatus(status) {
  if (isBlank(status)) return '';
  const s = String(status).toLowerCase();
  if (s.indexOf('locked') !== -1) return 'Decided';
  if (s.indexOf('recommendation') !== -1) return 'Pending';
  return String(status).trim();
}

function dueWindow(days) {
  if (days < 0) return 'Overdue';
  if (days <= 30) return '0–30 days';
  if (days <= 60) return '31–60 days';
  return '61+ days';
}

function fundingRange(amount) {
  if (!amount || amount <= 0) return '';
  const LAKH = 100000;
  if (amount < 1 * LAKH) return '<₹1 lakh';
  if (amount <= 10 * LAKH) return '₹1–10 lakh';
  if (amount <= 20 * LAKH) return '₹11–20 lakh';
  if (amount <= 50 * LAKH) return '₹21–50 lakh';
  return '>₹50 lakh';
}

/** Logs a WARN listing grant_ids found in stg tables but not in stg_grants. */
function warnOrphanGrantIds(ss, idx, fnName, grants, groupedByTable, grantById) {
  const known = grantById || indexBy(grants, 'grant_id');
  Object.keys(groupedByTable).forEach(function (table) {
    const orphans = Object.keys(groupedByTable[table]).filter(function (id) { return !known[id]; });
    if (orphans.length) {
      log(ss, idx, 'WARN', fnName, 0, orphans.length + ' grant_id(s) in ' + table + ' not found in stg_grants: ' + orphans.slice(0, 10).join(', '), null, 'SUCCESS');
    }
  });
}
